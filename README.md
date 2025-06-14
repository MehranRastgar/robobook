# روبوبوک (RoboBook)

روبات هوشمند مشاور کتابفروشی با قابلیت تعامل صوتی و راهنمایی مشتریان

## ویژگی‌ها
- مشاوره خرید کتاب به مشتریان
- دسترسی به پایگاه داده موجودی کتاب‌ها
- راهنمایی مکان کتاب‌ها در قفسه‌ها
- تعامل با مشتری از طریق گفتگو

## تکنولوژی‌ها
- **مدل زبانی**: Llama (نسخه اولیه) و API LMStudio محلی
- **بعدها**: API OpenAI
- **سخت‌افزار آینده**: NVIDIA Jetson یا Orange Pi 5 با Rockchip NPU
- **کنترل حرکتی**: STM32 و IMU
- **تعامل پیشرفته**: سیستم بینایی کامپیوتری با دوربین

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.8+
- LMStudio (نسخه محلی)

### نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### اجرا
```bash
python src/main.py
```

## ساختار پروژه
- `src/`: کدهای اصلی پروژه
- `data/`: پایگاه داده کتاب‌ها
- `utils/`: ابزارهای کمکی
- `models/`: مدل‌های زبانی
- `tests/`: تست‌ها 






