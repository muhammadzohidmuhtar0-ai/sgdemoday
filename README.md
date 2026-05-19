# SG Demo Day Bot (@SGdemodaybot)

Startup Garage Demo Day uchun ariza qabul qiluvchi Telegram bot.

## Xususiyatlar

- ✅ Avval `@Startupgarage_uz` kanaliga obuna bo'lishni so'raydi
- ✅ Obuna tasdiqlangach: Ism Familiya → Startup nomi → Telefon (Telegram orqali) → Loyiha fayli
- ✅ Ma'lumotlar Google Sheets'ga avtomatik yoziladi
- ✅ Adminlar guruhiga ariza + fayl yuboriladi
- ✅ Foydalanuvchiga tasdiq xabari chiqadi

---

## 1-qadam: Bot Tokenini olish

1. Telegramda `@BotFather` ni oching
2. `/newbot` yuboring (yoki `/token` agar bot allaqachon yaratilgan bo'lsa)
3. Bot nomi: `SG Demo Day Bot`, username: `SGdemodaybot`
4. **Token'ni saqlang** — masalan: `123456789:AAGxxxxxxxxxxxxxxx`

## 2-qadam: Kanalda botni admin qilish

`@Startupgarage_uz` kanalida bot **admin** bo'lishi shart (obunani tekshirish uchun):
1. Kanalga kiring → "Administrators" → "Add Administrator"
2. `@SGdemodaybot` ni qo'shing
3. Hech qanday huquq bermasangiz ham bo'ladi — faqat admin bo'lsa kifoya

## 3-qadam: Adminlar guruhini yaratish

1. Telegramda yangi **guruh** yarating (masalan: "SG Demo Day — Arizalar")
2. `@SGdemodaybot` ni guruhga qo'shing va **admin** qiling
3. Guruh chat ID sini olish uchun:
   - Guruhga `@username_to_id_bot` (yoki `@getmyid_bot`) ni qo'shing
   - U sizga guruh ID ni beradi (manfiy son, masalan: `-1001234567890`)
   - ID ni olgach, helper botni guruhdan o'chiring

## 4-qadam: Google Sheets sozlash

### 4.1 Google Cloud Console'da loyiha yarating
1. https://console.cloud.google.com/ — yangi loyiha yarating
2. "APIs & Services" → "Library" → quyidagilarni yoqing:
   - **Google Sheets API**
   - **Google Drive API**

### 4.2 Service Account yarating
1. "APIs & Services" → "Credentials" → "Create Credentials" → "Service Account"
2. Nom bering (masalan: `sg-demoday-bot`)
3. Yaratilgach, service account'ga kiring → "Keys" → "Add Key" → "JSON"
4. JSON fayl yuklab olinadi — uni `credentials.json` deb nomlang va loyiha papkasiga joylashtiring

### 4.3 Google Sheet yarating
1. https://sheets.google.com — yangi jadval yarating (masalan: "SG Demo Day Arizalari")
2. URL'dan **Sheet ID** ni oling:
   `https://docs.google.com/spreadsheets/d/`**`BU_QISMI`**`/edit`
3. Service account email'ini sheet'ga **Editor** sifatida share qiling
   - Email shaklda: `sg-demoday-bot@<loyiha>.iam.gserviceaccount.com`
   - Uni `credentials.json` ichidan topishingiz mumkin (`client_email` maydonidan)

## 5-qadam: Loyihani ishga tushirish

```bash
cd /Users/muhammad/Documents/SGdemodaybot

# Virtual environment yaratish
python3 -m venv venv
source venv/bin/activate

# Kerakli paketlarni o'rnatish
pip install -r requirements.txt

# .env faylini sozlash
cp .env.example .env
# .env faylini oching va o'z qiymatlaringizni kiriting:
#   BOT_TOKEN, ADMIN_GROUP_ID, GOOGLE_SHEET_ID

# credentials.json fayli loyiha papkasida bo'lsin

# Botni ishga tushirish
python bot.py
```

---

## Fayllar tuzilishi

```
SGdemodaybot/
├── bot.py              # Asosiy bot kodi
├── sheets.py           # Google Sheets bilan ishlash
├── requirements.txt    # Python paketlar
├── .env                # Sizning sozlamalaringiz (yaratasiz)
├── .env.example        # Sozlamalar namunasi
├── credentials.json    # Google service account (yuklab olasiz)
└── README.md
```

## Hosting (keyinroq)

Lokal kompyuter o'chsa bot ham to'xtaydi. 24/7 ishlashi uchun:
- **Railway.app** (eng oson) — GitHub'ga push qiling, Railway avtomatik deploy qiladi
- **VPS** (DigitalOcean / Hetzner) — `screen` yoki `systemd` orqali doimiy ishlatish
- **PythonAnywhere** — Python loyihalar uchun arzon variant
