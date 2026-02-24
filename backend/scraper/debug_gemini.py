import os
import json
import logging
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logging.error("GEMINI_API_KEY environment variable is not set.")
    exit(1)

genai.configure(api_key=api_key)
print(f"GenAI Version: {genai.__version__}")
model = genai.GenerativeModel('gemini-1.5-flash')

import traceback

def debug_one():
    dataset_dir = "data/yolo_dataset/images"
    image_files = [f for f in os.listdir(dataset_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    print("Testing TEXT ONLY first...")
    try:
        response = model.generate_content("Hello, world!")
        print(f"Text response: {response.text}")
    except:
        print(f"Text error:\n{traceback.format_exc()}")

    if not image_files:
        print("No images found.")
        return

    # Find any image in the dataset for testing
    dataset_dir = "data/yolo_dataset/images"
    image_files = [f for f in os.listdir(dataset_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    if not image_files: return
    
    # Copy to a very simple path to avoid ANY encoding issues
    import shutil
    src_img = os.path.join(dataset_dir, image_files[0])
    img_path = "debug_tmp.jpg"
    shutil.copy(src_img, img_path)
    
    print(f"Testing IMAGE with simple path: {img_path}")
    
    try:
        from PIL import Image
        img = Image.open(img_path)
        
        # Explicit model name
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # Simplest call possible
        response = model.generate_content(img)
        print(f"Image success! Response: {response.text}")
    except:
        print(f"Image error:\n{traceback.format_exc()}")

if __name__ == "__main__":
    debug_one()
