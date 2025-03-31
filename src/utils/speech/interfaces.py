"""
اینترفیس‌های پایه برای موتورهای گفتار
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class BaseTTS(ABC):
    """کلاس پایه برای موتورهای تبدیل متن به گفتار"""
    
    def __init__(self, rate: int = 150, volume: float = 1.0, voice_id: Optional[str] = None):
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.is_available = False
    
    @abstractmethod
    def speak(self, text: str, blocking: bool = True) -> bool:
        """تبدیل متن به گفتار و پخش آن"""
        pass
    
    @abstractmethod
    def save_to_file(self, text: str, filename: str) -> bool:
        """ذخیره گفتار در یک فایل صوتی"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """دریافت لیست صداهای موجود"""
        pass

class BaseSTT(ABC):
    """کلاس پایه برای موتورهای تبدیل گفتار به متن"""
    
    def __init__(self):
        self.is_available = False
    
    @abstractmethod
    def listen(self, timeout: int = 10, phrase_time_limit: int = 30) -> Optional[str]:
        """گوش دادن به صدای کاربر و تبدیل آن به متن"""
        pass 