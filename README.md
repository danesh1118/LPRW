<p align="center">
  <img src="https://img.shields.io/badge/LPRW-Leviko%20Panel%20Railway%20V1.0.0-6366f1?style=for-the-badge" alt="LPRW"/>
</p>

<p align="center">
  <strong>LPRW</strong> — پنل پروکسی اختصاصی برای استقرار روی Railway<br/>
  VLESS · Trojan · Subscription · User Portal · Real-time Stats
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-Async-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Railway-Ready-0B0D0E?style=flat-square&logo=railway&logoColor=white" alt="Railway"/>
  <img src="https://img.shields.io/badge/License-Private-red?style=flat-square" alt="License"/>
</p>

---

## معرفی

**LPRW (Leviko Panel Railway)** یک پنل مدیریت تونل سبک و کامل است که برای دیپلوی سریع روی [Railway](https://railway.app) طراحی شده.

بدون نیاز به سرور اختصاصی، بدون کانفیگ پیچیدهٔ nginx — فقط ریپو را به Railway وصل کنید و دامنه بگیرید.

| قابلیت | توضیح |
|--------|--------|
| پروتکل‌ها | **VLESS-WS** و **Trojan-WS** |
| محدودیت | حجمی + زمانی + سقف اتصال همزمان |
| سابسکریپشن | تکی و گروهی (Base64) با هدر `subscription-userinfo` |
| پنل کاربر | صفحهٔ مصرف با QR، تم روز/شب، لینک دانلود کلاینت |
| مانیتورینگ | آنلاین واقعی، ترافیک ساعتی، لاگ فعالیت |
| ذخیره داده | Volume پایدار روی `/data` |

---

## پیش‌نیازها

- حساب [GitHub](https://github.com)
- حساب [Railway](https://railway.app)
- یک Volume روی مسیر `/data` (برای ماندگاری لینک‌ها)

---

## نصب و دیپلوی (گام‌به‌گام)

### ۱) ریپازیتوری

این پروژه را در یک مخزن GitHub خودتان قرار دهید (Push / Upload).

### ۲) سرویس Railway

1. وارد Railway شوید → **New Project** → **Deploy from GitHub repo**
2. همین مخزن را انتخاب کنید
3. صبر کنید تا بیلد تمام شود

### ۳) دامنه عمومی

**Settings → Networking → Generate Domain**

بدون این مرحله آدرس کانفیگ‌ها `localhost` می‌ماند.

پیشنهاد: بعد از ساخت دامنه یک‌بار **Redeploy** بزنید.

### ۴) Volume

**Settings → Volumes → Add Volume**

| Mount Path | مقدار پیشنهادی |
|------------|----------------|
| `/data` | حداقل 0.5 GB |

### ۵) متغیرهای محیطی (اختیاری ولی توصیه‌شده)

| متغیر | پیش‌فرض | توضیح |
|--------|----------|--------|
| `ADMIN_USER` | `admin` | نام کاربری پنل |
| `ADMIN_PASSWORD` | `12345` | رمز ورود — **حتماً عوض کنید** |
| `RAILWAY_PUBLIC_DOMAIN` | — | دامنهٔ پنل بدون `https://` (اگر خودکار درست نبود) |
| `PANEL_NAME` | `LPRW` | عنوان نمایشی |
| `SECRET_KEY` | خودکار | کلید امضای سشن |
| `DATA_DIR` | `/data` | مسیر ذخیره state |

---

## ورود به پنل

```
https://YOUR-DOMAIN.up.railway.app/dashboard
```

| فیلد | مقدار پیش‌فرض |
|------|----------------|
| نام کاربری | `admin` |
| رمز عبور | `12345` |

> بلافاصله بعد از ورود اول، از بخش **تنظیمات** رمز را تغییر دهید.

---

## نقشه مسیرها

| مسیر | نوع | کاربرد |
|------|-----|--------|
| `/dashboard` | UI | داشبورد مدیریت |
| `/u/{uuid}` | UI | پنل مصرف کاربر |
| `/sub/{uuid}` | API | سابسکریپشن تک‌لینک (Base64) |
| `/sub-group/{id}` | API | سابسکریپشن گروهی |
| `/qr/{uuid}` | API | تصویر QR کانفیگ |
| `/ws/{uuid}` | WebSocket | تونل VLESS |
| `/trojan-ws/{uuid}` | WebSocket | تونل Trojan |
| `/health` | API | وضعیت سلامت سرویس |
| `/api/*` | API | REST داخلی پنل (نیاز به سشن) |

---

## معماری تونل

```
Client (v2rayNG / Hiddify / …)
        │  TLS + WebSocket
        ▼
   Railway Edge
        │
        ▼
   LPRW (FastAPI)
        │  parse VLESS / Trojan header
        ▼
   TCP Relay  ──►  Destination
```

- مسیر VLESS: `/ws/{uuid}`
- مسیر Trojan: `/trojan-ws/{uuid}`
- رله با بافر بزرگ، `TCP_NODELAY` و شمارش ترافیک دسته‌ای (بدون قفل روی هر فریم)
- پاسخ اولیه VLESS برای کاهش تأخیر handshake

---

## سابسکریپشن

هر ساب شامل:

1. **خط وضعیت** — نمایش باقیمانده حجم و روز (فقط برای نمایش در لیست کلاینت)
2. **کانفیگ‌های واقعی** — VLESS یا Trojan قابل اتصال

هدرهای استاندارد کلاینت:

```
profile-title: base64:...
subscription-userinfo: upload=0; download=...; total=...; expire=...
profile-update-interval: 6
```

در کلاینت معمولاً با **Import subscription / افزودن اشتراک** لینک `/sub/...` یا `/sub-group/...` را وارد کنید.

---

## کلاینت‌های پیشنهادی

| پلتفرم | کلاینت |
|--------|--------|
| Android | v2rayNG · Hiddify · NekoBox |
| Windows | v2rayN · Hiddify |
| iOS | Streisand · V2Box · FoXray |
| چندسکویی | Hiddify |

مراحل کلی:

1. ساخت لینک در داشبورد  
2. کپی کانفیگ یا لینک ساب  
3. Import از کلیپ‌بورد / Subscription  
4. اتصال

صفحهٔ `/u/{uuid}` همین راهنما و لینک دانلود کلاینت‌ها را به کاربر نهایی نشان می‌دهد.

---

## نکات عملیاتی

- **دامنه:** اگر کانفیگ هنوز `localhost` است، `RAILWAY_PUBLIC_DOMAIN` را دستی ست کنید و Redeploy بزنید؛ یک‌بار هم داشبورد را در مرورگر باز کنید تا دامنه یاد گرفته شود.
- **منطقهٔ Railway:** برای کاربران ایران معمولاً منطقهٔ اروپا تأخیر کمتری از آمریکا دارد.
- **بکاپ:** از مسیر API بکاپ (در صورت فعال بودن در نسخه) یا کپی فایل `/data/lprw.json` استفاده کنید.
- **امنیت:** رمز پیش‌فرض را عوض کنید؛ لینک داشبورد را عمومی پخش نکنید.

---

## ساختار پروژه

```
LPRW/
├── main.py              # هسته FastAPI، API، ساب، احراز هویت
├── pages.py             # UI داشبورد + پنل کاربر
├── protocol/
│   ├── vless.py         # رله و پارس VLESS
│   └── trojan.py        # رله و پارس Trojan
├── requirements.txt
├── Procfile             # اجرای uvicorn روی Railway
└── README.md
```

---

## توسعه محلی

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export ADMIN_USER=admin
export ADMIN_PASSWORD=12345
export PUBLIC_HOST=localhost
export DATA_DIR=./data

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

سپس: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

---

## عیب‌یابی سریع

| مشکل | راه‌حل |
|------|--------|
| کانفیگ با `localhost` | Generate Domain + `RAILWAY_PUBLIC_DOMAIN` + Redeploy |
| سرویس Unexposed | Networking → Generate Domain |
| داده بعد از ری‌دیپلوی پاک می‌شود | Volume روی `/data` اضافه کنید |
| ورود انجام نمی‌شود | `ADMIN_USER` / `ADMIN_PASSWORD` را چک کنید |
| پینگ بالا | منطقهٔ Railway و کیفیت مسیر شبکه را بررسی کنید |

---

## مسئولیت استفاده

این نرم‌افزار صرفاً یک ابزار فنی برای مدیریت تونل است. رعایت قوانین کشور و ارائه‌دهندهٔ سرویس بر عهدهٔ کاربر است.

---

<p align="center">
  <strong>LPRW</strong> · Leviko Panel Railway<br/>
  <sub>Built for Railway · FastAPI · VLESS & Trojan</sub>
</p>
