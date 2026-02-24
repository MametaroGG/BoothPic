"""
Comprehensive BOOTH scraper for VRChat 3D Clothing items with 1000+ likes.

Phase 1: Scan search result pages to collect all item URLs with 1000+ likes
Phase 2: Visit each item's detail page to collect full metadata, compress images
         to WebP 512x512, and upload directly to Cloudflare R2

Output metadata is compatible with the existing vector_db.py seeding pipeline,
including avatars/colors/tags fields for Qdrant filtering.

Usage:
    cd backend
    python -m scraper.scrape_all_popular           # Run both phases
    python -m scraper.scrape_all_popular phase1     # Phase 1 only
    python -m scraper.scrape_all_popular phase2     # Phase 2 only
"""

import os
import sys
import time
import json
import re
import logging
import requests
import io
import random
import boto3
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from dotenv import load_dotenv
import concurrent.futures
import threading

from PIL import Image
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Load .env from backend root
load_dotenv(Path(__file__).parent.parent / ".env")

# =============================================================================
# Configuration
# =============================================================================
BASE_URL = "https://booth.pm"
SEARCH_URL = "https://booth.pm/ja/browse/3D%E8%A1%A3%E8%A3%85?tags%5B%5D=VRChat&adult=include"
MIN_LIKES = 1000
MAX_PAGES = 170
CONSECUTIVE_EMPTY_PAGES_LIMIT = 3

# Image compression settings (aggressive)
IMAGE_MAX_SIZE = 512          # Max dimension (px) — CLIP uses 224x224 internally
IMAGE_FORMAT = "WEBP"         # WebP is ~30-50% smaller than JPEG at same quality
IMAGE_QUALITY = 60            # Aggressive but visually acceptable for thumbnails
IMAGE_EXTENSION = ".webp"
MAX_RUNTIME = 5 * 3600 - 600  # 5 hours minus 10 minutes buffer (in seconds)
START_TIME = time.time()

# Directories
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
IMAGES_DIR = DATA_DIR / "raw_images"
PHASE1_OUTPUT = DATA_DIR / "popular_items_list.jsonl"
PHASE2_OUTPUT = DATA_DIR / "popular_items_full.jsonl"
PROGRESS_FILE = DATA_DIR / "scrape_progress.json"

# HTTP
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# Cloudflare R2
R2_ENABLED = bool(os.getenv("R2_ACCESS_KEY_ID"))
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "booth-images")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_DEV_URL", "").rstrip("/")
R2_KEY_PREFIX = "data/raw_images"  # Mirror local path structure in R2

# =============================================================================
# Avatar & Color Definitions (for Qdrant filter metadata)
# =============================================================================
# Comprehensive list of popular VRChat avatars (2024-2025)
TARGET_AVATARS = [
    # --- Very Popular ---
    "マヌカ", "桔梗", "セレスティア", "萌", "森羅", "瑞希", "ライム", "シフォン",
    "ウルフェリア", "薄荷", "京狐", "狛乃", "水瀬", "ユリスフィア", "エミスティア",
    "杏里", "彼方", "サクヤ", "ナユ", "真冬",
    # --- Popular (2024-2025) ---
    "リーファ", "ここあ", "イナバ", "カリン", "チセ", "ルーシュ", "リルモワ",
    "竜胆", "あのん", "ANON", "ミルク", "ラシューシャ", "メリノ", "キキョウ",
    "舞夜", "ルキフェル", "ソフィナ", "ヴェール", "フィリナ", "リミリア",
    "マリエル", "セフィラ", "チューベローズ", "シエル", "イヨ",
    "あまなつ", "しなの", "ラスク", "シュガ", "ルシナ",
    # --- Male / Neutral ---
    "アル", "ディオ", "Dio", "カーネリア", "グリフ",
    # --- Newer models ---
    "オディール", "ズフィ", "フェリス", "アイリス", "ミント",
]

