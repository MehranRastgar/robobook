from datasets import load_dataset
import logging
from typing import List, Dict, Optional
import os
from difflib import SequenceMatcher
from collections import Counter
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class USPDBooks:
    def __init__(self, cache_dir: str = "./dataset_cache"):
        self.cache_dir = cache_dir
        self.dataset = None
        self._stats = None
        
    def load_dataset(self):
        """Load the US-PD-Books dataset"""
        try:
            logger.info("Loading US-PD-Books dataset...")
            self.dataset = load_dataset(
                "storytracer/US-PD-Books",
                split="train",
                cache_dir=self.cache_dir
            )
            
            # Log dataset information
            logger.info(f"Dataset loaded successfully. Contains {len(self.dataset)} books")
            
            # Sample and log multiple books to understand the data structure
            sample_size = min(5, len(self.dataset))
            logger.info(f"Sampling {sample_size} books to understand data structure:")
            for i in range(sample_size):
                book = self.dataset[i]
                logger.info(f"Raw book {i}: {book}")
                processed = self._process_book(book)
                logger.info(f"Processed book {i}: {processed}")
            
            # Check for books with years
            years = []
            for i in range(min(100, len(self.dataset))):
                book = self._process_book(self.dataset[i])
                if book and book['year'] > 0:
                    years.append(book['year'])
            
            if years:
                logger.info(f"Year range in first 100 books: {min(years)} to {max(years)}")
                logger.info(f"Average year: {sum(years) / len(years)}")
            else:
                logger.warning("No valid years found in the first 100 books!")
            
            return True
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            return False
    
    def _process_book(self, book) -> Optional[Dict]:
        """Process a book item into a dictionary format"""
        try:
            if isinstance(book, str):
                # If it's a string, try to extract information
                parts = book.split('|')
                if len(parts) >= 6:
                    year_str = parts[2].strip()
                    year = int(year_str) if year_str.isdigit() else 0
                    logger.debug(f"Processing string book - Year string: '{year_str}', Parsed year: {year}")
                    
                    return {
                        'title': parts[0].strip(),
                        'author': parts[1].strip(),
                        'year': year,
                        'page_count': int(parts[3].strip()) if parts[3].strip().isdigit() else 0,
                        'ocaid': parts[4].strip(),
                        'full_text_url': parts[5].strip()
                    }
                return None
            elif isinstance(book, dict):
                year = int(book.get('year', 0))
                logger.debug(f"Processing dict book - Raw year: {book.get('year')}, Parsed year: {year}")
                
                return {
                    'title': str(book.get('title', '')),
                    'author': str(book.get('author', '')),
                    'year': year,
                    'page_count': int(book.get('page_count', 0)),
                    'ocaid': str(book.get('ocaid', '')),
                    'full_text_url': str(book.get('full_text_url', ''))
                }
            return None
        except Exception as e:
            logger.error(f"Error processing book: {str(e)}")
            return None
    
    def _similar(self, a: str, b: str) -> float:
        """Calculate string similarity ratio"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def get_dataset_stats(self) -> Dict:
        """Get statistics about the dataset"""
        if self._stats is None:
            try:
                if self.dataset is None:
                    if not self.load_dataset():
                        return {}
                
                # Process first 1000 books for quick stats
                sample_size = min(1000, len(self.dataset))
                years = []
                authors = []
                page_counts = []
                
                logger.info(f"Processing {sample_size} books for statistics...")
                for i in range(sample_size):
                    book = self._process_book(self.dataset[i])
                    if book:
                        if book['year'] > 0:
                            years.append(book['year'])
                        if book['author']:
                            authors.append(book['author'])
                        if book['page_count'] > 0:
                            page_counts.append(book['page_count'])
                
                # Calculate statistics
                self._stats = {
                    'total_books': len(self.dataset),
                    'sample_size': sample_size,
                    'year_range': {
                        'min': min(years) if years else 0,
                        'max': max(years) if years else 0,
                        'average': sum(years) / len(years) if years else 0
                    },
                    'top_authors': Counter(authors).most_common(10),
                    'page_count_stats': {
                        'min': min(page_counts) if page_counts else 0,
                        'max': max(page_counts) if page_counts else 0,
                        'average': sum(page_counts) / len(page_counts) if page_counts else 0
                    }
                }
                
                # Log detailed statistics
                logger.info(f"Dataset contains {self._stats['total_books']} total books")
                logger.info(f"Year range: {self._stats['year_range']['min']} to {self._stats['year_range']['max']}")
                logger.info(f"Average year: {self._stats['year_range']['average']}")
                logger.info(f"Top authors: {self._stats['top_authors']}")
                
            except Exception as e:
                logger.error(f"Error calculating dataset stats: {str(e)}")
                self._stats = {}
        
        return self._stats
    
    def search_books(self, 
                    title: Optional[str] = None, 
                    author: Optional[str] = None, 
                    year: Optional[int] = None,
                    min_year: Optional[int] = None,
                    max_year: Optional[int] = None,
                    limit: int = 10,
                    sort_by: str = 'relevance') -> List[Dict]:
        """Search books by title, author, or year"""
        if self.dataset is None:
            if not self.load_dataset():
                return []
        
        try:
            # Get dataset stats first
            stats = self.get_dataset_stats()
            logger.info(f"Dataset statistics: {stats}")
            
            # Log search parameters
            logger.info(f"Searching books with parameters: title={title}, author={author}, "
                       f"year={year}, min_year={min_year}, max_year={max_year}")
            
            # Process all books
            results = []
            total_books = len(self.dataset)
            logger.info(f"Processing {total_books} books...")
            
            # Pre-process author search terms if provided
            author_terms = []
            if author:
                # Split author name into parts and clean them
                author_terms = [term.strip().lower() for term in author.split()]
                logger.info(f"Searching for author terms: {author_terms}")
            
            for i in range(total_books):
                processed_book = self._process_book(self.dataset[i])
                if not processed_book:
                    continue
                    
                matches = True
                if title:
                    # Check for partial matches in title
                    title_matches = any(
                        title.lower() in word.lower() 
                        for word in processed_book['title'].split()
                    )
                    matches &= title_matches
                    
                if author_terms:
                    # Split author name into parts
                    book_author_parts = [part.strip().lower() for part in processed_book['author'].split()]
                    logger.debug(f"Book author parts: {book_author_parts}")
                    
                    # Check if any search term matches any part of the author name
                    author_matches = False
                    for term in author_terms:
                        # Check for exact matches
                        if term in book_author_parts:
                            author_matches = True
                            break
                        # Check for partial matches
                        for part in book_author_parts:
                            if term in part or part in term:
                                author_matches = True
                                break
                        if author_matches:
                            break
                    
                    matches &= author_matches
                    logger.debug(f"Author match for '{processed_book['author']}': {author_matches}")
                    
                if year:
                    # Allow year to be within a range
                    book_year = processed_book['year']
                    if book_year > 0:  # Only check if year is valid
                        matches &= abs(book_year - year) <= 1  # Allow 1 year difference
                
                # Apply year range filtering
                book_year = processed_book['year']
                if book_year > 0:  # Only check if year is valid
                    if min_year:
                        matches &= book_year >= min_year
                    if max_year:
                        matches &= book_year <= max_year
                
                if matches:
                    # Calculate relevance score
                    score = 0
                    if title:
                        score += self._similar(title, processed_book['title'])
                    if author_terms:
                        # Calculate author similarity based on matching terms
                        author_score = 0
                        for term in author_terms:
                            max_term_similarity = max(
                                self._similar(term, part) 
                                for part in processed_book['author'].split()
                            )
                            author_score += max_term_similarity
                        score += author_score / len(author_terms)
                    
                    if year and processed_book['year'] > 0:
                        score += 1 - (abs(processed_book['year'] - year) / 100)
                    
                    processed_book['relevance_score'] = score
                    results.append(processed_book)
            
            # Log number of matches found
            logger.info(f"Found {len(results)} matching books")
            
            # Sort results based on specified criteria
            if sort_by == 'year':
                results.sort(key=lambda x: (x['year'], x['relevance_score']), reverse=True)
            elif sort_by == 'title':
                results.sort(key=lambda x: (x['title'].lower(), x['relevance_score']))
            else:  # default to relevance
                results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Log final results
            logger.info(f"Returning {len(results[:limit])} books after sorting")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching books: {str(e)}")
            return []
    
    def get_book_content(self, ocaid: str) -> Optional[Dict]:
        """Get full content of a book by its Internet Archive ID"""
        if self.dataset is None:
            if not self.load_dataset():
                return None
        
        try:
            # Find book by ocaid
            for book in self.dataset:
                processed_book = self._process_book(book)
                if processed_book and processed_book['ocaid'] == ocaid:
                    return processed_book
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting book content: {str(e)}")
            return None
    
    def get_random_books(self, limit: int = 10) -> List[Dict]:
        """Get random books from the dataset"""
        if self.dataset is None:
            if not self.load_dataset():
                return []
        
        try:
            # Get random indices
            total_books = len(self.dataset)
            if total_books == 0:
                return []
                
            # Ensure we don't try to get more books than available
            limit = min(limit, total_books)
            
            # Get random indices
            random_indices = random.sample(range(total_books), limit)
            
            # Get books at random indices
            results = []
            for idx in random_indices:
                book = self._process_book(self.dataset[idx])
                if book:
                    results.append(book)
            
            logger.info(f"Returning {len(results)} random books")
            return results
            
        except Exception as e:
            logger.error(f"Error getting random books: {str(e)}")
            return [] 