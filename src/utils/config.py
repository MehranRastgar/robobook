#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ماژول تنظیمات برنامه
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, ClassVar

logger = logging.getLogger("AppConfig")

# بارگذاری متغیرهای محیطی
load_dotenv()

# تعیین مسیر اصلی پروژه
PROJECT_ROOT = Path(__file__).parent.parent.parent

class AppConfig(BaseModel):
    """کلاس مدیریت تنظیمات برنامه"""
    
    # تنظیم مقادیر پیش‌فرض
    defaults: ClassVar[Dict[str, Any]] = {
        "model_type": "4o-mini",  # تغییر مدل پیش‌فرض به 4o-mini
        "db_path": str(PROJECT_ROOT / "src" / "data" / "books.db"),
        "speech_rate": 300,
        "speech_volume": 1.0,
        "tts_type": "openai",
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "azure_speech_key": os.getenv("AZURE_SPEECH_KEY", ""),
        "azure_service_region": os.getenv("AZURE_SERVICE_REGION", ""),
        "gtts_language": "fa"
    }
    
    # مسیر فایل تنظیمات
    config_path: str = Field(default=str(PROJECT_ROOT / "config.json"))
    
    # نوع مدل زبانی (LLama, LMStudio, یا OpenAI)
    model_type: Literal["llama", "lmstudio", "openai", "4o-mini"] = Field(
        default=os.getenv("MODEL_TYPE", "4o-mini")
    )
    
    # کلید API برای سرویس‌های مدل زبانی
    api_key: Optional[str] = Field(
        default=os.getenv("API_KEY", None)
    )
    
    # کلید API برای OpenAI (می‌تواند همان api_key یا متفاوت باشد)
    openai_api_key: Optional[str] = Field(
        default=os.getenv("OPENAI_API_KEY", os.getenv("API_KEY", None))
    )
    
    # نوع موتور تبدیل متن به گفتار
    tts_type: Literal["auto", "pyttsx3", "gtts", "espeak", "azure", "openai"] = Field(
        default=os.getenv("TTS_TYPE", "openai")  # پیش‌فرض OpenAI برای کیفیت بهتر فارسی
    )
    
    # مدل TTS OpenAI (gpt-4o-mini-tts برای کیفیت بهتر)
    openai_tts_model: str = Field(
        default=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    )
    
    # صدای OpenAI TTS (alloy برای صدای طبیعی‌تر)
    openai_tts_voice: str = Field(
        default=os.getenv("OPENAI_TTS_VOICE", "nova")
    )
    
    # سرعت TTS OpenAI (0.25 تا 4.0)
    openai_tts_speed: float = Field(
        default=float(os.getenv("OPENAI_TTS_SPEED", "0.7"))
    )
    
    # آدرس API محلی LMStudio
    lmstudio_api_url: str = Field(
        default=os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/v1")
    )
    
    # مسیر مدل محلی LLama
    llama_model_path: str = Field(
        default=str(PROJECT_ROOT / "models" / "llama-2-7b-chat.gguf")
    )
    
    # مسیر پایگاه داده
    db_path: str = Field(
        default=os.getenv("DB_PATH", str(PROJECT_ROOT / "src" / "data" / "books.db"))
    )
    
    # تنظیمات گفتار
    speech_rate: int = Field(
        default=int(os.getenv("SPEECH_RATE", "150"))
    )
    
    speech_volume: float = Field(
        default=float(os.getenv("SPEECH_VOLUME", "1.0"))
    )
    
    # تنظیمات مدل زبانی
    temperature: float = Field(
        default=float(os.getenv("TEMPERATURE", "0.7"))
    )
    
    max_tokens: int = Field(
        default=int(os.getenv("MAX_TOKENS", "1024"))
    )
    
    def __init__(self, **data):
        """راه‌اندازی تنظیمات برنامه"""
        # بارگذاری تنظیمات از فایل
        config_path = data.get("config_path", str(PROJECT_ROOT / "config.json"))
        config = self._load_config(config_path)
        
        # ترکیب تنظیمات از فایل با مقادیر پیش‌فرض
        combined_data = {**self.defaults, **config, **data}
        
        # فراخوانی سازنده کلاس پایه
        super().__init__(**combined_data)
        
        # اطمینان از وجود دایرکتوری‌های مورد نیاز
        self._ensure_directories()
    
    def _ensure_directories(self):
        """اطمینان از وجود دایرکتوری‌های مورد نیاز"""
        # ایجاد دایرکتوری داده‌ها
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # ایجاد دایرکتوری مدل‌ها
        model_dir = os.path.dirname(self.llama_model_path)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
    
    def get_model_settings(self):
        """دریافت تنظیمات مدل زبانی"""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def get_api_url(self):
        """دریافت آدرس API مناسب براساس نوع مدل"""
        if self.model_type == "lmstudio":
            return self.lmstudio_api_url
        elif self.model_type in ["openai", "4o-mini"]:
            return "https://api.openai.com/v1"
        else:
            return None  # برای مدل محلی llama 
    
    def get_tts_settings(self):
        """دریافت تنظیمات تبدیل متن به گفتار"""
        return {
            "tts_type": self.tts_type,
            "openai_tts_model": self.openai_tts_model,
            "openai_tts_voice": self.openai_tts_voice,
            "openai_tts_speed": self.openai_tts_speed,
            "speech_rate": self.speech_rate,
            "speech_volume": self.speech_volume,
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """بارگذاری تنظیمات از فایل"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {} 