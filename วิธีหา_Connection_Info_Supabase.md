# 📍 วิธีหา Connection Info ใน Supabase

## 🎯 Connection Info อยู่ที่ไหน?

### วิธีที่ 1: ดูจาก Connection String (แนะนำ - ง่ายที่สุด!)

1. ไปที่ **Supabase Dashboard**
2. เลือก **Project** ของคุณ
3. ไปที่ **Settings** (⚙️) > **Database**
4. **เลื่อนลงไปหา "Connection string"** หรือ **"Connection info"**
   - มักจะอยู่ด้านบนของหน้า Database Settings
   - หรือดูในส่วน **"Connection pooling"**
5. จะเห็น **Connection string** ในรูปแบบ:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
6. **แยกข้อมูลออกมา:**
   - **Host**: `db.xxxxx.supabase.co` (ส่วนหลัง @ และก่อน :5432)
   - **Port**: `5432` (หลัง :)
   - **Database**: `postgres` (หลัง /)
   - **User**: `postgres` (หลัง ://)
   - **Password**: `[YOUR-PASSWORD]` (ส่วนที่อยู่ใน [ ] - ต้องใช้รหัสผ่านที่ตั้งไว้ตอนสร้าง project)

### วิธีที่ 2: ดูจาก Connection Parameters (แยกเป็นช่องๆ)

1. ไปที่ **Settings** > **Database**
2. หาส่วน **"Connection parameters"** หรือ **"Connection info"**
3. จะเห็นข้อมูลแยกเป็นช่องๆ:
   - **Host**: `db.xxxxx.supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: (ต้องดูในส่วน "Database password")

### วิธีที่ 3: ดู Password แยก

1. ไปที่ **Settings** > **Database**
2. หาส่วน **"Database password"**
3. ถ้าไม่เห็น password:
   - กด **"Reset database password"**
   - ตั้งรหัสผ่านใหม่
   - **จำไว้ให้ดี!** (จะใช้ตอนตั้งค่า Streamlit Cloud)

## 📋 ข้อมูลที่ต้องหา

### ✅ ข้อมูลที่ต้องมี:
- ✅ **Host**: `db.xxxxx.supabase.co` (รูปแบบ: db.xxxxx.supabase.co)
- ✅ **Port**: `5432` (default - ไม่เปลี่ยน)
- ✅ **Database**: `postgres` (default - ไม่เปลี่ยน)
- ✅ **User**: `postgres` (default - ไม่เปลี่ยน)
- ✅ **Password**: (รหัสผ่านที่ตั้งไว้ตอนสร้าง project)

## 🔍 ตัวอย่าง Connection String

```
postgresql://postgres:MyPassword123!@db.abcdefghijklmnop.supabase.co:5432/postgres
```

**แยกออกมา:**
- **Host**: `db.abcdefghijklmnop.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: `MyPassword123!`

## 💡 Tips

### ถ้าหาไม่เจอ:
1. **ลองดูในส่วน "Connection pooling"** - มักจะมี Connection string อยู่ที่นั่น
2. **ลองดูในส่วน "SSL Configuration"** - บางครั้งจะมี Connection info
3. **ลองดูในส่วน "Database password"** - เพื่อดู password

### ถ้าลืม Password:
1. กด **"Reset database password"**
2. ตั้งรหัสผ่านใหม่
3. **จำไว้ให้ดี!**
4. ใช้รหัสผ่านใหม่ในการตั้งค่า Streamlit Cloud

## 📝 ตัวอย่างที่ถูกต้อง

### สำหรับ Streamlit Cloud Secrets:
```toml
[database]
type = "postgresql"
host = "db.abcdefghijklmnop.supabase.co"
port = 5432
user = "postgres"
password = "MyPassword123!"
database = "postgres"
```

## ⚠️ ข้อควรระวัง

1. **อย่า share password กับใคร!**
2. **ใช้ Streamlit Secrets** สำหรับเก็บ password
3. **อย่า commit password ไป GitHub!**
4. **ใช้ strong password** (มีตัวอักษร ตัวเลข และอักขระพิเศษ)

## 🎯 สรุป

**Connection info อยู่ที่:**
- **Settings** > **Database** > **Connection string** หรือ **Connection info**
- หรือดูในส่วน **"Connection pooling"**
- **Password** ดูในส่วน **"Database password"**

**ข้อมูลที่ต้องหา:**
- Host, Port, Database, User, Password

**ใช้สำหรับ:**
- ตั้งค่า Streamlit Cloud Secrets

