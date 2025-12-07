# 💾 วิธีเก็บ Database ถาวรบน Streamlit Cloud

## ⚠️ ปัญหา

Streamlit Cloud ใช้ **ephemeral file system** ซึ่งหมายความว่า:
- ข้อมูลใน `/tmp` จะถูกลบเมื่อ app restart
- ข้อมูลใน local file system จะถูกลบเมื่อ redeploy
- **ไม่สามารถเก็บข้อมูลถาวรได้ด้วย SQLite**

## ✅ วิธีแก้ไข: ใช้ External Database

### ตัวเลือกที่แนะนำ

#### 1. **Supabase (แนะนำ - ฟรี!)**
- ✅ PostgreSQL database ฟรี
- ✅ ง่ายต่อการตั้งค่า
- ✅ มี dashboard สำหรับจัดการ
- ✅ รองรับ connection pooling

#### 2. **PostgreSQL (Heroku, AWS RDS, Google Cloud SQL)**
- ✅ ใช้งานได้ดี
- ✅ รองรับการขยายตัว
- ⚠️ อาจมีค่าใช้จ่าย

#### 3. **MySQL (PlanetScale, AWS RDS)**
- ✅ ใช้งานได้ดี
- ✅ PlanetScale มี free tier
- ⚠️ อาจต้องปรับโค้ดเล็กน้อย

## 🚀 วิธีตั้งค่า

### วิธีที่ 1: ใช้ Supabase (แนะนำ)

#### ขั้นตอนที่ 1: สร้าง Supabase Project
1. ไปที่ https://supabase.com
2. Sign up / Sign in
3. กด "New Project"
4. ตั้งชื่อ project และเลือก region
5. รอให้สร้างเสร็จ (ประมาณ 2 นาที)

#### ขั้นตอนที่ 2: ดู Connection String
1. ไปที่ Project Settings > Database
2. คัดลอก **Connection string** (URI format)
   - ตัวอย่าง: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

#### ขั้นตอนที่ 3: ตั้งค่าใน Streamlit Cloud
1. ไปที่ Streamlit Cloud dashboard
2. เลือก app ของคุณ
3. กด "Settings" > "Secrets"
4. เพิ่ม secrets ดังนี้:

```toml
[database]
type = "postgresql"
host = "db.xxxxx.supabase.co"
port = 5432
user = "postgres"
password = "YOUR-PASSWORD"
database = "postgres"
```

#### ขั้นตอนที่ 4: Deploy
1. Push โค้ดไป GitHub
2. Streamlit Cloud จะ rebuild อัตโนมัติ
3. ระบบจะเชื่อมต่อกับ Supabase database

### วิธีที่ 2: ใช้ PostgreSQL (Heroku)

#### ขั้นตอนที่ 1: สร้าง Heroku Postgres
1. ไปที่ https://heroku.com
2. สร้าง app ใหม่
3. เพิ่ม Heroku Postgres addon (free tier)
4. ดู connection string จาก Config Vars

#### ขั้นตอนที่ 2: ตั้งค่าใน Streamlit Cloud
```toml
[database]
type = "postgresql"
host = "xxxxx.amazonaws.com"
port = 5432
user = "xxxxx"
password = "xxxxx"
database = "xxxxx"
```

### วิธีที่ 3: ใช้ MySQL (PlanetScale)

#### ขั้นตอนที่ 1: สร้าง PlanetScale Database
1. ไปที่ https://planetscale.com
2. Sign up / Sign in
3. สร้าง database ใหม่
4. ดู connection string

#### ขั้นตอนที่ 2: ตั้งค่าใน Streamlit Cloud
```toml
[database]
type = "mysql"
host = "xxxxx.psdb.cloud"
port = 3306
user = "xxxxx"
password = "xxxxx"
database = "xxxxx"
```

## 📝 ตัวอย่าง Streamlit Secrets

### สำหรับ Supabase (PostgreSQL)
```toml
[database]
type = "postgresql"
host = "db.xxxxx.supabase.co"
port = 5432
user = "postgres"
password = "your-password-here"
database = "postgres"
```

### สำหรับ Heroku Postgres
```toml
[database]
type = "postgresql"
host = "ec2-xx-xx-xx-xx.compute-1.amazonaws.com"
port = 5432
user = "xxxxx"
password = "xxxxx"
database = "xxxxx"
```

### สำหรับ PlanetScale (MySQL)
```toml
[database]
type = "mysql"
host = "xxxxx.psdb.cloud"
port = 3306
user = "xxxxx"
password = "xxxxx"
database = "xxxxx"
```

## 🔧 การใช้งาน

### Auto-Detection
ระบบจะตรวจสอบอัตโนมัติ:
1. **Streamlit Secrets** (สำหรับ Streamlit Cloud)
2. **Environment Variables** (DATABASE_URL)
3. **SQLite** (default สำหรับ local)

### Local Development
สำหรับ local development ยังใช้ SQLite ได้ตามปกติ:
- Database จะเก็บใน `data/pos.db`
- ไม่ต้องตั้งค่าเพิ่มเติม

### Streamlit Cloud
เมื่อตั้งค่า secrets แล้ว:
- ระบบจะเชื่อมต่อกับ external database อัตโนมัติ
- ข้อมูลจะเก็บถาวร
- ไม่ถูกลบเมื่อ app restart

## 🔒 ความปลอดภัย

### ⚠️ ข้อควรระวัง
- **อย่า commit secrets ไปที่ GitHub!**
- ใช้ Streamlit Secrets สำหรับเก็บ connection string
- ใช้ environment variables สำหรับ local development

### ✅ Best Practices
1. ใช้ strong password
2. จำกัด IP access (ถ้าเป็นไปได้)
3. ใช้ SSL/TLS connection
4. สำรองข้อมูลเป็นประจำ

## 📊 เปรียบเทียบ

| Database | Free Tier | ง่ายต่อการตั้งค่า | รองรับ |
|----------|-----------|------------------|--------|
| Supabase | ✅ 500MB | ⭐⭐⭐⭐⭐ | ✅ |
| Heroku Postgres | ✅ 10K rows | ⭐⭐⭐⭐ | ✅ |
| PlanetScale | ✅ 5GB | ⭐⭐⭐⭐ | ✅ |
| AWS RDS | ❌ | ⭐⭐⭐ | ✅ |
| Google Cloud SQL | ❌ | ⭐⭐⭐ | ✅ |

## 🎯 สรุป

### สำหรับ Local Development
- ใช้ SQLite (default)
- ไม่ต้องตั้งค่าเพิ่มเติม

### สำหรับ Streamlit Cloud
1. สร้าง external database (แนะนำ: Supabase)
2. ตั้งค่า Streamlit Secrets
3. Deploy!
4. ✅ ข้อมูลจะเก็บถาวร!

## 💡 Tips

1. **เริ่มต้นด้วย Supabase** - ฟรีและง่ายที่สุด
2. **ทดสอบ local ก่อน** - ใช้ environment variables
3. **สำรองข้อมูล** - สำรองเป็นประจำ
4. **Monitor usage** - ตรวจสอบการใช้งาน database

## 🔗 Links

- [Supabase](https://supabase.com)
- [Heroku Postgres](https://www.heroku.com/postgres)
- [PlanetScale](https://planetscale.com)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

