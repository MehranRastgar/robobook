#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ماژول پیکربندی برنامه
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Literal

# بارگذاری متغیرهای محیطی
load_dotenv()

class AppConfig(BaseModel):
    """کلاس مدیریت پیکربندی برنامه"""
    
    # نوع مدل زبانی (LLama, LMStudio, یا OpenAI)
    model_type: Literal["llama", "lmstudio", "openai"] = Field(
        default=os.getenv("MODEL_TYPE", "lmstudio")
    )
    
    # کلید API برای سرویس‌های مدل زبانی
    api_key: Optional[str] = Field(
        default=os.getenv("API_KEY", None)
    )
    
    # آدرس API محلی LMStudio
    lmstudio_api_url: str = Field(
        default=os.getenv("LMSTUDIO_API_URL", "http://localhost:1234/v1")
    )
    
    # مسیر مدل محلی LLama
    llama_model_path: str = Field(
        default=os.getenv("LLAMA_MODEL_PATH", "./models/llama-2-7b-chat.gguf")
    )
    
    # مسیر پایگاه داده
    db_path: str = Field(
        default=os.getenv("DB_PATH", "./src/data/books.db")
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
        elif self.model_type == "openai":
            return "https://api.openai.com/v1"
        else:
            return None  # برای مدل محلی llama 