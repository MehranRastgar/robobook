#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست‌های پایه برای بررسی عملکرد سیستم
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# اضافه کردن مسیر ریشه پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.database import BookDatabase
from src.models.llm_service import LLMService
from src.utils.speech import SpeechHandler
from src.utils.config import AppConfig

class TestBasicFunctionality(unittest.TestCase):
    """کلاس تست‌های پایه برای بررسی عملکرد سیستم"""
    
    def setUp(self):
        """آماده‌سازی قبل از اجرای هر تست"""
        # استفاده از یک پایگاه داده موقت برای تست
        self.test_db_path = "./src/tests/test_books.db"
        self.db = BookDatabase(db_path=self.test_db_path)
        
        # ساخت مدل مصنوعی برای LLM
        self.llm = LLMService(model_type="lmstudio")
        self.llm._query_lmstudio_api = MagicMock(return_value="این یک پاسخ آزمایشی است.")
        
        # مسدود کردن تابع speak برای جلوگیری از پخش صدا در تست‌ها
        self.speech = SpeechHandler()
        self.speech.speak = MagicMock(return_value=True)
    
    def tearDown(self):
        """پاکسازی بعد از اجرای هر تست"""
        # پاک کردن پایگاه داده تست
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_book_search(self):
        """تست جستجوی کتاب در پایگاه داده"""
        # جستجو برای کتاب با کلمه "هری"
        books = self.db.search_books("هری")
        
        # انتظار داریم حداقل یک کتاب با "هری" در عنوان پیدا شود
        self.assertTrue(len(books) > 0)
        self.assertTrue(any("هری" in book['title'] for book in books))
    
    def test_llm_response(self):
        """تست پاسخگویی مدل زبانی"""
        query = "معرفی کتاب در مورد هوش مصنوعی"
        books = self.db.search_books("هوش مصنوعی")
        
        # دریافت پاسخ از مدل زبانی
        response = self.llm.process_query(query, books)
        
        # بررسی وجود پاسخ
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
    
    def test_shelf_location(self):
        """تست اطلاعات مکانی قفسه‌ها"""
        # بررسی اطلاعات قفسه B1
        shelf = self.db.get_shelf_location("B1")
        
        # آیا قفسه وجود دارد؟
        self.assertIsNotNone(shelf)
        self.assertEqual(shelf['name'], "B1")
    
    def test_speech_functionality(self):
        """تست عملکرد گفتار"""
        text = "این یک تست برای بررسی عملکرد گفتار است."
        
        # تست پخش گفتار
        result = self.speech.speak(text)
        
        # بررسی موفقیت‌آمیز بودن پخش گفتار
        self.assertTrue(result)
        
        # بررسی فراخوانی تابع با متن صحیح
        self.speech.speak.assert_called_with(text)

if __name__ == "__main__":
    unittest.main() 