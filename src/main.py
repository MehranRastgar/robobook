#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RoboBook - روبات هوشمند مشاور کتابفروشی
"""

import os
import sys
import argparse
import logging
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv

# تنظیم مسیر برای import‌های نسبی
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.llm_service import LLMService
from src.db.database import BookDatabase
from src.utils.speech import SpeechHandler
from src.utils.config import AppConfig

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('robobook.log', encoding='utf-8')
    ]
)

# تنظیم encoding برای stdout
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

logger = logging.getLogger("RoboBook")

# بارگذاری تنظیمات از فایل .env
load_dotenv()

app = Flask(__name__)

def initialize_services():
    """راه‌اندازی سرویس‌های اصلی برنامه"""
    config = AppConfig()
    db = BookDatabase(config.db_path)
    llm = LLMService(model_type=config.model_type, api_key=config.api_key)
    
    # اضافه کردن پشتیبانی از TTS آنلاین
    tts_settings = config.get_tts_settings()
    tts_type = tts_settings['tts_type']
    logger.info(f"Initializing speech handler with TTS type: {tts_type}")
    
    # تنظیم environment variable برای OpenAI اگر تنظیم نشده باشد
    if config.openai_api_key and os.environ.get('OPENAI_API_KEY') is None:
        os.environ['OPENAI_API_KEY'] = config.openai_api_key
        logger.info("Set OPENAI_API_KEY from config")
    
    speech = SpeechHandler(
        rate=config.speech_rate,
        volume=config.speech_volume,
        tts_type=tts_type,

    )
    
    # تنظیم زبان gTTS اگر از قبل تنظیم نشده باشد
    if hasattr(speech, 'gtts_language') and not speech.gtts_language:
        speech.gtts_language = "fa"  # تنظیم زبان فارسی برای gTTS
        logger.info(f"Set gTTS language to: fa (Persian)")
    
    return config, db, llm, speech

@app.route('/')
def index():
    """صفحه اصلی وب اپلیکیشن"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """پردازش درخواست کاربر از طریق API"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # جستجو در پایگاه داده کتاب‌ها
    book_results = db.search_books(query)
    
    # پردازش پرسش با مدل زبانی
    llm_response = llm.process_query(query, book_results)
    
    response = jsonify({
        "response": llm_response,
        "books": book_results
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/api/speak', methods=['POST'])
def text_to_speech():
    """تبدیل متن به گفتار"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    speech.speak(text)
    return jsonify({"status": "success"})

@app.route('/api/tts_file', methods=['POST'])
def text_to_speech_file():
    """تبدیل متن به گفتار و ارسال فایل صوتی"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        # ایجاد یک فایل موقت برای ذخیره صدا
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
        
        # انتخاب روش تبدیل متن به گفتار
        success = False
        
        # تلاش با OpenAI TTS برای زبان فارسی (اولویت اول)
        if hasattr(speech, 'openai_available') and speech.openai_available:
            try:
                from openai import OpenAI
                from src.utils.openai_tts import OpenAITTS
                logger.info("Creating TTS file with OpenAI (Persian)")
                
                # تغییر پسوند به mp3 برای OpenAI
                mp3_filename = temp_filename
                
                # استفاده از کلاینت OpenAI
                openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
                # ساخت خروجی صوتی با زبان فارسی
                response = openai_client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="nova",  # صدای قابل تنظیم
                    input=text,
                    response_format="mp3",
                    speed=1.0
                )
                
                # ذخیره سازی خروجی
                response.stream_to_file(mp3_filename)
                success = True
                logger.info("Successfully created TTS file with OpenAI")
            except Exception as e:
                logger.error(f"Error using OpenAI TTS: {e}")
        
        # # تلاش با Azure TTS برای زبان فارسی (اولویت دوم)
        # if not success and hasattr(speech, 'azure_available') and speech.azure_available:
        #     try:
        #         import azure.cognitiveservices.speech as speechsdk
        #         logger.info("Creating TTS file with Azure (Persian)")
                
        #         # تغییر پسوند به wav برای Azure
        #         wav_filename = temp_filename.replace('.mp3', '.wav')
                
        #         # تنظیم پیکربندی Azure Speech
        #         speech_config = speechsdk.SpeechConfig(subscription=speech.azure_speech_key, region=speech.azure_service_region)
        #         speech_config.speech_synthesis_voice_name = "fa-IR-DilaraNeural"  # صدای فارسی زن
                
        #         # تنظیم خروجی صدا
        #         audio_config = speechsdk.audio.AudioOutputConfig(filename=wav_filename)
        #         synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
                
        #         result = synthesizer.speak_text_async(text).get()
                
        #         if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #             temp_filename = wav_filename
        #             success = True
        #             logger.info("Successfully created TTS file with Azure")
        #         else:
        #             logger.warning(f"Azure TTS failed with status: {result.reason}")
        #     except Exception as e:
        #         logger.error(f"Error using Azure TTS: {e}")
        
        # # تلاش با espeak برای زبان فارسی
        # if not success and hasattr(speech, 'espeak_available') and speech.espeak_available:
        #     try:
        #         import espeakng
        #         logger.info("Creating TTS file with espeak (Persian)")
                
        #         # تغییر پسوند به wav برای espeak
        #         wav_filename = temp_filename.replace('.mp3', '.wav')
                
        #         # تنظیم espeak برای زبان فارسی
        #         speaker = espeakng.Speaker()
        #         speaker.voice = 'fa'
        #         speaker.pitch = 50
        #         speaker.wpm = speech.rate
                
        #         # ذخیره در فایل wav
        #         speaker.wavfile(text, wav_filename)
                
        #         # اگر تبدیل مستقیم ممکن نباشد، همان فایل wav را استفاده می‌کنیم
        #         temp_filename = wav_filename
        #         success = True
        #         logger.info("Successfully created TTS file with espeak")
            except Exception as e:
                logger.error(f"Error using espeak: {e}")
        
        # # تلاش با gTTS اگر روش‌های دیگر موفق نبودند
        # if not success:
        #     try:
        #         import gtts
                
        #         # اطمینان از اینکه زبان پشتیبانی می‌شود
        #         lang_to_use = speech.gtts_language if hasattr(speech, 'gtts_language') and speech.gtts_language else "en"
        #         logger.info(f"Creating TTS file with language: {lang_to_use}")
                
        #         # استفاده از gTTS
        #         tts = gtts.gTTS(text=text, lang=lang_to_use, slow=False)
        #         tts.save(temp_filename)
        #         success = True
        #         logger.info("Successfully created TTS file with gTTS")
        #     except Exception as e:
        #         logger.error(f"Error using gTTS: {e}")
        #         try:
        #             # استفاده از زبان انگلیسی در صورت خطا
        #             logger.info("Retrying with English language")
        #             tts = gtts.gTTS(text=text, lang="en", slow=False)
        #             tts.save(temp_filename)
        #             success = True
        #             logger.info("Successfully created TTS file with English")
        #         except Exception as e2:
        #             logger.error(f"Error using gTTS with English: {e2}")
        #             # در صورت خطا، تلاش برای استفاده از pyttsx3
        #             if hasattr(speech, 'engine') and speech.engine is not None:
        #                 logger.info("Falling back to pyttsx3")
        #                 success = speech.save_to_file(text, temp_filename)
        
        if not success:
            return jsonify({"error": "Failed to generate speech file"}), 500
        
        # ارسال فایل صوتی با تشخیص نوع MIME مناسب
        mimetype = 'audio/wav' if temp_filename.endswith('.wav') else 'audio/mpeg'
        download_name = 'speech.wav' if temp_filename.endswith('.wav') else 'speech.mp3'
        
        # ارسال فایل صوتی
        logger.info(f"Sending speech file: {temp_filename}")
        return send_file(temp_filename, mimetype=mimetype, as_attachment=True, 
                        download_name=download_name, 
                        max_age=0)
    
    except Exception as e:
        logger.error(f"Error generating speech file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/listen', methods=['POST'])
def speech_to_text():
    """دریافت صدا و تبدیل به متن"""
    try:
        # دریافت پارامترها
        data = request.json or {}
        timeout = data.get('timeout', 5)  # زمان انتظار به ثانیه
        phrase_time_limit = data.get('phrase_time_limit', 10)  # حداکثر زمان ضبط به ثانیه
        
        # شروع ضبط و تشخیص گفتار
        text = speech.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)
        
        if text:
            logger.info(f"Recognized speech: {text}")
            
            # جستجوی کتاب‌ها بر اساس متن تشخیص داده شده
            book_results = db.search_books(text)
            
            # دریافت پاسخ از مدل زبانی
            llm_response = llm.process_query(text, book_results)
            
            # ارسال پاسخ صوتی اگر درخواست شده باشد
            auto_speak = data.get('auto_speak', False)
            if auto_speak:
                speech.speak(llm_response, blocking=False)
            
            response = jsonify({
                "status": "success",
                "text": text,
                "response": llm_response,
                "books": book_results
            })
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        else:
            response = jsonify({
                "status": "error",
                "error": "Could not recognize speech"
            }), 400
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
            
    except Exception as e:
        logger.error(f"Error in speech recognition: {e}")
        response = jsonify({
            "status": "error",
            "error": str(e)
        }), 500
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

@app.route('/api/listen_and_respond', methods=['GET'])
def listen_and_respond():
    """گوش دادن به صدا، تبدیل به متن، پاسخگویی و تبدیل پاسخ به گفتار"""
    try:
        # گوش دادن و تشخیص گفتار
        text = speech.listen()
        
        if not text:
            speech.speak("متأسفانه نتوانستم صدای شما را تشخیص دهم. لطفاً دوباره تلاش کنید.")
            return jsonify({
                "status": "error",
                "error": "Could not recognize speech"
            }), 400
        
        # جستجوی کتاب‌ها
        book_results = db.search_books(text)
        
        # دریافت پاسخ
        response = llm.process_query(text, book_results)
        
        # تبدیل پاسخ به گفتار
        speech.speak(response)
        
        return jsonify({
            "status": "success",
            "query": text,
            "response": response,
            "books": book_results
        })
        
    except Exception as e:
        logger.error(f"Error in voice conversation: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

def interactive_mode():
    """حالت تعاملی برنامه از طریق خط فرمان"""
    print("=== روبوبوک - مشاور هوشمند کتابفروشی ===")
    print("برای خروج 'exit' را وارد کنید.")
    
    while True:
        query = input("\nسوال خود را بپرسید: ")
        
        if query.lower() == 'exit':
            print("خداحافظ!")
            break
        
        # جستجو در پایگاه داده کتاب‌ها
        book_results = db.search_books(query)
        
        # پردازش پرسش با مدل زبانی
        response = llm.process_query(query, book_results)
        
        print(f"\nپاسخ: {response}")
        
        if book_results:
            print("\nکتاب‌های پیشنهادی:")
            for i, book in enumerate(book_results, 1):
                print(f"{i}. {book['title']} - {book['author']} - قفسه: {book['shelf_location']}")

def test_speech():
    """تست عملکرد گفتار"""
    try:
        # ایجاد نمونه از SpeechHandler
        speech = SpeechHandler(tts_type="openai")
        
        # تست تبدیل متن به گفتار
        print("تست تبدیل متن به گفتار...")
        speech.speak("سلام، من یک ربات کتابفروشی هستم")
        
        # تست تبدیل گفتار به متن
        print("تست تبدیل گفتار به متن...")
        print("لطفاً به فارسی صحبت کنید...")
        text = speech.listen()
        if text:
            print(f"متن تشخیص داده شده: {text}")
        else:
            print("هیچ متنی تشخیص داده نشد")
            
    except Exception as e:
        print(f"خطا در تست گفتار: {e}")

def main():
    """تابع اصلی برنامه"""
    parser = argparse.ArgumentParser(description='روبوبوک - مشاور هوشمند کتابفروشی')
    parser.add_argument('--server', action='store_true', help='اجرای برنامه در حالت سرور وب')
    parser.add_argument('--test', action='store_true', help='اجرای تست گفتار')
    parser.add_argument('--port', type=int, default=5000, help='پورت سرور وب')
    parser.add_argument('--debug', action='store_true', help='اجرا در حالت دیباگ')
    
    args = parser.parse_args()
    
    global config, db, llm, speech
    config, db, llm, speech = initialize_services()
    
    if args.test:
        test_speech()
    elif args.server:
        # اجرا در حالت سرور وب
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
    else:
        # اجرا در حالت تعاملی
        interactive_mode()

if __name__ == "__main__":
    main() 