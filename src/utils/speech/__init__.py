"""
ماژول مدیریت گفتار (تبدیل متن به گفتار و گفتار به متن)
"""

from .speech_handler import SpeechHandler
from .interfaces import BaseTTS, BaseSTT
from .tts.openai_tts import OpenAITTS
from .stt.openai_stt import OpenAISTT

__all__ = [
    'SpeechHandler',
    'BaseTTS',
    'BaseSTT',
    'OpenAITTS',
    'OpenAISTT'
] 