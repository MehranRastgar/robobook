# راهنمای استفاده از قابلیت‌های صوتی روبوبوک

## پیش‌نیازها

برای استفاده از قابلیت‌های صوتی (تبدیل گفتار به متن و متن به گفتار) نیاز به نصب کتابخانه‌های زیر دارید:

1. **PyAudio**: برای ضبط صدا از میکروفون
2. **SpeechRecognition**: برای تشخیص گفتار
3. **pyttsx3** یا **gTTS**: برای تبدیل متن به گفتار
4. **pygame** یا **playsound**: برای پخش صدا (مورد نیاز gTTS)

## نصب

نصب از طریق pip:

```bash
pip install pyaudio speechrecognition pyttsx3 gtts pygame playsound
```

### نصب PyAudio در ویندوز

در صورت بروز مشکل در نصب PyAudio در ویندوز، می‌توانید از روش‌های زیر استفاده کنید:

1. **نصب با pipwin**:
```bash
pip install pipwin
pipwin install pyaudio
```

2. **نصب مستقیم از فایل wheel**:
   - به [این صفحه](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) بروید
   - فایل مناسب با نسخه پایتون و معماری سیستم خود را دانلود کنید
   - با دستور زیر نصب کنید:
   ```bash
   pip install path\to\downloaded\PyAudio‑X.X.X‑cpXX‑cpXXm‑win_amd64.whl
   ```

3. **نصب با Conda**:
```bash
conda install pyaudio
```

## موتورهای تبدیل متن به گفتار

روبوبوک از دو موتور تبدیل متن به گفتار پشتیبانی می‌کند:

1. **pyttsx3**: موتور محلی و آفلاین که سریع‌تر است، اما کیفیت پایین‌تری دارد
2. **gTTS**: موتور آنلاین Google که کیفیت بالایی دارد، اما نیاز به اتصال اینترنت دارد

در صورت مشغول بودن یا بروز مشکل در یک موتور، سیستم به طور خودکار به موتور دیگر سوئیچ می‌کند.

برای انتخاب موتور مورد نظر، می‌توانید فایل `.env` را ویرایش کنید:

```
TTS_TYPE=auto    # انتخاب خودکار (ابتدا pyttsx3، سپس gTTS)
TTS_TYPE=pyttsx3  # استفاده از pyttsx3
TTS_TYPE=gtts    # استفاده از gTTS
```

### پخش صدا با gTTS

برای پخش صدای تولید شده توسط gTTS، سیستم از یکی از روش‌های زیر استفاده می‌کند:

1. **pygame**: کتابخانه اصلی برای پخش صدا
2. **playsound**: کتابخانه ساده‌تر برای پخش صدا (به عنوان جایگزین)
3. **پخش‌کننده سیستم‌عامل**: در صورت عدم وجود pygame و playsound، از پخش‌کننده پیش‌فرض سیستم‌عامل استفاده می‌شود

### عیب‌یابی موتورهای TTS

1. **pyttsx3 کار نمی‌کند**:
   - اطمینان حاصل کنید که صدای سیستم عامل به درستی تنظیم شده باشد
   - در ویندوز، اطمینان حاصل کنید که موتور SAPI5 نصب شده باشد
   - خطای "run loop already started": این خطا به صورت خودکار مدیریت می‌شود و سیستم به موتور gTTS سوئیچ می‌کند

2. **gTTS کار نمی‌کند**:
   - بررسی کنید که اتصال اینترنت برقرار باشد
   - محدودیت‌های فایروال را بررسی کنید
   - اگر خطای pygame دریافت می‌کنید، سیستم به صورت خودکار از playsound یا پخش‌کننده سیستم‌عامل استفاده می‌کند

## استفاده از API‌های صوتی

### 1. تبدیل متن به گفتار

برای تبدیل متن به گفتار، یک درخواست POST به آدرس زیر ارسال کنید:

```
POST /api/speak
Content-Type: application/json

{
  "text": "متنی که می‌خواهید به گفتار تبدیل شود"
}
```

### 2. تبدیل گفتار به متن

برای تبدیل گفتار به متن، یک درخواست POST به آدرس زیر ارسال کنید:

```
POST /api/listen
Content-Type: application/json

{
  "timeout": 5,
  "phrase_time_limit": 10,
  "auto_speak": true
}
```

پارامترها:
- `timeout`: زمان انتظار برای شروع صحبت (ثانیه)
- `phrase_time_limit`: حداکثر زمان ضبط (ثانیه)
- `auto_speak`: اگر true باشد، پاسخ به صورت خودکار به گفتار تبدیل می‌شود

### 3. گفتگوی کامل صوتی

برای شروع یک گفتگوی صوتی کامل، یک درخواست GET به آدرس زیر ارسال کنید:

```
GET /api/listen_and_respond
```

این API گوش می‌دهد، گفتار را تشخیص می‌دهد، پاسخ را تولید می‌کند و آن را به گفتار تبدیل می‌کند.

## استفاده از رابط وب

برای استفاده از رابط وب، برنامه را در حالت سرور اجرا کنید:

```bash
python src/main.py --server
```

سپس به آدرس زیر در مرورگر خود بروید:

```
http://localhost:5000/
```

در این رابط می‌توانید:
- پرسش‌های خود را تایپ کنید
- دکمه "ضبط صدا" را برای استفاده از تشخیص گفتار فشار دهید
- دکمه "گفتگوی صوتی" را برای تعامل کامل صوتی استفاده کنید

## عیب‌یابی مشکلات صوتی

1. **میکروفون کار نمی‌کند**:
   - مطمئن شوید مرورگر اجازه دسترسی به میکروفون را دارد
   - بررسی کنید که میکروفون سیستم فعال و به درستی تنظیم شده باشد

2. **صدا پخش نمی‌شود**:
   - بررسی کنید که بلندگوها یا هدفون به درستی متصل و فعال باشند
   - اطمینان حاصل کنید که صدای سیستم قطع نباشد
   
3. **خطای تشخیص گفتار**:
   - در محیطی با نویز کمتر آزمایش کنید
   - آهسته‌تر و واضح‌تر صحبت کنید
   - بررسی کنید که اتصال اینترنت برقرار باشد (برای تشخیص گفتار آنلاین)

4. **خطای "No module named 'pyaudio'"**:
   - به بخش نصب مراجعه کرده و PyAudio را با روش‌های ذکر شده نصب کنید

## استفاده در محیط سخت‌افزاری روبات

برای استفاده از این قابلیت‌ها در یک روبات فیزیکی، می‌توانید:

1. **میکروفون‌های بهتر**: از میکروفون‌های با کیفیت بالاتر و با قابلیت حذف نویز استفاده کنید
2. **بلندگوهای مناسب محیط**: بلندگوهایی با کیفیت مناسب برای محیط کتابفروشی انتخاب کنید
3. **پردازش آفلاین**: برای محیط‌هایی با اتصال اینترنت محدود، از موتورهای تشخیص گفتار آفلاین مانند Vosk یا CMU Sphinx استفاده کنید
4. **کنترل صدا**: اضافه کردن کنترل بلندی صدا براساس نویز محیط 