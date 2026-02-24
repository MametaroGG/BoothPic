"""
Standalone Search API - Uses in-memory Qdrant to avoid file lock issues.
Loads seed data into memory on startup.
"""
import io
import uuid
import torch
import traceback
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio

import logging
import os

# Configure logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    filename=os.path.join(BASE_DIR, 'debug.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logging.info("--- [DEBUG] Standalone Search API starting ---")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Ensure the directory exists before mounting to avoid RuntimeError
images_dir = os.path.join(BASE_DIR, "scraper", "data", "raw_images")
os.makedirs(images_dir, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=images_dir), name="images")

COLLECTION_NAME = "booth_items"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SAMPLE_ITEMS = [
    {
        "title": "幽狐族の娘「桔梗」専用【3D衣装モデル】Royal Dress",
        "price": 2000,
        "shopName": "Mame-Shop",
        "boothUrl": "https://booth.pm/ja/items/1234567",
        "thumbnailUrl": "https://picsum.photos/seed/royal_dress/600/600"
    },
    {
        "title": "【萌専用】ゴスロリメイド服",
        "price": 1800,
        "shopName": "Alice-Atelier",
        "boothUrl": "https://booth.pm/ja/items/2345678",
        "thumbnailUrl": "https://picsum.photos/seed/maid_goth/600/600"
    },
    {
        "title": "【桔梗/萌/ここあ対応】和風衣装セット",
        "price": 2500,
        "shopName": "VRC-Fashion",
        "boothUrl": "https://booth.pm/ja/items/3456789",
        "thumbnailUrl": "https://picsum.photos/seed/japanese_outfit/600/600"
    },
]

print("--- [DEBUG] Starting In-Memory Search API ---")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- [DEBUG] Device: {device} ---")

# Initialize CLIP
print("--- [DEBUG] Loading CLIP model ---")
from transformers import CLIPImageProcessor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("--- [DEBUG] CLIP loaded ---")

# Initialize Qdrant (Cloud or In-Memory)
print("--- [DEBUG] Initializing Qdrant ---")
qdrant_url = os.getenv("QDRANT_CLOUD_URL")
qdrant_api_key = os.getenv("QDRANT_CLOUD_API_KEY")

if qdrant_url and qdrant_api_key:
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    print("--- [DEBUG] Connected to Qdrant Cloud ---")
else:
    qdrant = QdrantClient(":memory:")
    print("--- [DEBUG] Connected to Local In-Memory Qdrant ---")

# Try to create collection if it doesn't exist
try:
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )
except Exception as e:
    print(f"--- [DEBUG] Collection check/create notice: {e} ---")

