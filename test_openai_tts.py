#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست تبدیل متن به گفتار با OpenAI برای زبان فارسی
"""

import os
import sys
import logging
from dotenv import load_dotenv

# تنظیم مسیر برای import‌های نسبی
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.speech import SpeechHandler
from src.utils.config import AppConfig

# تنظیم logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("OpenAI-TTS-Test")

def test_openai_tts():
    """تست تبدیل متن به گفتار با OpenAI برای زبان فارسی"""
    
    # بارگذاری تنظیمات
    load_dotenv()
    config = AppConfig()
    
    # اطمینان از تنظیم کلید API
    if not config.openai_api_key:
        logger.error("OPENAI_API_KEY is not set. Please set it in .env file.")
        return False
    
    # تنظیم کلید API به عنوان متغیر محیطی
    if os.environ.get('OPENAI_API_KEY') is None:
        os.environ['OPENAI_API_KEY'] = config.openai_api_key
    
    # نمونه متن فارسی برای تست
    test_text = "سلام! این یک تست تبدیل متن به گفتار با OpenAI برای زبان فارسی است. امیدوارم این آزمایش موفقیت‌آمیز باشد."
    
    # ایجاد نمونه از SpeechHandler
    tts = SpeechHandler(tts_type="openai")
    
    # بررسی دسترسی به OpenAI
    if not tts.openai_available:
        logger.error("OpenAI TTS is not available. Please check your installation and API key.")
        return False
    
    # تست تبدیل متن به گفتار
    logger.info("Testing OpenAI TTS with Persian text:")
    logger.info(f"Text: {test_text}")
    
    result = tts.speak(test_text)
    
    if result:
        logger.info("OpenAI TTS test completed successfully!")
    else:
        logger.error("OpenAI TTS test failed!")
    
    return result

if __name__ == "__main__":
    test_openai_tts() 