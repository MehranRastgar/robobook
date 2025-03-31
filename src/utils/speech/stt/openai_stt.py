"""
ماژول OpenAI Speech-to-Text
"""

import os
import tempfile
import re
import logging
from typing import Optional
import speech_recognition as sr
from openai import OpenAI
from ..interfaces import BaseSTT

logger = logging.getLogger("OpenAISTT")

class OpenAISTT(BaseSTT):
    """کلاس پیاده‌سازی OpenAI Speech-to-Text"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.recognizer = sr.Recognizer()
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.is_available = True
                logger.info("OpenAI STT initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI STT: {e}")
                self.is_available = False
        else:
            logger.warning("OpenAI API key not found")
            self.is_available = False
    
    def listen(self, timeout: int = 10, phrase_time_limit: int = 30) -> Optional[str]:
        """گوش دادن به صدای کاربر و تبدیل آن به متن با OpenAI"""
        if not self.is_available:
            return None
        
        try:
            # دریافت لیست میکروفون‌های موجود
            available_mics = sr.Microphone.list_microphone_names()
            logger.info(f"Available microphones: {available_mics}")
            
            # استفاده از میکروفون پیش‌فرض
            mic_index = 0
            with sr.Microphone(device_index=mic_index, sample_rate=44100) as source:
                logger.info(f"Listening for speech using microphone: {available_mics[mic_index] if len(available_mics) > mic_index else 'default'}")
                
                # تنظیم برای نویز محیطی
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=3.0)
                
                # تنظیمات حساسیت تشخیص گفتار
                self.recognizer.energy_threshold = 250
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.dynamic_energy_adjustment_ratio = 1.5
                
                # تنظیمات مناسب برای گفتار فارسی
                self.recognizer.pause_threshold = 0.8
                self.recognizer.phrase_threshold = 0.3
                self.recognizer.non_speaking_duration = 0.5
                
                logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
                
                try:
                    logger.info("Waiting for speech (speak in Farsi)...")
                    audio = self.recognizer.listen(
                        source, 
                        timeout=timeout, 
                        phrase_time_limit=phrase_time_limit,
                        snowboy_configuration=None
                    )
                    logger.info(f"Audio captured: {len(audio.get_raw_data())} bytes")
                    
                    # ذخیره صدا در فایل موقت
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                        wav_data = audio.get_wav_data(convert_rate=44100, convert_width=2)
                        temp_file.write(wav_data)
                        temp_filename = temp_file.name
                    
                    # بررسی اندازه فایل
                    file_size = os.path.getsize(temp_filename)
                    logger.info(f"Audio saved to temporary file: {file_size} bytes")
                    
                    if file_size < 1000:
                        logger.warning("Audio file is very small, may not contain speech")
                    
                    # ارسال به OpenAI برای تبدیل به متن
                    with open(temp_filename, 'rb') as audio_file:
                        logger.info("Sending audio to OpenAI for transcription...")
                        response = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="fa",
                            prompt="این متن فارسی است. نمونه جملات: این کتاب در کتابفروشی ما موجود نیست. اگر مایلید، می‌توانم به شما کتاب‌های مشابه را پیشنهاد دهم. برای اطلاعات بیشتر، لطفاً موضوع، نویسنده یا سبک مورد نظر خود را مشخص کنید.",
                            response_format="text"
                        )
                    
                    # دریافت متن
                    if hasattr(response, 'text'):
                        text = response.text
                    else:
                        text = response
                    
                    # بررسی اگر متن به صورت حروف لاتین باشد
                    if text and not re.search('[\u0600-\u06FF]', text):
                        logger.warning(f"Text appears to be romanized rather than Farsi script: '{text}'")
                        # تلاش مجدد با راهنمایی قوی‌تر
                        with open(temp_filename, 'rb') as audio_file:
                            try:
                                logger.info("Retrying transcription with stronger Farsi hint...")
                                response = self.client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="fa",
                                    prompt="این یک متن فارسی است، لطفا به الفبای فارسی تبدیل کنید نه حروف لاتین. نمونه جملات: این کتاب در کتابفروشی ما موجود نیست. اگر مایلید، می‌توانم به شما کتاب‌های مشابه را پیشنهاد دهم. برای اطلاعات بیشتر، لطفاً موضوع، نویسنده یا سبک مورد نظر خود را مشخص کنید.",
                                    response_format="text"
                                )
                                
                                if hasattr(response, 'text'):
                                    text = response.text
                                else:
                                    text = response
                            except Exception as retry_error:
                                logger.error(f"Error in retry transcription: {retry_error}")
                    
                    # پاکسازی فایل موقت
                    try:
                        os.unlink(temp_filename)
                        logger.debug("Temporary audio file deleted successfully")
                    except Exception as cleanup_error:
                        logger.warning(f"Error deleting temporary file: {cleanup_error}")
                    
                    logger.info(f"Recognized text: '{text}'")
                    return text
                    
                except sr.WaitTimeoutError:
                    logger.warning("Listening timed out: no speech detected")
                except sr.UnknownValueError:
                    logger.warning("Speech was not understood")
                except sr.RequestError as e:
                    logger.error(f"Could not request results; {e}")
                except Exception as e:
                    logger.error(f"Error in OpenAI transcription: {e}")
                    logger.exception("Full traceback:")
        
        except Exception as e:
            logger.error(f"Error in speech recognition setup: {e}")
            logger.exception("Full traceback:")
        
        return None 