def get_embedding(image: Image.Image):
    # Use image-only processing without padding to bypass the older transformers bug
    inputs = processor(images=[image], return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    
    # Robust extraction
    if isinstance(outputs, torch.Tensor):
        features = outputs
    elif hasattr(outputs, "image_embeds"):
        features = outputs.image_embeds
    elif hasattr(outputs, "pooler_output"):
        features = outputs.pooler_output
    elif isinstance(outputs, (list, tuple)):
        features = outputs[0]
    else:
        features = outputs

    # Final check
    if not isinstance(features, torch.Tensor):
        # Fallback to index access if possible
        try:
            features = outputs[0]
        except:
             raise Exception(f"Failed to extract tensor from {type(outputs)}")

    features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy()[0].tolist()

# Seed in-memory Qdrant with real scraped data if available
import json
import os
import hashlib

def get_stable_uuid(text: str):
    """Generate a stable UUID from a string (e.g. image path)"""
    hash_obj = hashlib.md5(text.encode('utf-8'))
    return str(uuid.UUID(hash_obj.hexdigest()))

# Use absolute paths to avoid issues with background tasks
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METADATA_PATH = os.path.join(BASE_DIR, "scraper", "data", "popular_items_full.jsonl")
SCRAPER_DIR = os.path.join(BASE_DIR, "scraper")


# Global state for indexing status
indexing_status = {
    "total": 0,
    "current": 0,
    "is_complete": False,
    "last_item": None
}

async def seed_data():
    global indexing_status
    logging.info("--- [DEBUG] Starting background seeding ---")
    if os.path.exists(METADATA_PATH):
        processed_urls = set()
        
        # Read total lines first for progress tracking
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)
        indexing_status["total"] = total_lines

        logging.info(f"--- [DEBUG] Loading real data from {METADATA_PATH} (Total items: {total_lines}) ---")
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            count = 0
            img_count = 0
            for line in f:
                try:
                    await asyncio.sleep(0) # Yield to event loop
                    item = json.loads(line.strip())
                    count += 1
                    indexing_status["current"] = count
                    
                    if not item.get("images") or not item.get("url"):
                        continue
                    
                    if item["url"] in processed_urls:
                        continue
                    processed_urls.add(item["url"])

                    for img_rel_path in item["images"]:
                        try:
                            # Use a small sleep to throttle
                            await asyncio.sleep(0.01) 
                            
                            is_url = img_rel_path.startswith("http://") or img_rel_path.startswith("https://")
                            
                            if is_url:
                                resp = requests.get(img_rel_path, timeout=10)
                                if resp.status_code != 200:
                                    logging.warning(f"Failed to fetch remote image: {img_rel_path}")
                                    continue
                                img_data = io.BytesIO(resp.content)
                                img = Image.open(img_data).convert("RGB")
                                thumbnail_url = img_rel_path
                            else:
                                # Try the path as is first
                                img_path = os.path.join(SCRAPER_DIR, img_rel_path)
                                
                                # Fallback: Many paths in metadata have extra 'アズキ/' etc. 
                                # but files are flat in raw_images
                                if not os.path.exists(img_path):
                                    filename = os.path.basename(img_rel_path)
                                    img_path = os.path.join(SCRAPER_DIR, "raw_images", filename)
                                    
                                if not os.path.exists(img_path):
                                    logging.warning(f"Image not found: {img_rel_path} or {img_path}")
                                    continue
                                
                                img = Image.open(img_path).convert("RGB")
                                filename = os.path.basename(img_path)
                                thumbnail_url = f"/api/images/{filename}"

                            vector = get_embedding(img)

                            payload = {
                                "title": item.get("title", "Unknown"),
                                "price": item.get("price", "Unknown"),
                                "shopName": item.get("shop", "Unknown"),
                                "boothUrl": item.get("url", "#"),
                                "thumbnailUrl": thumbnail_url
                            }
                            point_id = get_stable_uuid(img_rel_path)

                            qdrant.upsert(
                                collection_name=COLLECTION_NAME,
                                points=[PointStruct(
                                    id=point_id,
                                    vector=vector,
                                    payload=payload
                                )]
                            )
                            img_count += 1
                        except Exception as img_e:
                             logging.error(f"Error indexing image {img_rel_path}: {img_e}")

                    indexing_status["last_item"] = f"{item.get('title')} ({item.get('price')})"
                    if count % 10 == 0:
                        logging.info(f"--- [DEBUG] Progress: {count}/{total_lines} items ({img_count} images). ---")
                except Exception as e:
                    logging.error(f"--- [DEBUG] Seed error at line {count}: {e}")
        
        indexing_status["is_complete"] = True
        logging.info(f"--- [DEBUG] Seeding complete. Loaded {count} items ({img_count} images). ---")
    else:
        logging.warning(f"--- [DEBUG] No metadata.jsonl found at {METADATA_PATH}. Skipping background seeding. ---")
        indexing_status["is_complete"] = True

@app.on_event("startup")
async def startup_event():
    import asyncio
    # Start seeding in the background
    asyncio.create_task(seed_data())



from pydantic import BaseModel
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

# ... (existing imports)