# Color keywords (Japanese + English)
TARGET_COLORS = {
    # Japanese → Normalized key
    "黒": "black", "ブラック": "black",
    "白": "white", "ホワイト": "white",
    "赤": "red", "レッド": "red",
    "青": "blue", "ブルー": "blue",
    "緑": "green", "グリーン": "green",
    "黄": "yellow", "イエロー": "yellow",
    "ピンク": "pink",
    "紫": "purple", "パープル": "purple",
    "茶": "brown", "ブラウン": "brown",
    "グレー": "gray", "灰": "gray",
    "水色": "light_blue",
    "オレンジ": "orange",
    "ベージュ": "beige",
    "ネイビー": "navy",
    "ワインレッド": "wine_red",
    "モノクロ": "monochrome",
    "ゴールド": "gold", "金": "gold",
    "シルバー": "silver", "銀": "silver",
    # English
    "black": "black", "white": "white", "red": "red",
    "blue": "blue", "green": "green", "yellow": "yellow",
    "pink": "pink", "purple": "purple", "brown": "brown",
    "gray": "gray", "grey": "gray", "orange": "orange",
    "navy": "navy", "beige": "beige", "gold": "gold", "silver": "silver",
}

# =============================================================================
# Logging
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(SCRIPT_DIR / "scrape_popular.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# R2 Client
# =============================================================================
_s3_client = None

def get_r2_client():
    global _s3_client
    if _s3_client is None and R2_ENABLED:
        _s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv("R2_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name='auto'
        )
        logger.info(f"R2 client initialized. Bucket: {R2_BUCKET}")
    return _s3_client


def r2_key_exists(key):
    """Check if a key already exists in R2."""
    try:
        client = get_r2_client()
        if client:
            client.head_object(Bucket=R2_BUCKET, Key=key)
            return True
    except Exception:
        pass
    return False


# =============================================================================
# Utility
# =============================================================================
def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"phase1_last_page": 0, "phase2_last_index": 0}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f)


def load_existing_items(filepath):
    items = {}
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        items[item.get("url", "")] = item
                    except json.JSONDecodeError:
                        continue
    return items


def sleep_random(min_sec=0.5, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))


def check_timeout():
    """Check if the execution has exceeded the maximum runtime."""
    elapsed = time.time() - START_TIME
    if elapsed > MAX_RUNTIME:
        return True
    return False


