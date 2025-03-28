#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ماژول مدیریت پایگاه داده کتاب‌ها
"""

import os
import json
import sqlite3
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger("BookDatabase")

class BookDatabase:
    """کلاس مدیریت پایگاه داده کتاب‌ها"""
    
    def __init__(self, db_path: str = "./src/data/books.db"):
        """
        راه‌اندازی پایگاه داده
        
        Args:
            db_path: مسیر فایل پایگاه داده SQLite
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_db()
        logger.info(f"Book database initialized at {db_path}")
    
    def _ensure_db_directory(self):
        """اطمینان از وجود پوشه پایگاه داده"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """ایجاد اتصال به پایگاه داده"""
        return sqlite3.connect(self.db_path)
    
    def _initialize_db(self):
        """راه‌اندازی اولیه پایگاه داده و ایجاد جداول"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # ایجاد جدول کتاب‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    isbn TEXT,
                    publisher TEXT,
                    publish_year INTEGER,
                    language TEXT,
                    description TEXT,
                    price REAL,
                    page_count INTEGER,
                    category TEXT,
                    subcategory TEXT,
                    shelf_location TEXT NOT NULL,
                    stock INTEGER DEFAULT 0,
                    cover_image TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ایجاد جدول دسته‌بندی‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_id INTEGER,
                    description TEXT,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            ''')
            
            # ایجاد جدول قفسه‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shelves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    location TEXT NOT NULL,
                    description TEXT
                )
            ''')
            
            # ایجاد جدول کلمات کلیدی کتاب
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    FOREIGN KEY (book_id) REFERENCES books (id),
                    UNIQUE(book_id, keyword)
                )
            ''')
            
            # ایجاد ایندکس‌ها برای جستجوی سریع‌تر
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_title ON books (title)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_author ON books (author)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_category ON books (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_shelf ON books (shelf_location)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords ON book_keywords (keyword)')
            
            conn.commit()
            
            # اضافه کردن داده‌های نمونه اگر جدول خالی است
            cursor.execute('SELECT COUNT(*) FROM books')
            count = cursor.fetchone()[0]
            
            if count == 0:
                self._add_sample_data()
            
            conn.close()
            logger.info("Database schema initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _add_sample_data(self):
        """اضافه کردن داده‌های نمونه به پایگاه داده"""
        try:
            # اضافه کردن قفسه‌های نمونه
            shelves = [
                ('A1', 'طبقه اول، راهروی اول', 'قفسه رمان‌های کلاسیک'),
                ('A2', 'طبقه اول، راهروی اول', 'قفسه رمان‌های معاصر'),
                ('B1', 'طبقه اول، راهروی دوم', 'قفسه کتب علمی'),
                ('C1', 'طبقه دوم، راهروی اول', 'قفسه کتب کودک و نوجوان'),
                ('D1', 'طبقه دوم، راهروی دوم', 'قفسه کتب تاریخی')
            ]
            
            # اضافه کردن دسته‌بندی‌های نمونه
            categories = [
                ('رمان', None, 'کتاب‌های داستانی و رمان'),
                ('رمان کلاسیک', 1, 'رمان‌های کلاسیک جهان'),
                ('رمان معاصر', 1, 'رمان‌های نویسندگان معاصر'),
                ('علمی', None, 'کتاب‌های علمی و آموزشی'),
                ('کامپیوتر', 4, 'کتاب‌های علوم کامپیوتر و برنامه‌نویسی'),
                ('فیزیک', 4, 'کتاب‌های فیزیک'),
                ('کودک و نوجوان', None, 'کتاب‌های مخصوص کودکان و نوجوانان'),
                ('تاریخ', None, 'کتاب‌های تاریخی')
            ]
            
            # اضافه کردن کتاب‌های نمونه
            books = [
                ('صد سال تنهایی', 'گابریل گارسیا مارکز', '9789643514921', 'نشر چشمه', 1389, 'فارسی',
                 'رمان صد سال تنهایی شاهکار گابریل گارسیا مارکز، نویسنده کلمبیایی و برنده جایزه نوبل ادبیات است.',
                 65000, 495, 'رمان کلاسیک', None, 'A1', 10, None),
                
                ('کیمیاگر', 'پائولو کوئیلو', '9789643511555', 'نشر کاروان', 1392, 'فارسی',
                 'داستان چوپان جوانی به نام سانتیاگو که به دنبال گنج خود سفر می‌کند.',
                 45000, 180, 'رمان معاصر', None, 'A2', 15, None),
                
                ('آناکارنینا', 'لئو تولستوی', '9789643116460', 'نشر نیلوفر', 1387, 'فارسی',
                 'رمان روسی که به روابط انسانی و مسائل اجتماعی می‌پردازد.',
                 95000, 850, 'رمان کلاسیک', None, 'A1', 5, None),
                
                ('یادگیری عمیق', 'یان گودفلو', '9786003249875', 'نشر نص', 1400, 'فارسی',
                 'کتابی جامع در زمینه یادگیری عمیق و هوش مصنوعی.',
                 150000, 720, 'کامپیوتر', None, 'B1', 7, None),
                
                ('هری پاتر و سنگ جادو', 'جی.کی. رولینگ', '9789643191474', 'نشر کتابسرای تندیس', 1390, 'فارسی',
                 'کتاب اول از مجموعه هری پاتر که ماجراهای پسری جادوگر را روایت می‌کند.',
                 55000, 350, 'کودک و نوجوان', None, 'C1', 20, None),
                
                ('تاریخ ایران باستان', 'حسن پیرنیا', '9789644881572', 'نشر اساطیر', 1395, 'فارسی',
                 'پژوهشی دقیق در تاریخ ایران باستان از آغاز تا پایان دوره ساسانیان.',
                 85000, 520, 'تاریخ', None, 'D1', 8, None),
                
                ('باشگاه مشت‌زنی', 'چاک پالانیک', '9789643116453', 'نشر چشمه', 1396, 'فارسی',
                 'رمانی سورئال درباره مردی بی‌نام که از زندگی مدرن خسته شده است.',
                 48000, 250, 'رمان معاصر', None, 'A2', 12, None),
                
                ('نظریه همه چیز', 'استیون هاوکینگ', '9786003042209', 'نشر مازیار', 1393, 'فارسی',
                 'کتابی درباره نظریات فیزیک مدرن و کیهان‌شناسی به زبانی ساده.',
                 75000, 280, 'فیزیک', None, 'B1', 9, None)
            ]
            
            # اضافه کردن کلمات کلیدی نمونه برای کتاب‌ها
            keywords = [
                (1, 'رئالیسم جادویی'),
                (1, 'آمریکای لاتین'),
                (1, 'خانواده بوئندیا'),
                (2, 'سفر معنوی'),
                (2, 'خودشناسی'),
                (3, 'ادبیات روسیه'),
                (3, 'عشق'),
                (4, 'هوش مصنوعی'),
                (4, 'یادگیری ماشین'),
                (5, 'فانتزی'),
                (5, 'جادوگری'),
                (6, 'ایران باستان'),
                (6, 'هخامنشیان'),
                (7, 'آنارشیسم'),
                (7, 'هویت'),
                (8, 'کیهان‌شناسی'),
                (8, 'نسبیت')
            ]
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # اضافه کردن قفسه‌ها
            cursor.executemany(
                'INSERT INTO shelves (name, location, description) VALUES (?, ?, ?)',
                shelves
            )
            
            # اضافه کردن دسته‌بندی‌ها
            cursor.executemany(
                'INSERT INTO categories (name, parent_id, description) VALUES (?, ?, ?)',
                categories
            )
            
            # اضافه کردن کتاب‌ها
            cursor.executemany(
                'INSERT INTO books (title, author, isbn, publisher, publish_year, language, description, price, page_count, category, subcategory, shelf_location, stock, cover_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                books
            )
            
            # اضافه کردن کلمات کلیدی
            cursor.executemany(
                'INSERT INTO book_keywords (book_id, keyword) VALUES (?, ?)',
                keywords
            )
            
            conn.commit()
            conn.close()
            logger.info("Sample data added to database")
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")
    
    def search_books(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        جستجوی کتاب‌ها بر اساس عبارت جستجو
        
        Args:
            query: عبارت جستجو
            limit: حداکثر تعداد نتایج
            
        Returns:
            لیستی از کتاب‌های یافته شده
        """
        try:
            conn = self._get_connection()
            # تبدیل کوئری به فرمت مناسب برای جستجو با LIKE
            search_term = f"%{query.strip()}%"
            # پیدا کردن کلمات کلیدی جستجو
            search_words = query.strip().split()
            # ساخت الگوهای جستجو برای هر کلمه
            word_patterns = [f"%{word}%" for word in search_words]
            
            cursor = conn.cursor()
            
            # جستجوی اصلی
            sql = '''
                SELECT DISTINCT b.id, b.title, b.author, b.isbn, b.publisher, b.publish_year, 
                       b.language, b.description, b.price, b.page_count, b.category,
                       b.subcategory, b.shelf_location, b.stock, b.cover_image
                FROM books b
                WHERE 
            '''
            
            # اضافه کردن شرط‌های جستجو برای کل عبارت
            conditions = [
                "b.title LIKE ?", 
                "b.author LIKE ?", 
                "b.description LIKE ?", 
                "b.category LIKE ?"
            ]
            
            params = []
            
            # جستجوی دقیق با کل عبارت
            sql += " OR ".join(conditions)
            params.extend([search_term] * len(conditions))
            
            # جستجوی کلمات کلیدی
            sql += " UNION SELECT DISTINCT b.id, b.title, b.author, b.isbn, b.publisher, b.publish_year, b.language, b.description, b.price, b.page_count, b.category, b.subcategory, b.shelf_location, b.stock, b.cover_image FROM books b, book_keywords k WHERE b.id = k.book_id AND k.keyword LIKE ?"
            params.append(search_term)
            
            # جستجوی کلمه به کلمه برای نتایج بهتر
            if len(search_words) > 1:
                for word_pattern in word_patterns:
                    sql += " UNION SELECT DISTINCT b.id, b.title, b.author, b.isbn, b.publisher, b.publish_year, b.language, b.description, b.price, b.page_count, b.category, b.subcategory, b.shelf_location, b.stock, b.cover_image FROM books b WHERE b.author LIKE ?"
                    params.append(word_pattern)
            
            sql += " LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            
            columns = [col[0] for col in cursor.description]
            books = []
            
            for row in cursor.fetchall():
                book = dict(zip(columns, row))
                books.append(book)
            
            conn.close()
            logger.info(f"Found {len(books)} books matching '{query}'")
            return books
        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return []
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک کتاب بر اساس شناسه
        
        Args:
            book_id: شناسه کتاب
            
        Returns:
            اطلاعات کتاب یا None در صورت عدم وجود
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT b.id, b.title, b.author, b.isbn, b.publisher, b.publish_year,
                       b.language, b.description, b.price, b.page_count, b.category,
                       b.subcategory, b.shelf_location, b.stock, b.cover_image,
                       s.name as shelf_name, s.location as shelf_location_detail
                FROM books b
                LEFT JOIN shelves s ON b.shelf_location = s.name
                WHERE b.id = ?
            ''', (book_id,))
            
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            columns = [col[0] for col in cursor.description]
            book = dict(zip(columns, row))
            
            # دریافت کلمات کلیدی این کتاب
            cursor.execute('SELECT keyword FROM book_keywords WHERE book_id = ?', (book_id,))
            keywords = [row[0] for row in cursor.fetchall()]
            book['keywords'] = keywords
            
            conn.close()
            return book
        except Exception as e:
            logger.error(f"Error getting book with ID {book_id}: {e}")
            return None
    
    def get_shelf_location(self, shelf_code: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات مکانی یک قفسه
        
        Args:
            shelf_code: کد قفسه
            
        Returns:
            اطلاعات مکانی قفسه یا None در صورت عدم وجود
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, location, description
                FROM shelves
                WHERE name = ?
            ''', (shelf_code,))
            
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            columns = [col[0] for col in cursor.description]
            shelf = dict(zip(columns, row))
            
            conn.close()
            return shelf
        except Exception as e:
            logger.error(f"Error getting shelf location for {shelf_code}: {e}")
            return None
    
    def get_books_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت کتاب‌ها بر اساس دسته‌بندی
        
        Args:
            category: نام دسته‌بندی
            limit: حداکثر تعداد نتایج
            
        Returns:
            لیستی از کتاب‌های این دسته‌بندی
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, author, description, price, shelf_location, stock
                FROM books
                WHERE category = ?
                LIMIT ?
            ''', (category, limit))
            
            columns = [col[0] for col in cursor.description]
            books = []
            
            for row in cursor.fetchall():
                book = dict(zip(columns, row))
                books.append(book)
            
            conn.close()
            return books
        except Exception as e:
            logger.error(f"Error getting books in category {category}: {e}")
            return []
    
    def get_book_categories(self) -> List[str]:
        """
        دریافت لیست همه دسته‌بندی‌های کتاب
        
        Returns:
            لیست دسته‌بندی‌ها
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT name FROM categories ORDER BY name')
            categories = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return categories
        except Exception as e:
            logger.error(f"Error getting book categories: {e}")
            return []
    
    def add_book(self, book_data: Dict[str, Any]) -> Optional[int]:
        """
        اضافه کردن کتاب جدید به پایگاه داده
        
        Args:
            book_data: اطلاعات کتاب جدید
            
        Returns:
            شناسه کتاب جدید یا None در صورت خطا
        """
        required_fields = ['title', 'author', 'shelf_location']
        for field in required_fields:
            if field not in book_data or not book_data[field]:
                logger.error(f"Missing required field: {field}")
                return None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # استخراج اطلاعات اصلی کتاب
            title = book_data.get('title')
            author = book_data.get('author')
            isbn = book_data.get('isbn')
            publisher = book_data.get('publisher')
            publish_year = book_data.get('publish_year')
            language = book_data.get('language', 'فارسی')
            description = book_data.get('description', '')
            price = book_data.get('price', 0)
            page_count = book_data.get('page_count', 0)
            category = book_data.get('category')
            subcategory = book_data.get('subcategory')
            shelf_location = book_data.get('shelf_location')
            stock = book_data.get('stock', 0)
            cover_image = book_data.get('cover_image')
            
            # اضافه کردن کتاب
            cursor.execute('''
                INSERT INTO books (
                    title, author, isbn, publisher, publish_year, language,
                    description, price, page_count, category, subcategory,
                    shelf_location, stock, cover_image
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title, author, isbn, publisher, publish_year, language,
                description, price, page_count, category, subcategory,
                shelf_location, stock, cover_image
            ))
            
            book_id = cursor.lastrowid
            
            # اضافه کردن کلمات کلیدی اگر موجود باشند
            keywords = book_data.get('keywords', [])
            for keyword in keywords:
                cursor.execute(
                    'INSERT INTO book_keywords (book_id, keyword) VALUES (?, ?)',
                    (book_id, keyword)
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added new book: {title} (ID: {book_id})")
            return book_id
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            return None 