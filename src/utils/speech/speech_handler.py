"""
کلاس اصلی مدیریت گفتار
"""

import logging
import os
from typing import Optional
from .interfaces import BaseTTS, BaseSTT
from .tts.openai_tts import OpenAITTS
from .stt.openai_stt import OpenAISTT

logger = logging.getLogger("SpeechHandler")

class SpeechHandler:
    """کلاس اصلی مدیریت گفتار"""
    
    def __init__(self, tts_type: str = "auto", rate: int = 150, volume: float = 1.0, voice_id: Optional[str] = None):
        self.tts_type = tts_type.lower()
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.tts_engine = None
        self.stt_engine = None
        self._initialize_engines()
    
    def _initialize_engines(self):
        """راه‌اندازی موتورهای TTS و STT"""
        try:
            # راه‌اندازی موتور TTS
            if self.tts_type == "auto":
                # اول OpenAI را امتحان می‌کنیم
                self.tts_engine = OpenAITTS(voice="alloy")
                if not self.tts_engine.is_available:
                    logger.warning("OpenAI TTS not available")
                    self.tts_engine = None
            elif self.tts_type == "openai":
                self.tts_engine = OpenAITTS(voice="alloy")
            else:
                logger.warning(f"Unknown TTS type: {self.tts_type}")
            
            # راه‌اندازی موتور STT
            self.stt_engine = OpenAISTT()
            
            # بررسی وضعیت موتورها
            if self.tts_engine and self.tts_engine.is_available:
                logger.info("TTS engine initialized successfully")
            else:
                logger.warning("No TTS engine available")
            
            if self.stt_engine and self.stt_engine.is_available:
                logger.info("STT engine initialized successfully")
            else:
                logger.warning("No STT engine available")
                
        except Exception as e:
            logger.error(f"Error initializing speech engines: {e}")
            self.tts_engine = None
            self.stt_engine = None
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """تبدیل متن به گفتار و پخش آن"""
        if not text:
            logger.warning("Cannot speak: No text provided")
            return False
        
        if self.tts_engine and self.tts_engine.is_available:
            logger.info(f"Using TTS engine: {self.tts_engine.__class__.__name__}")
            return self.tts_engine.speak(text, blocking)
        else:
            logger.warning("No TTS engine available")
            return False
    
    def listen(self, timeout: int = 10, phrase_time_limit: int = 30) -> Optional[str]:
        """گوش دادن به صدای کاربر و تبدیل آن به متن"""
        if self.stt_engine and self.stt_engine.is_available:
            return self.stt_engine.listen(timeout, phrase_time_limit)
        else:
            logger.warning("No STT engine available")
            return None 