# =============================================================================
# Image Processing & Upload
# =============================================================================
def compress_and_upload_image(url, item_id, image_index):
    """
    Download image, compress to WebP 512x512 quality=60, upload to R2.
    Returns (r2_url, file_size_bytes) or (None, 0) on failure.
    Falls back to local save if R2 is disabled.
    """
    filename = f"{item_id}_{image_index}{IMAGE_EXTENSION}"
    r2_key = f"{R2_KEY_PREFIX}/{filename}"

    # Check if already uploaded
    if R2_ENABLED and r2_key_exists(r2_key):
        r2_url = f"{R2_PUBLIC_URL}/{r2_key}"
        logger.debug(f"  Already in R2: {filename}")
        return r2_url, 0

    local_path = IMAGES_DIR / filename
    if not R2_ENABLED and local_path.exists():
        return str(local_path.relative_to(DATA_DIR)), local_path.stat().st_size

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"  Image HTTP {resp.status_code}: {url}")
            return None, 0

        original_size = len(resp.content)

        # Compress
        img = Image.open(io.BytesIO(resp.content))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img.thumbnail((IMAGE_MAX_SIZE, IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format=IMAGE_FORMAT, quality=IMAGE_QUALITY, method=6)  # method=6 = slowest/best compression
        compressed_bytes = buf.getvalue()
        compressed_size = len(compressed_bytes)

        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        logger.debug(f"  {filename}: {original_size//1024}KB -> {compressed_size//1024}KB ({ratio:.0f}% reduction)")

        if R2_ENABLED:
            try:
                client = get_r2_client()
                content_type = "image/webp" if IMAGE_FORMAT == "WEBP" else "image/jpeg"
                client.put_object(
                    Bucket=R2_BUCKET,
                    Key=r2_key,
                    Body=compressed_bytes,
                    ContentType=content_type,
                    CacheControl="public, max-age=31536000",  # 1 year cache
                )
                r2_url = f"{R2_PUBLIC_URL}/{r2_key}"
                return r2_url, compressed_size
            except Exception as e:
                logger.error(f"  R2 upload failed for {filename}: {e}")
                # Fall through to local save

        # Local fallback
        with open(local_path, 'wb') as f:
            f.write(compressed_bytes)
        return str(local_path.relative_to(DATA_DIR)), compressed_size

    except Exception as e:
        logger.warning(f"  Image error {url}: {e}")
        return None, 0


# =============================================================================
# Metadata Extraction: Avatars & Colors
# =============================================================================
def extract_avatars(title, description, variation_names, tags):
    """Extract compatible avatar names from all available text fields."""
    found = set()
    # Build a single searchable text blob
    searchable = " ".join([
        title,
        description,
        " ".join(variation_names),
        " ".join(tags),
    ])

    for avatar in TARGET_AVATARS:
        if avatar in searchable:
            found.add(avatar)

    return sorted(found)


def extract_colors(title, description, variation_names):
    """Extract color info from title, description, variation names."""
    found = set()
    searchable = " ".join([
        title.lower(),
        " ".join(v.lower() for v in variation_names),
        description[:500].lower(),  # Only check start of description
    ])

    for keyword, normalized in TARGET_COLORS.items():
        if keyword.lower() in searchable:
            found.add(normalized)

    return sorted(found)


# =============================================================================
# Phase 1: Collect item URLs from search result pages
# =============================================================================
def phase1_collect_urls():
    logger.info("=" * 60)
    logger.info("PHASE 1: Collecting item URLs from search pages")
    logger.info("=" * 60)

    progress = load_progress()
    start_page = progress.get("phase1_last_page", 0) + 1
    existing = load_existing_items(PHASE1_OUTPUT)
    logger.info(f"Resuming from page {start_page}. Already collected: {len(existing)} items.")

    consecutive_empty = 0
    new_items_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
        )
        page = context.new_page()
        page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        # --- Handle age verification on first load ---
        age_verified = False

        for page_num in range(start_page, MAX_PAGES + 1):
            url = f"{SEARCH_URL}&page={page_num}"
            logger.info(f"[Phase 1] Page {page_num}/{MAX_PAGES}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)

                # Handle age gate (appears on first visit with adult=include)
                if not age_verified:
                    age_yes = page.locator('a:has-text("はい"), button:has-text("はい")').first
                    if age_yes.count() > 0 and age_yes.is_visible():
                        logger.info("Age verification detected. Clicking 'はい' (Yes)...")
                        age_yes.click()
                        page.wait_for_timeout(3000)
                        age_verified = True

                # Wait for item cards to render (Vue.js)
                try:
                    page.wait_for_selector('li.item-card', timeout=15000)
                except Exception:
                    # Retry: maybe page didn't fully load
                    logger.warning(f"  Cards not found, retrying page {page_num}...")
                    page.reload(wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    if not age_verified:
                        age_yes = page.locator('a:has-text("はい"), button:has-text("はい")').first
                        if age_yes.count() > 0 and age_yes.is_visible():
                            age_yes.click()
                            page.wait_for_timeout(3000)
                            age_verified = True
                    try:
                        page.wait_for_selector('li.item-card', timeout=15000)
                    except Exception:
                        logger.error(f"  Cards still not found on page {page_num}. Skipping.")
                        continue

                cards = page.locator("li.item-card")
                card_count = cards.count()

                if card_count == 0:
                    logger.warning(f"No cards on page {page_num}. Stopping.")
                    break

                page_qualifying = 0
                for i in range(card_count):
                    card = cards.nth(i)

                    # --- Extract likes ---
                    likes = 0
                    try:
                        likes_parent = card.locator('[class*="shop__text--link"]').first
                        if likes_parent.count() > 0:
                            likes_div = likes_parent.locator('.typography-14').first
                            if likes_div.count() > 0:
                                likes_text = likes_div.inner_text()
                                nums = re.findall(r'[\d,]+', likes_text)
                                if nums:
                                    likes = int(nums[0].replace(',', ''))
                    except Exception:
                        pass

                    if likes < MIN_LIKES:
                        continue

                    # --- Extract card metadata ---
                    try:
                        wrap_div = card.locator('.item-card__wrap').first
                        item_id = ""
                        if wrap_div.count() > 0:
                            item_id = (wrap_div.get_attribute('id') or '').replace('item_', '')

                        title_el = card.locator('.item-card__title-anchor--multiline').first
                        title = title_el.inner_text() if title_el.count() > 0 else "Unknown"
                        item_url = title_el.get_attribute('href') if title_el.count() > 0 else ""
                        if item_url and not item_url.startswith('http'):
                            item_url = urljoin(BASE_URL, item_url)
                        if not item_url:
                            continue

                        thumb_el = card.locator('a[data-original]').first
                        thumb_url = thumb_el.get_attribute('data-original') if thumb_el.count() > 0 else ""

                        price_el = card.locator('.price').first
                        price = price_el.inner_text().strip() if price_el.count() > 0 else ""

                        shop_el = card.locator('.item-card__shop-name-anchor').first
                        shop_name = shop_el.inner_text().strip() if shop_el.count() > 0 else ""
                        shop_url = shop_el.get_attribute('href') if shop_el.count() > 0 else ""

                        item_data = {
                            "item_id": item_id,
                            "url": item_url,
                            "title": title.strip(),
                            "thumbnail_url": thumb_url,
                            "price": price,
                            "likes": likes,
                            "shop_name": shop_name,
                            "shop_url": shop_url,
                            "collected_at": datetime.now().isoformat(),
                        }

                        if item_url not in existing:
                            with open(PHASE1_OUTPUT, 'a', encoding='utf-8') as f:
                                f.write(json.dumps(item_data, ensure_ascii=False) + '\n')
                            existing[item_url] = item_data
                            new_items_count += 1

                        page_qualifying += 1

                    except Exception as e:
                        logger.warning(f"Card {i} extraction error on page {page_num}: {e}")

                logger.info(
                    f"  -> {card_count} cards, {page_qualifying} with 1000+ likes. "
                    f"New total: {new_items_count}"
                )

                if page_qualifying == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= CONSECUTIVE_EMPTY_PAGES_LIMIT:
                        logger.info(f"{CONSECUTIVE_EMPTY_PAGES_LIMIT} consecutive empty pages. Done.")
                        break
                else:
                    consecutive_empty = 0

                progress["phase1_last_page"] = page_num
                save_progress(progress)

                if check_timeout():
                    logger.warning(f"Maximum runtime reached ({MAX_RUNTIME}s). Stopping Phase 1.")
                    break

                sleep_random(2, 4)

            except Exception as e:
                logger.error(f"Page {page_num} error: {e}")
                sleep_random(5, 10)

        browser.close()

    total = len(existing)
    logger.info(f"Phase 1 complete. Total items with 1000+ likes: {total}")
    return total


# =============================================================================
# Phase 2: Collect detailed metadata + compressed images → R2
# =============================================================================
def phase2_collect_details():
    logger.info("=" * 60)
    logger.info("PHASE 2: Collecting details + uploading compressed images to R2")
    logger.info(f"  Image settings: {IMAGE_MAX_SIZE}x{IMAGE_MAX_SIZE} {IMAGE_FORMAT} q={IMAGE_QUALITY}")
    logger.info(f"  R2 upload: {'ENABLED' if R2_ENABLED else 'DISABLED (local only)'}")
    logger.info("=" * 60)

    phase1_items = load_existing_items(PHASE1_OUTPUT)
    if not phase1_items:
        logger.error("No Phase 1 data found. Run phase1 first.")
        return

    phase2_done = load_existing_items(PHASE2_OUTPUT)
    progress = load_progress()
    start_index = progress.get("phase2_last_index", 0)

    items_list = list(phase1_items.values())
    total = len(items_list)
    total_bytes = 0

    logger.info(f"Items to process: {total}. Already done: {len(phase2_done)}. Start: {start_index}")

    write_lock = threading.Lock()

    def process_item(idx, item):
        item_url = item["url"]
        
        if item_url in phase2_done:
            return None, 0

        logger.info(f"[{idx+1}/{total}] {item['title'][:50]}... ({item['likes']} likes)")

        try:
            detail = fetch_item_detail_v2(item_url, item)

            if detail:
                with write_lock:
                    with open(PHASE2_OUTPUT, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(detail, ensure_ascii=False) + '\n')
                    phase2_done[item_url] = detail
                    
                    # Update progress occasionally to avoid excessive I/O
                    if idx > progress.get("phase2_last_index", 0):
                        progress["phase2_last_index"] = idx + 1
                        save_progress(progress)
            
            sleep_random(0.5, 1.5)

            if check_timeout():
                # Note: threads might still finish their current task but no new ones will start easily
                # This check inside process_item helps stop early.
                return detail, detail.get("_total_image_bytes", 0) if detail else 0

            return detail, detail.get("_total_image_bytes", 0) if detail else 0

        except Exception as e:
            logger.error(f"Error: {item_url}: {e}")
            sleep_random(1.5, 3)
            return None, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_item, idx, items_list[idx]): idx for idx in range(start_index, total)}
        for future in concurrent.futures.as_completed(futures):
            try:
                detail, item_bytes = future.result()
                if detail:
                    total_bytes += item_bytes
            except Exception as e:
                logger.error(f"Error in future: {e}")

    # Final progress save
    progress["phase2_last_index"] = total
    save_progress(progress)

    logger.info(f"Phase 2 complete. {len(phase2_done)} items. "
                f"Total image data: {total_bytes / 1024 / 1024:.1f} MB")


