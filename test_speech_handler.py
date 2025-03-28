#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the SpeechHandler class with pyttsx3 for Persian text
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

# Add the project root to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SpeechHandler class
from src.utils.speech import SpeechHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestSpeechHandler")

# Load environment variables
load_dotenv()

def test_speech_handler():
    """Test the SpeechHandler class with pyttsx3 for Persian text"""
    
    # Get TTS settings from environment variables
    tts_type = os.getenv("TTS_TYPE", "pyttsx3")
    speech_rate = int(os.getenv("SPEECH_RATE", "150"))
    speech_volume = float(os.getenv("SPEECH_VOLUME", "1.0"))
    
    logger.info(f"Testing SpeechHandler with TTS type: {tts_type}")
    logger.info(f"Speech rate: {speech_rate}, Speech volume: {speech_volume}")
    
    # Initialize the SpeechHandler
    speech = SpeechHandler(
        rate=speech_rate,
        volume=speech_volume,
        tts_type=tts_type
    )
    
    # Test English text
    logger.info("Testing English text...")
    english_text = "Hello, this is a test for text to speech using the Speech Handler."
    success = speech.speak(english_text)
    logger.info(f"English TTS success: {success}")
    
    # Wait between tests
    time.sleep(1)
    
    # Test Persian text
    logger.info("Testing Persian text...")
    persian_text = "سلام، این یک آزمایش برای تبدیل متن به گفتار با استفاده از مدیریت گفتار است."
    success = speech.speak(persian_text)
    logger.info(f"Persian TTS success: {success}")
    
    # Test non-blocking mode
    logger.info("Testing non-blocking mode...")
    non_blocking_text = "این متن در حالت غیر انسدادی پخش می‌شود."
    success = speech.speak(non_blocking_text, blocking=False)
    logger.info(f"Non-blocking TTS started: {success}")
    
    # Wait for non-blocking speech to finish
    logger.info("Waiting for non-blocking speech to finish...")
    time.sleep(5)
    
    logger.info("All tests completed.")

if __name__ == "__main__":
    test_speech_handler() 