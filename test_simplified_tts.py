#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified Persian TTS tester using pyttsx3
"""

import pyttsx3
import time
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimplifiedTTS")

class SimplifiedTTS:
    def __init__(self, rate=150, volume=1.0, voice_id=None):
        """Initialize the TTS engine with custom settings"""
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.engine = None
        self.tts_lock = threading.Lock()
        self.busy = False
        
        logger.info("Initializing pyttsx3 engine...")
        self._setup_engine()
        
    def _setup_engine(self):
        """Setup the pyttsx3 engine with proper settings"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            
            # Print all available voices
            voices = self.engine.getProperty('voices')
            logger.info(f"Found {len(voices)} voices:")
            for i, voice in enumerate(voices):
                logger.info(f"Voice {i}: {voice.name} ({voice.id})")
            
            # Use the first voice by default if not specified
            if not self.voice_id and voices:
                self.engine.setProperty('voice', voices[0].id)
                logger.info(f"Using default voice: {voices[0].name}")
                
            logger.info("Engine setup complete")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            self.engine = None
    
    def speak(self, text, blocking=True):
        """Speak the given text"""
        if not text or self.engine is None:
            logger.warning("Cannot speak: No text provided or engine not available")
            return False
        
        with self.tts_lock:
            try:
                self.busy = True
                logger.info(f"Speaking text: {text[:50]}...")
                
                if blocking:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    def run_in_thread():
                        try:
                            self.engine.say(text)
                            self.engine.runAndWait()
                        except Exception as e:
                            logger.error(f"Error in speech thread: {e}")
                        finally:
                            self.busy = False
                    
                    thread = threading.Thread(target=run_in_thread)
                    thread.daemon = True
                    thread.start()
                
                if blocking:
                    self.busy = False
                
                return True
            except Exception as e:
                self.busy = False
                logger.error(f"Error in speech: {e}")
                return False

def main():
    """Test the simplified TTS with English and Persian text"""
    tts = SimplifiedTTS()
    
    # Wait for engine to initialize
    time.sleep(1)
    
    # Test English text
    print("\nTesting English text...")
    english_text = "Hello, this is a test for text to speech."
    success = tts.speak(english_text)
    print(f"English TTS success: {success}")
    
    # Wait between tests
    time.sleep(1)
    
    # Test Persian text
    print("\nTesting Persian text...")
    persian_text = "سلام، این یک آزمایش برای تبدیل متن به گفتار است."
    success = tts.speak(persian_text)
    print(f"Persian TTS success: {success}")
    
    # Test with second voice if available
    voices = tts.engine.getProperty('voices')
    if len(voices) > 1:
        print("\nTesting with second voice...")
        tts = SimplifiedTTS(voice_id=voices[1].id)
        time.sleep(1)
        
        success = tts.speak(persian_text)
        print(f"Persian TTS with second voice success: {success}")
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 