def get_booth_identifiers(text: str):
    """
    Extracts stable identifiers (Shop Subdomain, Item ID) from BOOTH URLs or text.
    Returns a set of normalized strings.
    """
    ids = set()
    text = text.strip()
    if not text:
        return ids
    
    # 1. Direct Shop Subdomain (e.g. mame-shop.booth.pm)
    shop_match = re.search(r'https?://([\w-]+)\.booth\.pm', text)
    if shop_match and shop_match.group(1) not in ('www', 'extension', 'manage'):
        ids.add(shop_match.group(1).lower())
    
    # 2. Item ID from path (e.g. booth.pm/ja/items/12345 or shop.booth.pm/items/12345)
    item_match = re.search(r'/items/(\d+)', text)
    if item_match:
        ids.add(item_match.group(1))
    
    # 3. Simple numeric ID
    if text.isdigit():
        ids.add(text)
    
    # 4. Fallback: if it's a slug or name part (lowercase)
    if not text.startswith("http"):
        ids.add(text.lower())
        
    return ids

# Persistent store for opted-out shops (names or URLs)
BLACKLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blacklist.txt")
OPTED_OUT_SHOPS = set()

def load_blacklist():
    global OPTED_OUT_SHOPS
    if os.path.exists(BLACKLIST_PATH):
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    OPTED_OUT_SHOPS.add(line)
    logging.info(f"--- [DEBUG] Blacklist loaded: {len(OPTED_OUT_SHOPS)} entries ---")

# Initial load
load_blacklist()

class OptOutRequest(BaseModel):
    shopUrl: str

import smtplib
from email.message import EmailMessage

def send_opt_out_email(identifier: str):
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASSWORD")
    if email_user and email_pass:
        try:
            msg = EmailMessage()
            msg.set_content(f"A new opt-out request has been received for:\n\nShop Identifier: {identifier}\n\nPlease review and delete their data from the index if appropriate.")
            msg['Subject'] = f'BOOTH-Lens Opt-out Request: {identifier}'
            msg['From'] = email_user
            msg['To'] = 'tyarity3@gmail.com'

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            server.quit()
            logging.info(f"--- [DEBUG] Opt-out email notification sent successfully for {identifier}. ---")
        except Exception as e:
            logging.error(f"--- [DEBUG] Failed to send opt-out email: {e} ---")
    else:
        logging.warning("--- [DEBUG] EMAIL_USER or EMAIL_PASSWORD not set. Opt-out email not sent. ---")

@app.post("/api/opt-out")
async def opt_out(req: OptOutRequest, background_tasks: BackgroundTasks):
    """
    Registers a shop to be excluded from search results.
    Accepts a shop URL or name.
    """
    # Robust normalization: extract identifiers
    identifier = req.shopUrl.strip()
    if identifier:
        new_ids = get_booth_identifiers(identifier)
        for nid in new_ids:
            OPTED_OUT_SHOPS.add(nid)
        
        # Original fallback (just in case)
        OPTED_OUT_SHOPS.add(identifier.lower())

        logging.info(f"--- [DEBUG] Opted out: {identifier} -> IDs: {new_ids} (Total: {len(OPTED_OUT_SHOPS)}) ---")
        
        # Save to blacklist.txt for persistence
        try:
            with open(BLACKLIST_PATH, "a", encoding="utf-8") as f:
                f.write(f"{identifier}\n")
        except Exception as e:
            logging.error(f"Failed to save to blacklist.txt: {e}")

        # Dispatch background task for email
        background_tasks.add_task(send_opt_out_email, identifier)
        
        return {"status": "success", "message": f"Shop '{identifier}' has been opted out."}
    else:
        raise HTTPException(status_code=400, detail="Invalid shop identifier")


