# راهنمای استفاده از تبدیل متن به گفتار فارسی در روبوبوک

## گزینه‌های تبدیل متن به گفتار فارسی

روبوبوک از چند روش برای تبدیل متن فارسی به گفتار پشتیبانی می‌کند:

1. **OpenAI TTS**: بهترین کیفیت برای زبان فارسی، نیازمند اینترنت و کلید API
2. **espeak-ng**: گزینه خوب برای زبان فارسی، پشتیبانی محلی (بدون نیاز به اینترنت)
3. **gTTS**: کیفیت نسبتاً خوب اما نیازمند اینترنت، پشتیبانی محدود از فارسی
4. **pyttsx3**: پشتیبانی از فارسی بستگی به سیستم عامل دارد

## تنظیم OpenAI TTS برای زبان فارسی

برای استفاده از OpenAI TTS که بهترین کیفیت را برای متن فارسی ارائه می‌دهد:

1. **دریافت کلید API از OpenAI**:
   - در [وبسایت OpenAI](https://platform.openai.com/) ثبت‌نام کنید
   - یک کلید API در بخش API Keys ایجاد کنید

2. **تنظیم کلید API در فایل `.env`**:
   ```
   # OpenAI API Settings
   OPENAI_API_KEY=sk-your-api-key-here
   
   # Text-to-Speech Settings
   TTS_TYPE=openai
   
   # OpenAI TTS Settings
   OPENAI_TTS_MODEL=tts-1
   OPENAI_TTS_VOICE=alloy
   OPENAI_TTS_SPEED=1.0
   ```

3. **صداهای مختلف OpenAI**:
   - `alloy`: صدای خنثی (پیش‌فرض)
   - `echo`: صدای زیر
   - `fable`: صدای گرم و دوستانه
   - `onyx`: صدای عمیق و قدرتمند
   - `nova`: صدای نرم و متعادل
   - `shimmer`: صدای روشن و درخشان

## نصب espeak-ng برای زبان فارسی

### 1. نصب espeak-ng روی سیستم عامل

**در ویندوز:**
- [دانلود espeak-ng از اینجا](https://github.com/espeak-ng/espeak-ng/releases)
- نصب برنامه
- اطمینان از نصب صداهای فارسی (معمولاً به صورت پیش‌فرض نصب می‌شوند)

**در لینوکس:**
```bash
sudo apt-get install espeak-ng
```

**در macOS:**
```bash
brew install espeak-ng
```

### 2. نصب کتابخانه Python برای espeak

```bash
pip install py-espeak-ng
```

## پیکربندی روبوبوک برای استفاده از espeak

در فایل `.env` می‌توانید تنظیمات گفتار را تغییر دهید:

```
# تنظیمات گفتار
SPEECH_RATE=150
SPEECH_VOLUME=1.0
# نوع موتور TTS: "pyttsx3", "gtts", "espeak", "openai", "auto"
TTS_TYPE=espeak
```

## تنظیمات صدای فارسی در espeak

در صورت نیاز به تنظیم بیشتر صدای فارسی، می‌توانید پارامترهای زیر را در فایل `src/utils/speech.py` در متد `_speak_espeak` تغییر دهید:

```python
speaker = espeakng.Speaker()
speaker.voice = 'fa'        # زبان فارسی
speaker.pitch = 50          # زیر و بمی صدا (0-100)
speaker.wpm = self.rate     # سرعت گفتار
```

## عیب‌یابی مشکلات espeak

1. **خطای "No such voice: fa"**:
   - اطمینان حاصل کنید که صداهای فارسی در espeak-ng نصب شده‌اند
   - دستور `espeak-ng --voices` را در خط فرمان اجرا کنید تا صداهای موجود را ببینید
   - اگر فارسی در لیست نبود، مجدداً espeak-ng را با پشتیبانی از زبان‌های بیشتر نصب کنید

2. **کیفیت پایین صدای فارسی**:
   - تنظیمات pitch و speed را در کد تغییر دهید
   - از نسخه‌های جدیدتر espeak-ng استفاده کنید که کیفیت بهتری دارند

3. **خطای "No module named 'espeakng'"**:
   - مطمئن شوید که کتابخانه py-espeak-ng را نصب کرده‌اید:
   ```bash
   pip install py-espeak-ng
   ```
   - مطمئن شوید که espeak-ng روی سیستم شما نصب شده است

## گزینه‌های جایگزین برای متن به گفتار فارسی

اگر OpenAI TTS یا espeak-ng برای شما مناسب نیست، می‌توانید از گزینه‌های دیگر استفاده کنید:

1. **Mozilla TTS**: کیفیت بالا، نیاز به منابع بیشتر
   ```bash
   pip install TTS
   ```

2. **Pyfarsitts**: کتابخانه مخصوص زبان فارسی
   ```bash
   pip install pyfarsitts
   ```

3. **Azure Speech Service**: سرویس تجاری مایکروسافت با کیفیت خوب
   ```bash
   pip install azure-cognitiveservices-speech
   ``` 
