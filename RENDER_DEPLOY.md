# 🚀 คู่มือ Deploy บน Render.com

## ✅ ทำไม Render.com ดีกว่า Streamlit Cloud?

### ข้อดีของ Render.com:
1. **✅ Persistent Disks** - เก็บไฟล์ถาวรได้ (รวม SQLite!)
2. **✅ Render Postgres** - PostgreSQL database ฟรี
3. **✅ รองรับ Python** - Deploy Streamlit ได้
4. **✅ Auto-deploy** - จาก GitHub
5. **✅ Free tier** - มี free tier สำหรับทดสอบ
6. **✅ Custom domains** - ตั้งค่า domain ได้

### เปรียบเทียบ

| ฟีเจอร์ | Streamlit Cloud | Render.com |
|---------|----------------|-----------|
| Persistent Storage | ❌ | ✅ (Persistent Disks) |
| SQLite ถาวร | ❌ | ✅ |
| PostgreSQL | ⚠️ (ต้อง external) | ✅ (Render Postgres) |
| Free tier | ✅ | ✅ |
| Custom domain | ⚠️ | ✅ |
| Auto-deploy | ✅ | ✅ |

## 🚀 วิธี Deploy

### วิธีที่ 1: ใช้ Persistent Disks (เก็บ SQLite ถาวร)

#### ขั้นตอนที่ 1: สร้าง Render Account
1. ไปที่ https://render.com
2. Sign up / Sign in ด้วย GitHub
3. Connect GitHub account

#### ขั้นตอนที่ 2: สร้าง Web Service
1. กด "New +" > "Web Service"
2. Connect repository ของคุณ
3. ตั้งค่า:
   - **Name**: `pos-system` (หรือชื่อที่ต้องการ)
   - **Region**: เลือก region ที่ใกล้ที่สุด
   - **Branch**: `main` หรือ `master`
   - **Root Directory**: `.` (root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

#### ขั้นตอนที่ 3: เพิ่ม Persistent Disk
1. ไปที่ Settings > Persistent Disks
2. กด "Add Persistent Disk"
3. ตั้งค่า:
   - **Name**: `database`
   - **Mount Path**: `/data`
   - **Size**: 1GB (หรือตามต้องการ)

#### ขั้นตอนที่ 4: แก้ไข Database Path
แก้ไข `database/db.py` ให้ใช้ persistent disk:

```python
# ใช้ persistent disk บน Render
if os.path.exists("/data"):
    DB_DIR = "/data"  # Persistent disk
elif os.path.exists("/tmp"):
    DB_DIR = "/tmp"   # Temporary (Streamlit Cloud)
else:
    DB_DIR = "data"   # Local development
```

#### ขั้นตอนที่ 5: Deploy!
1. กด "Create Web Service"
2. Render จะ build และ deploy อัตโนมัติ
3. ✅ ข้อมูลจะเก็บถาวรใน persistent disk!

### วิธีที่ 2: ใช้ Render Postgres (แนะนำ)

#### ขั้นตอนที่ 1: สร้าง PostgreSQL Database
1. กด "New +" > "PostgreSQL"
2. ตั้งค่า:
   - **Name**: `pos-database`
   - **Database**: `pos`
   - **User**: `pos_user`
   - **Region**: เลือก region เดียวกับ web service
   - **Plan**: Free (หรือ paid)

#### ขั้นตอนที่ 2: ตั้งค่า Environment Variables
1. ไปที่ Web Service > Environment
2. เพิ่ม environment variables:
   ```
   DATABASE_URL=<Internal Database URL>
   ```
   (Render จะให้ Internal Database URL อัตโนมัติ)

#### ขั้นตอนที่ 3: Deploy!
1. ระบบจะใช้ PostgreSQL อัตโนมัติ
2. ✅ ข้อมูลจะเก็บถาวร!

## 📝 ไฟล์ที่ต้องสร้าง

### `render.yaml` (Optional - Infrastructure as Code)

```yaml
services:
  - type: web
    name: pos-system
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: pos-database
          property: connectionString
    disk:
      name: database
      mountPath: /data
      sizeGB: 1

databases:
  - name: pos-database
    databaseName: pos
    user: pos_user
    plan: free
```

### `Procfile` (Alternative)

```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

## 🔧 การตั้งค่า

### Environment Variables

#### สำหรับ Persistent Disks (SQLite):
```
DATABASE_PATH=/data/pos.db
```

#### สำหรับ Render Postgres:
```
DATABASE_URL=<Internal Database URL>
```

### Streamlit Config

สร้าง `.streamlit/config.toml`:

```toml
[server]
headless = true
port = $PORT
address = "0.0.0.0"

[browser]
gatherUsageStats = false
```

## 📊 เปรียบเทียบ Options

### Option 1: Persistent Disks + SQLite
- ✅ เก็บ SQLite ถาวรได้
- ✅ ไม่ต้องตั้งค่า database
- ✅ ใช้ได้กับโค้ดเดิม
- ⚠️ จำกัดขนาด (ตาม disk size)

### Option 2: Render Postgres
- ✅ ข้อมูลถาวร
- ✅ Scale ได้
- ✅ รองรับ concurrent access
- ✅ Free tier
- ⚠️ ต้องตั้งค่าเพิ่มเติม

## 💰 Pricing

### Free Tier:
- **Web Service**: 750 hours/month (พอใช้)
- **PostgreSQL**: 90 days free trial
- **Persistent Disk**: ต้องใช้ paid plan

### Paid Plans:
- **Starter**: $7/month
- **Standard**: $25/month
- **Pro**: $85/month

## 🎯 คำแนะนำ

### สำหรับ Production:
1. **ใช้ Render Postgres** - ดีที่สุด
2. **ใช้ Persistent Disks** - ถ้าต้องการ SQLite
3. **ตั้งค่า Custom Domain** - สำหรับ production

### สำหรับ Testing:
1. **ใช้ Free tier** - ทดสอบได้
2. **ใช้ SQLite + Persistent Disks** - ง่ายและเร็ว

## 🔗 Links

- [Render.com](https://render.com)
- [Render Docs](https://render.com/docs)
- [Render Postgres](https://render.com/docs/databases)
- [Persistent Disks](https://render.com/docs/disks)

## 📝 สรุป

### ✅ Render.com ดีกว่า Streamlit Cloud เพราะ:
1. **Persistent Disks** - เก็บ SQLite ถาวรได้!
2. **Render Postgres** - PostgreSQL ฟรี
3. **Custom domains** - ตั้งค่า domain ได้
4. **More control** - ควบคุมได้มากกว่า

### 🚀 วิธี Deploy:
1. สร้าง Render account
2. Connect GitHub
3. สร้าง Web Service
4. เพิ่ม Persistent Disk หรือ Render Postgres
5. Deploy!

**แนะนำ: ใช้ Render.com สำหรับ production!**