@app.post("/api/search")
async def search_image(file: UploadFile = File(...)):
    if not indexing_status["is_complete"] and indexing_status["current"] == 0:
         raise HTTPException(status_code=503, detail="Search engine is still initializing. Please wait a few moments.")
    
    try:
        s_filename = repr(file.filename)
        logging.info(f"--- [DEBUG] START REQUEST: {s_filename} ---")
        
        logging.info("--- [DEBUG] 1. Reading file content ---")
        contents = await file.read()
        
        logging.info("--- [DEBUG] 2. Opening image with PIL ---")
        try:
            img_obj = Image.open(io.BytesIO(contents))
            # Safely handle animated images by only taking the first frame
            if getattr(img_obj, "is_animated", False):
                img_obj.seek(0)
            
            # Create a solid white background for transparent images to avoid RGBA bugs
            image = Image.new("RGB", img_obj.size, (255, 255, 255))
            if img_obj.mode in ('RGBA', 'LA') or (img_obj.mode == 'P' and 'transparency' in img_obj.info):
                image.paste(img_obj, mask=img_obj.convert('RGBA').split()[3])
            else:
                image.paste(img_obj)
                
            logging.info(f"--- [DEBUG] Image size: {image.size} ---")
        except Exception as e:
            logging.error(f"--- [DEBUG] PIL Error: {e} ---")
            raise e
        
        logging.info("--- [DEBUG] 3. Calling get_embedding ---")
        vector = get_embedding(image)
        logging.info("--- [DEBUG] 4. Embedding generated successfully ---")
        
        logging.info(f"--- [DEBUG] 5. Searching Qdrant with Opt-out Filter (Excluded: {len(OPTED_OUT_SHOPS)}) ---")
        
        # Construct filter to exclude opted-out shops
        # We filter against 'shopName' and 'boothUrl' payload fields
        # Ideally, we should exact match, but for now we check if the shopName is in the set
        
        query_filter = None
        if OPTED_OUT_SHOPS:
            # Create a list of conditions where shopName matches any of the opted-out identifiers
            # Qdrant 'must_not' with multiple Match conditions acts as NOR (neither A nor B)
            # We want to exclude if shopName is in OPTED_OUT_SHOPS OR boothUrl is in OPTED_OUT_SHOPS
            
            # Since qdrant filters are strict, let's just match against shopName for the prototype
            # as our sample data has clean shop names.
            
            conditions = []
            for excluded in OPTED_OUT_SHOPS:
                # Match against shopName (subdomain) or boothUrl (contains ID)
                # Note: MatchValue is an exact match for the field.
                # However, our payload contains the FULL URL in 'boothUrl'.
                # To be robust, we'd need 'must_not' to catch any item where
                # ANY of our normalized IDs appear in the URL or shopName.
                
                # Filter by Shop Name (exact)
                conditions.append(FieldCondition(key="shopName", match=MatchValue(value=excluded)))
                
                # To filter by Item ID in the URL, we can't easily do substring match in Qdrant 
                # without Regex index. For now, we'll rely on the Shop Name matching correctly.
                # If 'excluded' is a numeric ID, we normally can't match it against the full URL.
            
            query_filter = Filter(must_not=conditions)

        try:
            # Fetch more points to allow for deduplication by product (boothUrl)
            search_result = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                query_filter=query_filter, 
                limit=40,
                with_payload=True
            )
            
            # Deduplicate by boothUrl, keeping only the best match per product
            unique_results = []
            seen_urls = set()
            for hit in search_result:
                url = hit.payload.get("boothUrl")
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(hit)
                if len(unique_results) >= 12: # Slightly higher limit for better UI
                    break
            
            search_result = unique_results
            logging.info(f"--- [DEBUG] Found {len(search_result)} unique products ---")

        except Exception as e:
            logging.error(f"--- [DEBUG] Qdrant Error: {e} ---")
            raise e
        
        logging.info("--- [DEBUG] 6. Formatting response ---")
        return {
            "results": [
                {"id": str(hit.id), "score": hit.score, "payload": hit.payload}
                for hit in search_result
            ]
        }
    except Exception as e:
        logging.error(f"FATAL SEARCH ERROR: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")



@app.get("/")
def root():
    return {
        "status": "In-Memory Search API running",
        "indexing": indexing_status
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
