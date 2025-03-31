"""
ماژول OpenAI Text-to-Speech
"""

import os
import tempfile
import threading
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..interfaces import BaseTTS

logger = logging.getLogger("OpenAITTS")

class OpenAITTS(BaseTTS):
    """کلاس پیاده‌سازی OpenAI Text-to-Speech"""
    
    def __init__(self, api_key: Optional[str] = None, voice: str = "alloy", speed: float = 1.0):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.voice = voice
        self.speed = speed
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.is_available = True
                logger.info("OpenAI TTS initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI TTS: {e}")
                self.is_available = False
        else:
            logger.warning("OpenAI API key not found")
            self.is_available = False
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """تبدیل متن به گفتار و پخش آن با OpenAI"""
        if not self.is_available:
            return False
        
        try:
            # ایجاد فایل موقت برای صدا
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # تبدیل متن به گفتار
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
                speed=self.speed,
                response_format="mp3"
            )
            
            # ذخیره در فایل
            response.stream_to_file(temp_filename)
            
            if blocking:
                # پخش مستقیم
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()
                # پاکسازی
                os.unlink(temp_filename)
            else:
                # پخش در پس‌زمینه
                def play_audio():
                    try:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(temp_filename)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(10)
                        pygame.mixer.quit()
                        # پاکسازی
                        os.unlink(temp_filename)
                    except Exception as e:
                        logger.error(f"Error playing OpenAI audio: {e}")
                
                thread = threading.Thread(target=play_audio)
                thread.daemon = True
                thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error in OpenAI TTS: {e}")
            return False
    
    def save_to_file(self, text: str, filename: str) -> bool:
        """ذخیره گفتار در یک فایل صوتی"""
        if not self.is_available:
            return False
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text,
                speed=self.speed,
                response_format="mp3"
            )
            response.stream_to_file(filename)
            return True
        except Exception as e:
            logger.error(f"Error saving OpenAI audio to file: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """دریافت لیست صداهای موجود OpenAI"""
        return [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "male"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"}
        ] 