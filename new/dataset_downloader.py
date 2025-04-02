import os
import requests
from tqdm import tqdm
import logging
from datasets import load_dataset
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATASET_URL = "https://huggingface.co/datasets/TheBritishLibrary/blbooks/resolve/main/data/train-00000-of-00001.parquet"
CACHE_DIR = "./dataset_cache"
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def download_with_resume(url: str, dest_file: str):
    """Download a file with resume capability"""
    
    # Create cache directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    
    # Get the total file size
    response = requests.head(url)
    total_size = int(response.headers.get('content-length', 0))
    
    # If file exists, get the current size
    initial_pos = os.path.getsize(dest_file) if os.path.exists(dest_file) else 0
    
    # If file is complete, skip download
    if initial_pos >= total_size and total_size > 0:
        logger.info("File already completely downloaded")
        return True
    
    # Resume download from where we left off
    headers = {'Range': f'bytes={initial_pos}-'} if initial_pos > 0 else {}
    
    try:
        response = requests.get(url, headers=headers, stream=True)
        
        # Setup progress bar
        mode = 'ab' if initial_pos > 0 else 'wb'
        desc = 'Resuming download' if initial_pos > 0 else 'Downloading'
        total = total_size - initial_pos if initial_pos > 0 else total_size
        
        with open(dest_file, mode) as f:
            with tqdm(
                total=total,
                initial=initial_pos,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                desc=desc
            ) as pbar:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    size = f.write(chunk)
                    pbar.update(size)
                    
        logger.info("Download completed successfully")
        
    except KeyboardInterrupt:
        logger.warning("\nDownload interrupted. You can resume later.")
        return False
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        return False
    
    return True

def verify_dataset():
    """Verify the downloaded dataset"""
    try:
        logger.info("Verifying dataset...")
        dataset = load_dataset(
            "TheBritishLibrary/blbooks",
            split="train",
            trust_remote_code=True,
            cache_dir=CACHE_DIR
        )
        logger.info(f"Dataset verified. Contains {len(dataset)} entries")
        return True
    except Exception as e:
        logger.error(f"Dataset verification failed: {str(e)}")
        return False

def clean_cache():
    """Clean the dataset cache"""
    try:
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            logger.info("Cache cleaned successfully")
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")

def main():
    dest_file = os.path.join(CACHE_DIR, "blbooks_dataset.parquet")
    
    while True:
        print("\nBritish Library Dataset Downloader")
        print("1. Start/Resume Download")
        print("2. Verify Dataset")
        print("3. Clean Cache")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            success = download_with_resume(DATASET_URL, dest_file)
            if success:
                verify_dataset()
        elif choice == '2':
            verify_dataset()
        elif choice == '3':
            clean_cache()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 