def fetch_item_detail_v2(item_url, base_item):
    """Fetch detail page, extract rich metadata, compress & upload images."""
    try:
        resp = requests.get(item_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"  HTTP {resp.status_code}: {item_url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Title ---
        title_tag = soup.select_one("h2.font-bold")
        title = title_tag.get_text(strip=True) if title_tag else base_item.get("title", "Unknown")

        # --- Shop ---
        shop_tag = soup.select_one("header a[href*='booth.pm'] span")
        shop_name = shop_tag.get_text(strip=True) if shop_tag else base_item.get("shop_name", "Unknown")

        # --- Price ---
        items_div = soup.select_one("div#items")
        raw_price = items_div.get("data-product-price", "0") if items_div else "0"
        has_variations = False
        try:
            script_tag = soup.find("script", type="application/ld+json")
            if script_tag:
                ld_data = json.loads(script_tag.string)
                offers = ld_data.get("offers", {})
                if offers.get("@type") == "AggregateOffer":
                    if float(offers.get("highPrice", 0)) > float(offers.get("lowPrice", 0)):
                        has_variations = True
        except Exception:
            pass
        price = f"¥ {raw_price}" + ("~" if has_variations else "")

        # --- Description ---
        desc_tag = (
            soup.select_one("div.market-item-detail-description")
            or soup.select_one("div.js-market-item-detail-description")
            or soup.select_one("div.typography-16")
            or soup.select_one("div.markdown-body")
        )
        description = ""
        if desc_tag:
            for sidebar in desc_tag.select("aside, .sidebar, .shop-info"):
                sidebar.decompose()
            description = desc_tag.get_text(separator='\n', strip=True)

        # --- Tags ---
        tags = extract_tags(soup)

        # --- Category ---
        category = "Unknown"
        breadcrumbs = soup.select("nav[aria-label=breadcrumb] ol li a")
        if breadcrumbs and len(breadcrumbs) > 1:
            category = breadcrumbs[-1].get_text(strip=True)

        # --- Variation Names ---
        variation_elements = (
            soup.select("div.variation-name")
            or soup.select("div[class*='variation-name']")
        )
        variation_names = list(set(
            v.get_text(strip=True) for v in variation_elements if v.get_text(strip=True)
        ))

        # --- Avatars (for filtering) ---
        avatars = extract_avatars(title, description, variation_names, tags)

        # --- Colors (for filtering) ---
        colors = extract_colors(title, description, variation_names)

        # --- Images: compress + upload to R2 ---
        image_tags = soup.select("img.market-item-detail-item-image")
        image_paths = []  # R2 URLs or local paths (compatible with vector_db.py)
        image_urls = []   # Original source URLs
        total_img_bytes = 0

        item_id = base_item.get("item_id", os.path.basename(item_url))
        for i, img in enumerate(image_tags):
            img_url = img.get("data-origin") or img.get("src")
            if not img_url:
                continue
            image_urls.append(img_url)

            path_or_url, size = compress_and_upload_image(img_url, item_id, i)
            if path_or_url:
                image_paths.append(path_or_url)
                total_img_bytes += size
            time.sleep(0.1)

        # --- Build output (compatible with existing metadata.jsonl schema) ---
        detail = {
            # Core fields (same keys as booth_scraper.py for vector_db.py compatibility)
            "url": item_url,
            "title": title,
            "shop": shop_name,
            "price": price,
            "images": image_paths,
            "category": category,
            "likes": base_item.get("likes", 0),
            # Filter fields (used by Qdrant payload indices)
            "avatars": avatars,
            "colors": colors,
            # Rich metadata
            "description": description[:2000],
            "tags": tags,
            "variation_names": variation_names,
            # Auxiliary
            "item_id": item_id,
            "shop_url": base_item.get("shop_url", ""),
            "thumbnail_url": base_item.get("thumbnail_url", ""),
            "image_urls": image_urls,
            "collected_at": datetime.now().isoformat(),
            "_total_image_bytes": total_img_bytes,
        }

        logger.info(
            f"  -> {len(image_paths)} imgs ({total_img_bytes//1024}KB) | "
            f"{len(avatars)} avatars | {len(colors)} colors | {len(tags)} tags"
        )
        return detail

    except Exception as e:
        logger.error(f"  Detail fetch error {item_url}: {e}")
        return None


def extract_tags(soup):
    """Extract tags from the detail page."""
    tags = []
    tag_heading = None
    for h in soup.find_all(["h2", "h3"]):
        if "タグ" in h.get_text():
            tag_heading = h
            break

    if tag_heading:
        tag_container = tag_heading.find_next("div")
        if tag_container:
            for t in tag_container.select("a[href*='/search/'], a[href*='tags%5B%5D=']"):
                tag_text = t.get_text(strip=True)
                if not tag_text:
                    img_el = t.find("img")
                    if img_el:
                        tag_text = img_el.get("alt", "").strip()
                if tag_text and tag_text not in tags and "で検索" not in tag_text:
                    tags.append(tag_text)

    if not tags:
        for t in soup.select("a.icon-tag-base, a.icon-tag, li.item-tag a, a[href*='tags%5B%5D=']"):
            txt = t.get_text(strip=True)
            if not txt:
                img_el = t.find("img")
                if img_el:
                    txt = img_el.get("alt", "").strip()
            if txt and txt not in tags and "検索" not in txt:
                tags.append(txt)

    return tags


# =============================================================================
# Lock file to prevent multiple instances
# =============================================================================
LOCK_FILE = SCRIPT_DIR / "scraper.lock"

def acquire_lock():
    """Prevent multiple instances from running simultaneously."""
    import atexit
    if LOCK_FILE.exists():
        # Check if the PID in the lock file is still alive
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            # On Windows, check if process exists
            import signal
            try:
                os.kill(old_pid, 0)
                logger.error(f"Another instance is running (PID {old_pid}). Exiting.")
                sys.exit(1)
            except (OSError, ProcessLookupError):
                logger.warning(f"Stale lock file (PID {old_pid} not running). Removing.")
                LOCK_FILE.unlink()
        except (ValueError, FileNotFoundError):
            LOCK_FILE.unlink(missing_ok=True)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    atexit.register(release_lock)
    logger.info(f"Lock acquired (PID {os.getpid()})")


def release_lock():
    LOCK_FILE.unlink(missing_ok=True)


# =============================================================================
# Main
# =============================================================================
def main():
    ensure_dirs()
    acquire_lock()

    logger.info("=" * 60)
    logger.info("BOOTH Popular Items Scraper")
    logger.info(f"  Min likes: {MIN_LIKES}")
    logger.info(f"  Image: {IMAGE_MAX_SIZE}px {IMAGE_FORMAT} q={IMAGE_QUALITY}")
    logger.info(f"  R2: {'ENABLED → ' + R2_BUCKET if R2_ENABLED else 'DISABLED'}")
    logger.info("=" * 60)

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("all", "phase1", "1"):
        phase1_collect_urls()

    if mode in ("all", "phase2", "2"):
        phase2_collect_details()

    # Summary
    p1 = load_existing_items(PHASE1_OUTPUT)
    p2 = load_existing_items(PHASE2_OUTPUT)
    logger.info("=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info(f"  Phase 1 (URLs):   {len(p1)} items")
    logger.info(f"  Phase 2 (Detail): {len(p2)} items")
    logger.info(f"  Output:")
    logger.info(f"    {PHASE1_OUTPUT}")
    logger.info(f"    {PHASE2_OUTPUT}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
