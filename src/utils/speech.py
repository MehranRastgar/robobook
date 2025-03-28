#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ماژول مدیریت گفتار (تبدیل متن به گفتار و گفتار به متن)
"""

import os
import logging
import tempfile
import threading
from typing import Optional, Callable, Any

# برای تبدیل متن به گفتار
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# برای تبدیل گفتار به متن
try:
    import speech_recognition as sr
except ImportError:
    sr = None

logger = logging.getLogger("SpeechHandler")

class SpeechHandler:
    """کلاس مدیریت تبدیل متن به گفتار و گفتار به متن"""
    
    def __init__(self, rate: int = 150, volume: float = 1.0, voice_id: Optional[str] = None, tts_type: str = "auto"):
        """
        راه‌اندازی سرویس گفتار
        
        Args:
            rate: سرعت گفتار (کلمه در دقیقه)
            volume: بلندی صدا (بین 0 تا 1)
            voice_id: شناسه صدا (اختیاری)
            tts_type: نوع موتور TTS ("pyttsx3", "gTTS", "espeak", "azure", "auto")
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.tts_type = tts_type.lower()
        self.engine = None
        self.recognizer = None
        self.tts_lock = threading.Lock()  # قفل برای جلوگیری از استفاده همزمان
        self.pyttsx3_busy = False  # وضعیت موتور pyttsx3
        self.gtts_language = "fa"  # زبان پیش‌فرض برای gTTS
        self.espeak_available = False  # وضعیت دسترسی به espeak
        self.azure_available = False  # وضعیت دسترسی به Azure TTS
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY", "")
        self.azure_service_region = os.getenv("AZURE_SERVICE_REGION", "eastus")
        
        # بررسی دسترسی به Azure
        if self.azure_speech_key:
            try:
                import azure.cognitiveservices.speech as speechsdk
                self.azure_available = True
                logger.info("Azure Speech SDK is available for Persian TTS")
            except ImportError:
                logger.info("Azure Speech SDK is not available")
        
        # بررسی دسترسی به espeak
        try:
            import espeakng
            self.espeak_available = True
            logger.info("espeak-ng is available for Persian TTS")
        except ImportError:
            logger.info("espeak-ng is not available")
        
        # راه‌اندازی موتور تبدیل متن به گفتار
        if self.tts_type == "auto":
            # امتحان کردن موتورهای مختلف
            if self.azure_available:
                logger.info("Using Azure Speech for TTS (best quality for Persian)")
                self.tts_type = "azure"
            elif self.espeak_available:
                logger.info("Using espeak for TTS (good for Persian)")
                self.tts_type = "espeak"
            elif pyttsx3 is not None:
                try:
                    self._setup_tts_engine()
                    if self.engine is not None:
                        logger.info("Using pyttsx3 for TTS")
                        self.tts_type = "pyttsx3"
                    else:
                        # امتحان کردن gTTS
                        try:
                            import gtts
                            logger.info("Using gTTS for TTS")
                            self.tts_type = "gtts"
                        except ImportError:
                            logger.warning("No TTS engine available")
                            self.tts_type = "none"
                except Exception as e:
                    logger.warning(f"pyttsx3 initialization failed: {e}")
                    try:
                        import gtts
                        logger.info("Using gTTS for TTS")
                        self.tts_type = "gtts"
                    except ImportError:
                        logger.warning("No TTS engine available")
                        self.tts_type = "none"
            else:
                # امتحان کردن gTTS
                try:
                    import gtts
                    logger.info("Using gTTS for TTS")
                    self.tts_type = "gtts"
                except ImportError:
                    logger.warning("No TTS engine available")
                    self.tts_type = "none"
        elif self.tts_type == "azure":
            if not self.azure_available:
                if self.azure_speech_key:
                    try:
                        import azure.cognitiveservices.speech as speechsdk
                        self.azure_available = True
                        logger.info("Azure Speech SDK initialized for TTS")
                    except ImportError:
                        logger.warning("Azure Speech SDK not available, falling back to other methods")
                        self.tts_type = "auto"
                        self.__init__(rate, volume, voice_id, "auto")
                        return
                else:
                    logger.warning("Azure Speech SDK requires AZURE_SPEECH_KEY, falling back to other methods")
                    self.tts_type = "auto"
                    self.__init__(rate, volume, voice_id, "auto")
                    return
        elif self.tts_type == "espeak":
            if not self.espeak_available:
                try:
                    import espeakng
                    self.espeak_available = True
                    logger.info("espeak-ng initialized for TTS")
                except ImportError:
                    logger.warning("espeak-ng module not available, falling back to other methods")
                    self.tts_type = "auto"
                    self.__init__(rate, volume, voice_id, "auto")
                    return
        elif self.tts_type == "pyttsx3" and pyttsx3 is not None:
            self._setup_tts_engine()
        elif self.tts_type == "gtts":
            try:
                import gtts
                logger.info("Using gTTS for TTS")
                # بررسی زبان پشتیبانی شده
                self._get_gtts_supported_language()
            except ImportError:
                logger.warning("gTTS module not available")
                self.tts_type = "none"
        
        # راه‌اندازی تشخیص گفتار
        if sr is not None:
            self.recognizer = sr.Recognizer()
        
        logger.info(f"Speech handler initialized with TTS type: {self.tts_type}")
    
    def _setup_tts_engine(self):
        """راه‌اندازی موتور تبدیل متن به گفتار"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # تنظیم صدا اگر مشخص شده باشد
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            else:
                # انتخاب صدا به صورت خودکار (اولویت با صدای فارسی)
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if "persian" in voice.name.lower() or "farsi" in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        logger.info(f"Persian voice selected: {voice.name}")
                        break
            
            logger.info("Text-to-speech engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize text-to-speech engine: {e}")
            self.engine = None
    
    def _reinitialize_pyttsx3_if_needed(self):
        """بازسازی موتور pyttsx3 در صورت نیاز"""
        if self.engine is None and pyttsx3 is not None:
            logger.info("Reinitializing pyttsx3 engine")
            self._setup_tts_engine()
            return True
        return False
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        تبدیل متن به گفتار و پخش آن
        
        Args:
            text: متنی که باید به گفتار تبدیل شود
            blocking: آیا اجرای برنامه تا پایان صحبت متوقف شود؟
            
        Returns:
            موفقیت در پخش صدا
        """
        if not text:
            logger.warning("Cannot speak: No text provided")
            return False
         
        # استفاده از قفل برای جلوگیری از استفاده همزمان
        with self.tts_lock:
            try:
                # اولویت با Azure برای زبان فارسی
                if self.tts_type == "azure" and self.azure_available:
                    return self._speak_azure(text, blocking)
                # اولویت با espeak برای زبان فارسی
                elif self.tts_type == "espeak" and self.espeak_available:
                    return self._speak_espeak(text, blocking)
                # اولویت با gTTS در صورت مشغول بودن pyttsx3
                elif self.pyttsx3_busy and self.tts_type == "pyttsx3":
                    try:
                        import gtts
                        logger.info("Switching to gTTS for this request as pyttsx3 is busy")
                        return self._speak_gtts(text)
                    except ImportError:
                        pass
                
                if self.tts_type == "pyttsx3" and self.engine is not None:
                    # بررسی مجدد وضعیت pyttsx3
                    if self.pyttsx3_busy:
                        logger.warning("pyttsx3 engine is busy, trying to reinitialize")
                        self._reinitialize_pyttsx3_if_needed()
                        if self.pyttsx3_busy:  # اگر هنوز مشغول است
                            return self._speak_gtts(text)  # استفاده از gTTS به جای آن
                    
                    return self._speak_pyttsx3(text, blocking)
                elif self.tts_type == "gtts":
                    return self._speak_gtts(text)
                else:
                    logger.warning("No TTS engine available")
                    return False
            except Exception as e:
                logger.error(f"Error in text-to-speech: {e}")
                # تلاش با gTTS در صورت شکست سایر روش‌ها
                try:
                    import gtts
                    logger.info("Falling back to gTTS after error")
                    return self._speak_gtts(text)
                except (ImportError, Exception) as gtts_error:
                    logger.error(f"gTTS fallback also failed: {gtts_error}")
                return False
    
    def _speak_pyttsx3(self, text: str, blocking: bool = True) -> bool:
        """استفاده از pyttsx3 برای تبدیل متن به گفتار"""
        try:
            self.pyttsx3_busy = True
            
            if blocking:
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # پخش در یک thread جداگانه برای اجرای غیر blocking
                def run_in_thread():
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Error in pyttsx3 thread: {e}")
                    finally:
                        self.pyttsx3_busy = False
                
                thread = threading.Thread(target=run_in_thread)
                thread.daemon = True
                thread.start()
            
            logger.debug(f"Speaking with pyttsx3: {text[:50]}...")
            
            if blocking:
                self.pyttsx3_busy = False
                
            return True
        except Exception as e:
            self.pyttsx3_busy = False
            logger.error(f"Error in pyttsx3 speech: {e}")
            return False
    
    def _get_gtts_supported_language(self):
        """یافتن زبان پشتیبانی شده در gTTS برای فارسی"""
        try:
            import gtts
            
            # لیست زبان‌های پیشنهادی برای استفاده
            suggested_langs = ["fa", "ar", "en"]
            
            # دریافت لیست زبان‌های پشتیبانی شده توسط gTTS
            try:
                supported_langs = gtts.lang.tts_langs()
                logger.info(f"Available gTTS languages: {', '.join(supported_langs.keys())}")
                
                # بررسی اینکه آیا زبان فارسی پشتیبانی می‌شود
                if 'fa' in supported_langs:
                    self.gtts_language = 'fa'
                    logger.info("Persian language 'fa' is supported by gTTS")
                    return 'fa'
                elif 'ar' in supported_langs:
                    self.gtts_language = 'ar'
                    logger.info("Arabic language 'ar' is used as Persian is not supported")
                    return 'ar'
                else:
                    self.gtts_language = 'en'
                    logger.info("English language 'en' is used as Persian and Arabic are not supported")
                    return 'en'
            except:
                # اگر نتوانستیم لیست زبان‌ها را دریافت کنیم، روش قبلی را امتحان می‌کنیم
                logger.warning("Could not get list of supported languages, trying languages one by one")
                
            # بررسی پشتیبانی از زبان‌ها
            for lang_code in suggested_langs:
                try:
                    # در نسخه‌های جدید gTTS، تست کردن مستقیم زبان
                    test_tts = gtts.gTTS(text="test", lang=lang_code)
                    # اگر به اینجا برسیم، یعنی زبان پشتیبانی می‌شود
                    self.gtts_language = lang_code
                    logger.info(f"Using language code '{lang_code}' for gTTS")
                    return lang_code
                except ValueError as e:
                    # اگر زبان پشتیبانی نشود، خطای ValueError می‌دهد
                    logger.warning(f"Language '{lang_code}' not supported by gTTS: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error testing language '{lang_code}': {e}")
                    continue
            
            # اگر هیچ‌کدام پشتیبانی نشد، از انگلیسی استفاده می‌کنیم
            self.gtts_language = "en"
            logger.warning("Falling back to English for gTTS")
            return "en"
        except ImportError:
            logger.warning("gTTS module not available")
            return "en"
    
    def list_gtts_languages(self):
        """دریافت لیست زبان‌های پشتیبانی شده توسط gTTS"""
        try:
            import gtts
            langs = gtts.lang.tts_langs()
            return langs
        except (ImportError, Exception) as e:
            logger.error(f"Error getting gTTS languages: {e}")
            return {}
    
    def _speak_gtts(self, text: str) -> bool:
        """استفاده از gTTS برای تبدیل متن به گفتار"""
        try:
            # نیاز به import در اینجا برای جلوگیری از خطا در صورت عدم وجود ماژول
            import gtts
            import os
            import tempfile
            
            # ایجاد یک فایل موقت برای ذخیره صدا
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            logger.debug(f"Converting text to speech with gTTS: {text[:50]}...")
            
            # بررسی زبان پشتیبانی شده اگر هنوز تنظیم نشده
            if not hasattr(self, 'gtts_language') or not self.gtts_language:
                self._get_gtts_supported_language()
            
            # تبدیل متن به گفتار و ذخیره در فایل
            try:
                tts = gtts.gTTS(text=text, lang=self.gtts_language, slow=False)
                tts.save(temp_filename)
                logger.debug(f"Created speech file using language: {self.gtts_language}")
            except ValueError as lang_error:
                if "Language not supported" in str(lang_error):
                    # دوباره زبان پشتیبانی شده را بررسی می‌کنیم
                    supported_lang = self._get_gtts_supported_language()
                    logger.warning(f"Retrying with language code: {supported_lang}")
                    tts = gtts.gTTS(text=text, lang=supported_lang, slow=False)
                    tts.save(temp_filename)
                else:
                    # در صورت سایر خطاها، از انگلیسی استفاده می‌کنیم
                    logger.warning(f"Falling back to English due to error: {lang_error}")
                    tts = gtts.gTTS(text=text, lang="en", slow=False)
                    tts.save(temp_filename)
            
            try:
                # تلاش برای استفاده از pygame
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                
                # منتظر اتمام پخش
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                pygame.mixer.quit()
            except ImportError:
                # در صورت عدم وجود pygame، از playsound استفاده می‌کنیم
                try:
                    from playsound import playsound
                    playsound(temp_filename)
                except ImportError:
                    # در صورت عدم وجود playsound، از os برای اجرای برنامه پخش استفاده می‌کنیم
                    if os.name == 'nt':  # ویندوز
                        os.system(f'start {temp_filename}')
                    elif os.name == 'posix':  # لینوکس/مک
                        os.system(f'afplay {temp_filename}' if os.uname().sysname == 'Darwin' else f'mpg123 {temp_filename}')
            
            # تلاش برای پاکسازی فایل موقت
            try:
                os.unlink(temp_filename)
            except Exception as cleanup_error:
                logger.warning(f"Failed to remove temporary audio file: {cleanup_error}")
            
            logger.debug(f"Successfully played speech with gTTS: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error in gTTS speech: {e}")
            return False
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        گوش دادن به صدای کاربر و تبدیل آن به متن
        
        Args:
            timeout: مدت زمان انتظار برای شروع صحبت (ثانیه)
            phrase_time_limit: حداکثر مدت زمان گوش دادن به یک جمله (ثانیه)
            
        Returns:
            متن تشخیص داده شده یا None در صورت خطا
        """
        if self.recognizer is None:
            logger.warning("Speech recognition is not available")
            return None
        
        # استفاده از میکروفون برای ضبط صدا
        try:
            with sr.Microphone() as source:
                logger.info("Listening for speech...")
                # تنظیم برای کاهش نویز محیط
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                    logger.info("Audio captured, recognizing...")
                    
                    # تلاش برای تشخیص با استفاده از موتور گوگل (می‌توان تنظیم کرد)
                    text = self.recognizer.recognize_google(audio, language="fa-IR")
                    logger.info(f"Recognized: {text}")
                    return text
                except sr.WaitTimeoutError:
                    logger.warning("Listening timed out: no speech detected")
                except sr.UnknownValueError:
                    logger.warning("Speech was not understood")
                except sr.RequestError as e:
                    logger.error(f"Could not request results; {e}")
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
        
        return None
    
    def save_to_file(self, text: str, filename: str) -> bool:
        """
        ذخیره گفتار در یک فایل صوتی
        
        Args:
            text: متنی که باید به گفتار تبدیل شود
            filename: نام فایل برای ذخیره (با پسوند)
            
        Returns:
            موفقیت در ذخیره فایل
        """
        if not text or self.engine is None:
            logger.warning("Cannot save speech to file: engine not available or no text")
            return False
        
        try:
            # موقتاً صدا را خاموش می‌کنیم
            original_volume = self.engine.getProperty('volume')
            self.engine.setProperty('volume', 0.0)
            
            # ذخیره در فایل
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            
            # بازگرداندن صدا به حالت اولیه
            self.engine.setProperty('volume', original_volume)
            
            logger.info(f"Speech saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving speech to file: {e}")
            return False
    
    def get_available_voices(self):
        """دریافت لیست صداهای موجود"""
        if self.engine is None:
            logger.warning("TTS engine not available")
            return []
        
        voices = self.engine.getProperty('voices')
        voice_list = []
        
        for voice in voices:
            voice_info = {
                'id': voice.id,
                'name': voice.name,
                'languages': voice.languages,
                'gender': voice.gender
            }
            voice_list.append(voice_info)
        
        return voice_list
    
    def _speak_espeak(self, text: str, blocking: bool = True) -> bool:
        """استفاده از espeak برای تبدیل متن به گفتار فارسی"""
        try:
            import espeakng
            
            # ایجاد یک فایل موقت برای ذخیره صدا
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_filename = temp_file.name
            
            # تنظیم espeak برای زبان فارسی
            speaker = espeakng.Speaker()
            speaker.voice = 'fa'  # زبان فارسی
            speaker.pitch = 50  # تنظیم زیر و بمی صدا (0-100)
            speaker.wpm = self.rate  # سرعت گفتار
            
            logger.debug(f"Speaking with espeak (Persian): {text[:50]}...")
            
            if blocking:
                # گفتار مستقیم
                speaker.say(text)
            else:
                # ذخیره در فایل و پخش در پس‌زمینه
                speaker.wavfile(text, temp_filename)
                
                def play_audio():
                    try:
                        # پخش فایل با استفاده از pygame
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(temp_filename)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(10)
                        pygame.mixer.quit()
                        # پاکسازی فایل
                        os.unlink(temp_filename)
                    except Exception as e:
                        logger.error(f"Error playing espeak audio: {e}")
                
                thread = threading.Thread(target=play_audio)
                thread.daemon = True
                thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error in espeak speech: {e}")
            return False
    
    def _speak_azure(self, text: str, blocking: bool = True) -> bool:
        """استفاده از Azure Speech Services برای تبدیل متن فارسی به گفتار"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # ایجاد یک فایل موقت برای ذخیره صدا اگر non-blocking باشد
            if not blocking:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_filename = temp_file.name
            
            # تنظیم پیکربندی Azure Speech
            speech_config = speechsdk.SpeechConfig(subscription=self.azure_speech_key, region=self.azure_service_region)
            speech_config.speech_synthesis_voice_name = "fa-IR-DilaraNeural"  # صدای فارسی زن
            # یا استفاده از صدای مرد: "fa-IR-FaridNeural"
            
            # تنظیم خروجی صدا
            if blocking:
                # پخش مستقیم
                audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                
                logger.debug(f"Speaking with Azure TTS (Persian): {text[:50]}...")
                result = synthesizer.speak_text_async(text).get()
                
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                    logger.error(f"Error details: {cancellation_details.error_details}")
                    return False
            else:
                # ذخیره در فایل و پخش در پس‌زمینه
                audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_filename)
                synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                
                result = synthesizer.speak_text_async(text).get()
                
                if result.reason == speechsdk.ResultReason.Canceled:
                    logger.error(f"Speech synthesis canceled: {result.cancellation_details.reason}")
                    return False
                
                # پخش فایل در پس‌زمینه
                def play_audio():
                    try:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(temp_filename)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            pygame.time.Clock().tick(10)
                        pygame.mixer.quit()
                        # پاکسازی فایل
                        os.unlink(temp_filename)
                    except Exception as e:
                        logger.error(f"Error playing Azure audio: {e}")
                
                thread = threading.Thread(target=play_audio)
                thread.daemon = True
                thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Error in Azure speech: {e}")
            return False 