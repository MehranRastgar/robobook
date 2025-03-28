# راهنمای استفاده از Azure Speech Services برای گفتار فارسی

## مزایای استفاده از Azure Speech Services

سرویس Azure Speech برای تبدیل متن فارسی به گفتار مزایای زیر را دارد:

1. **کیفیت بسیار بالای صدا**: صدای طبیعی و واقعی مشابه انسان
2. **پشتیبانی عالی از زبان فارسی**: تلفظ صحیح کلمات فارسی
3. **تنوع صدا**: صداهای مرد و زن برای زبان فارسی
4. **قابلیت تنظیم**: کنترل سرعت، تن صدا و سایر ویژگی‌ها

## نحوه دریافت کلید Azure

برای استفاده از Azure Speech Services، نیاز به یک حساب کاربری Azure و کلید API دارید:

1. وارد [پرتال Azure](https://portal.azure.com) شوید
2. یک سرویس Cognitive Services یا Speech Service جدید ایجاد کنید
3. سطح قیمت‌گذاری Free F0 را انتخاب کنید (رایگان با محدودیت ماهانه)
4. پس از ایجاد سرویس، به بخش Key and Endpoint بروید
5. یکی از کلیدها (KEY 1 یا KEY 2) و منطقه (Region) را کپی کنید

## تنظیم روبوبوک برای استفاده از Azure

1. کلید و منطقه دریافت شده را در فایل `.env` قرار دهید:

```
# تنظیمات Azure Speech Services
AZURE_SPEECH_KEY=your_subscription_key_here
AZURE_SERVICE_REGION=eastus
```

2. نوع TTS را به `azure` تغییر دهید:

```
TTS_TYPE=azure
```

3. کتابخانه Azure را نصب کنید:

```bash
pip install azure-cognitiveservices-speech
```

## خطایابی مشکلات Azure TTS

1. **خطای "Unauthorized"**:
   - بررسی کنید که کلید API صحیح و معتبر باشد
   - بررسی کنید که منطقه (region) به درستی تنظیم شده باشد

2. **خطای "No subscription key provided"**:
   - اطمینان حاصل کنید که مقدار AZURE_SPEECH_KEY در فایل .env به درستی تنظیم شده است

3. **خطای "Connection error"**:
   - بررسی کنید که اتصال اینترنت برقرار باشد
   - بررسی کنید که فایروال یا پروکسی مانع اتصال به سرورهای Azure نباشد

## تنظیمات پیشرفته

برای تنظیمات پیشرفته‌تر می‌توانید کد را در `src/utils/speech.py` تغییر دهید:

1. **تغییر صدای فارسی**:
   - `fa-IR-DilaraNeural`: صدای زن فارسی (پیش‌فرض)
   - `fa-IR-FaridNeural`: صدای مرد فارسی

2. **تنظیم سرعت و تن صدا**:
   ```python
   speech_config.speech_synthesis_voice_name = "fa-IR-DilaraNeural"
   # تنظیم سرعت گفتار (0.5 تا 2.0، پیش‌فرض 1.0)
   speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
   speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_SynthRate, "0")  # -10 تا +10
   ```

## محدودیت‌های سرویس رایگان Azure

سرویس رایگان Azure (F0) محدودیت‌هایی دارد:
- حداکثر 500,000 کاراکتر در ماه
- حداکثر 20 درخواست در ثانیه

برای استفاده بیشتر، باید به سطح پولی (S0) ارتقا دهید. 