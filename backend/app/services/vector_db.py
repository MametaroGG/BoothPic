from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny
import os
import json
import asyncio
import logging
import hashlib
import uuid
import requests
import io
from typing import List, Optional
from PIL import Image
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .image_processor import ImageProcessor

# Global helper for Stable UUID
def get_stable_uuid(text: str):
    hash_obj = hashlib.md5(text.encode('utf-8'))
    return str(uuid.UUID(hash_obj.hexdigest()))

class VectorDBService:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        qdrant_url = os.getenv("QDRANT_CLOUD_URL")
        qdrant_api_key = os.getenv("QDRANT_CLOUD_API_KEY")
        
        if qdrant_url and qdrant_api_key:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            logging.info("Connected to Qdrant Cloud.")
        else:
            self.client = QdrantClient(":memory:")
            logging.info("Connected to Local Qdrant (:memory:).")
            
        self.collection_name = "booth_items"
        self.vector_size = 512
        self.ensure_collection()
        
        # Indexing state
        self.indexing_status = {
            "total": 0,
            "current": 0,
            "is_complete": False,
            "last_item": None
        }
        
        # Determine paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.metadata_path = os.path.join(self.base_dir, "scraper", "data", "popular_items_full.jsonl")
        self.scraper_dir = os.path.join(self.base_dir, "scraper")

    def ensure_collection(self):
        from qdrant_client.http.models import PayloadSchemaType
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            # Create indices on initialization
            fields = ["shopName", "category", "avatars", "colors"]
            for field in fields:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                        wait=True
                    )
                except Exception as e:
                    logging.error(f"Failed to create index for {field}: {e}")

    async def seed_data(self, image_processor: ImageProcessor):
        logging.info("--- [VectorDB] Starting background seeding ---")
        if not os.path.exists(self.metadata_path):
            logging.warning(f"--- [VectorDB] No metadata.jsonl found at {self.metadata_path} ---")
            self.indexing_status["is_complete"] = True
            return

        # Deduplicate metadata in memory first to avoid redundant processing
        unique_items = {}
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line.strip())
                if "url" in item:
                    unique_items[item["url"]] = item
        
        items_to_process = list(unique_items.values())
        self.indexing_status["total"] = len(items_to_process)
        logging.info(f"--- [VectorDB] Unique items to process: {len(items_to_process)} (from {len(unique_items)} entries) ---")

        logging.info("--- [VectorDB] Fetching existing IDs from Qdrant to skip... ---")
        existing_ids = set()
        next_page = None
        try:
            while True:
                # Optimized scroll: minimal payload
                records, next_page = self.client.scroll(
                    collection_name=self.collection_name, 
                    limit=10000, 
                    with_payload=False, 
                    with_vectors=False,
                    offset=next_page
                )
                for r in records:
                    existing_ids.add(r.id)
                if next_page is None: break
        except Exception as e:
            logging.error(f"Failed to fetch existing IDs: {e}")
        logging.info(f"--- [VectorDB] Total existing IDs in Qdrant: {len(existing_ids)} ---")

        async with httpx.AsyncClient(timeout=10.0, limits=httpx.Limits(max_connections=20)) as http_client:
            batch_points = []
            img_count = 0
            consecutive_skips = 0
            SKIP_LIMIT = 200 
            
            # Process in reverse (newest first)
            for idx, item in enumerate(reversed(items_to_process)):
                try:
                    self.indexing_status["current"] = idx + 1
                    
                    if not item.get("images") or not item.get("url"):
                        continue

                    all_images_already_indexed = True
                    item_points = []

                    for img_rel_path in item["images"]:
                        point_id = get_stable_uuid(img_rel_path)
                        if point_id in existing_ids:
                            continue
                        
                        all_images_already_indexed = False
                        
                        # Process image (Download if URL, else local)
                        img = None
                        thumbnail_url = img_rel_path
                        
                        is_url = img_rel_path.startswith("http://") or img_rel_path.startswith("https://")
                        if is_url:
                            try:
                                @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
                                async def fetch_image(url):
                                    resp = await http_client.get(url)
                                    resp.raise_for_status()
                                    return resp.content
                                
                                content = await fetch_image(img_rel_path)
                                img = Image.open(io.BytesIO(content)).convert("RGB")
                            except Exception as e:
                                logging.error(f"Error fetching image {img_rel_path}: {e}")
                                continue
                        else:
                            img_path = os.path.join(self.scraper_dir, img_rel_path)
                            if not os.path.exists(img_path):
                                filename = os.path.basename(img_rel_path)
                                img_path = os.path.join(self.scraper_dir, "raw_images", filename)
                            
                            if os.path.exists(img_path):
                                img = Image.open(img_path).convert("RGB")
                                filename = os.path.basename(img_path)
                                thumbnail_url = f"/api/images/{filename}"
                            else:
                                continue

                        if img:
                            vector = image_processor.get_embedding(img)
                            payload = {
                                "title": item.get("title", "Unknown"),
                                "price": item.get("price", "Unknown"),
                                "shopName": item.get("shop", "Unknown"),
                                "boothUrl": item.get("url", "#"),
                                "thumbnailUrl": thumbnail_url,
                                "category": item.get("category", "Unknown"),
                                "avatars": item.get("avatars", []),
                                "colors": item.get("colors", [])
                            }
                            item_points.append(PointStruct(id=point_id, vector=vector, payload=payload))

                    if all_images_already_indexed:
                        consecutive_skips += 1
                    else:
                        consecutive_skips = 0
                        batch_points.extend(item_points)
                        img_count += len(item_points)

                    # Upsert in batches of 50 points
                    if len(batch_points) >= 50:
                        self.client.upsert(collection_name=self.collection_name, points=batch_points)
                        logging.info(f"--- [VectorDB] Batch upserted: {len(batch_points)} points ---")
                        batch_points = []

                    if consecutive_skips >= SKIP_LIMIT:
                        logging.info(f"--- [VectorDB] Reached SKIP_LIMIT ({SKIP_LIMIT}). Early exit. ---")
                        break
                        
                    self.indexing_status["last_item"] = f"{item.get('title')}"
                    
                except Exception as e:
                    logging.error(f"Item processing error: {e}")

            # Final batch
            if batch_points:
                self.client.upsert(collection_name=self.collection_name, points=batch_points)
                logging.info(f"--- [VectorDB] Final batch upserted: {len(batch_points)} points ---")
        
        self.indexing_status["is_complete"] = True
        logging.info(f"--- [VectorDB] Seeding complete. {img_count} new images indexed. ---")

    def search_similar(self, vector: List[float], limit: int = 10, offset: int = 0, excluded_shops: set = None, category: str = None, avatars: List[str] = None, colors: List[str] = None):
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
        
        query_filter = None
        conditions = []
        must_not_conditions = []
        
        if excluded_shops:
            for excluded in excluded_shops:
                must_not_conditions.append(FieldCondition(key="shopName", match=MatchValue(value=excluded)))
                
        if category:
            conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))
            
        if avatars:
            for avatar in avatars:
                conditions.append(FieldCondition(key="avatars", match=MatchAny(any=[avatar])))
                
        if colors:
            for color in colors:
                conditions.append(FieldCondition(key="colors", match=MatchAny(any=[color])))
                
        if conditions or must_not_conditions:
            query_filter = Filter(must=conditions if conditions else None, must_not=must_not_conditions if must_not_conditions else None)

        # Retrieve more candidates for deduplication using query_points API
        raw_results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit * 3, 
            with_payload=True
        ).points

        # Deduplicate by unique boothUrl
        unique_results = []
        seen_urls = set()
        for hit in raw_results:
            url = hit.payload.get("boothUrl")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(hit)
            if len(unique_results) >= limit:
                break
        
        return unique_results
