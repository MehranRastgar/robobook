# main.py
from datasets import load_dataset
from typing import List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CACHE_DIR = "./dataset_cache"

def get_books_by_name_and_language(book_name: str, language: str) -> List[Dict]:
    """
    Retrieve books from the British Library dataset based on name and language.
    """
    try:
        # Load the dataset from cache
        dataset = load_dataset(
            "TheBritishLibrary/blbooks",
            split="train",
            trust_remote_code=True,
            cache_dir=CACHE_DIR
        )
        
        # Filter based on book name and language
        filtered_dataset = dataset.filter(
            lambda x: book_name.lower() in x['title'].lower() and x['language'] == language
        )
        
        # Convert to list of dictionaries
        filtered_books = [{
            'title': book['title'],
            'language': book['language'],
            'author': book.get('author', 'Unknown'),
            'date': book.get('date', 'Unknown'),
            'publisher': book.get('publisher', 'Unknown'),
            'identifier': book.get('identifier', '')
        } for book in filtered_dataset]
        
        return filtered_books
        
    except Exception as e:
        logger.error(f"Error loading dataset: {str(e)}")
        logger.info("Make sure to download the dataset first using dataset_downloader.py")
        return []

def main():
    if not os.path.exists(CACHE_DIR):
        logger.error("Dataset not found. Please run dataset_downloader.py first")
        return
        
    book_name = "history"
    language = "eng"
    
    books = get_books_by_name_and_language(book_name, language)
    
    if books:
        print(f"\nFound {len(books)} matching books:\n")
        for book in books:
            print(f"Title: {book['title']}")
            print(f"Author: {book['author']}")
            print(f"Language: {book['language']}")
            print(f"Date: {book['date']}")
            print(f"Publisher: {book['publisher']}")
            print("-" * 50)
    else:
        print(f"No books found matching '{book_name}' in language '{language}'")

if __name__ == "__main__":
    main()