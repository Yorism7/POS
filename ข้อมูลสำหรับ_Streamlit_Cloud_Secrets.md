# 📋 ข้อมูลสำหรับ Streamlit Cloud Secrets

## 🎯 ข้อมูลที่ต้องคัดลอกไปวางใน Streamlit Cloud

### ขั้นตอนการตั้งค่า:

1. ไปที่ **Streamlit Cloud Dashboard**
2. เลือก **App** ของคุณ
3. ไปที่ **Settings** > **Secrets**
4. **คัดลอกและวาง** ข้อมูลด้านล่างนี้:

---

## 📝 ข้อมูลที่ต้องวาง (คัดลอกทั้งหมด):

```toml
# สำหรับ Supabase Database (PostgreSQL)
# ⚠️ สำคัญ: ใช้ Connection Pooler (Transaction Mode) สำหรับ Streamlit Cloud
# เพราะ Streamlit Cloud ไม่รองรับ IPv6 (Direct connection ใช้ IPv6)
# 
# ========================================
# Transaction Mode Pooler (แนะนำสำหรับ Streamlit Cloud)
# ========================================
# วิธีหา:
# 1. ไปที่ Supabase Dashboard > Settings > Database > กด "Connect"
# 2. เลือก "Transaction mode" (port 6543)
# 3. ดูใน "View parameters":
#    - Host: aws-1-ap-southeast-1.pooler.supabase.com
#    - Port: 6543
#    - User: postgres.thvvvsyujfzntvepmvzo
#    - Password: (รหัสผ่าน Database)
#    - Database: postgres
#
# ========================================
# Direct Connection (สำหรับ Local Development เท่านั้น)
# ========================================
# ⚠️ ไม่ใช้กับ Streamlit Cloud (ไม่รองรับ IPv6)
# วิธีหา:
# 1. ไปที่ Supabase Dashboard > Settings > Database > กด "Connect"
# 2. เลือก "Direct connection" (port 5432)
# 3. ดูใน "View parameters":
#    - Host: db.thvvvsyujfzntvepmvzo.supabase.co
#    - Port: 5432
#    - User: postgres
#    - Password: (รหัสผ่าน Database)
#    - Database: postgres

[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"  # ⬅️ Transaction pooler host (สำหรับ Streamlit Cloud)
port = 6543  # ⬅️ Transaction mode pooler (แนะนำสำหรับ Streamlit Cloud)
user = "postgres.thvvvsyujfzntvepmvzo"  # ⬅️ Transaction pooler user (รูปแบบ: postgres.PROJECT_REF)
password = "your-database-password-here"  # ⬅️ แก้ไข: ใส่ password จริง
database = "postgres"

# สำหรับ Supabase Auth + OAuth (Optional)
[supabase]
url = "https://thvvvsyujfzntvepmvzo.supabase.co"
publishable_key = "sb_publishable_kvb5ahfcTvBjAhweDea-CA_xD1leVIa"
redirect_url = "https://pos-ez.streamlit.app/auth/callback"
```

---

## ⚠️ ข้อมูลที่ต้องแก้ไขก่อนวาง:

### 1. Database Password
```
password = "your-database-password-here"
```
**ต้องแก้ไข:** ใส่รหัสผ่าน Database ที่ตั้งไว้ตอนสร้าง Supabase Project

**วิธีหา:**
- ไปที่ Supabase Dashboard > Settings > Database
- ดูในส่วน "Database password"
- ถ้าไม่เห็น: กด "Reset database password" เพื่อตั้งใหม่

### 2. Redirect URL
```
redirect_url = "https://pos-ez.streamlit.app/auth/callback"
```
**ต้องแก้ไข:** เปลี่ยน `pos-ez.streamlit.app` เป็น URL ของ Streamlit app ของคุณ

**วิธีหา:**
- ดู URL ของ app ใน Streamlit Cloud Dashboard
- ตัวอย่าง: `https://your-app-name.streamlit.app`
- แล้วเพิ่ม `/auth/callback` ต่อท้าย

---

## ✅ ตัวอย่างที่ถูกต้อง (หลังจากแก้ไขแล้ว):

```toml
[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"  # Transaction pooler host
port = 6543  # Transaction mode pooler (แนะนำสำหรับ Streamlit Cloud)
user = "postgres.thvvvsyujfzntvepmvzo"  # Transaction pooler user (รูปแบบ: postgres.PROJECT_REF)
password = "MySecurePassword123!"  # Database password
database = "postgres"

[supabase]
url = "https://thvvvsyujfzntvepmvzo.supabase.co"
publishable_key = "sb_publishable_kvb5ahfcTvBjAhweDea-CA_xD1leVIa"
redirect_url = "https://your-app-name.streamlit.app/auth/callback"
```

---

## 📋 Checklist ก่อน Deploy:

- [ ] แก้ไข `host` ใน `[database]` section (aws-1-ap-southeast-1.pooler.supabase.com)
- [ ] แก้ไข `user` ใน `[database]` section (postgres.thvvvsyujfzntvepmvzo)
- [ ] แก้ไข `password` ใน `[database]` section (ใส่ password จริง)
- [ ] ตรวจสอบว่า `port` เป็น 6543 (Transaction mode pooler)
- [ ] แก้ไข `redirect_url` ใน `[supabase]` section
- [ ] ตรวจสอบว่า `url` ถูกต้อง (https://thvvvsyujfzntvepmvzo.supabase.co)
- [ ] ตรวจสอบว่า `publishable_key` ถูกต้อง
- [ ] คัดลอกทั้งหมดไปวางใน Streamlit Cloud Secrets
- [ ] Save และ Deploy

---

## 💡 Tips:

1. **อย่า commit secrets ไป GitHub!** - ใช้ Streamlit Cloud Secrets แทน
2. **ตรวจสอบข้อมูลให้ถูกต้อง** - ถ้า host หรือ password ผิด จะเชื่อมต่อ database ไม่ได้
3. **บันทึก password ไว้** - ถ้าลืมต้อง reset ใหม่
4. **ใช้ Publishable key** - ปลอดภัยสำหรับใช้ใน browser

---

## 🔍 วิธีตรวจสอบว่าเชื่อมต่อได้:

1. Deploy app บน Streamlit Cloud
2. เปิด app
3. ล็อคอิน (admin/admin)
4. ไปที่หน้า **📦 จัดการสต็อค**
5. เพิ่มสินค้าทดสอบ
6. ไปที่ Supabase Dashboard > Table Editor
7. ดูตาราง `products` - **ควรเห็นสินค้าที่เพิ่มไว้!** ✅

---

## ❌ ถ้าเชื่อมต่อไม่ได้:

### ปัญหา: "Cannot assign requested address" หรือ "Connection refused"

**สาเหตุ:** Streamlit Cloud ไม่รองรับ IPv6 (Direct connection ใช้ IPv6)

**วิธีแก้:**
1. **ใช้ Connection Pooler แทน Direct Connection**
   - ไปที่ Supabase Dashboard > Settings > Database
   - กด "Connect" button
   - เลือก **"Transaction mode"** (port 6543) - เหมาะสำหรับ serverless
   - หรือเลือก **"Session mode"** (port 5432) - สำหรับ persistent backend
   - คัดลอก Connection string หรือแยกข้อมูล

2. **อัปเดต port ใน Streamlit Cloud Secrets:**
   - ใช้ `port = 6543` สำหรับ Transaction mode (แนะนำ)
   - หรือ `port = 5432` สำหรับ Session mode

3. **ตรวจสอบข้อมูลอื่นๆ:**
   - ตรวจสอบ password - ต้องตรงกับที่ตั้งไว้ใน Supabase
   - ตรวจสอบ host - ต้องเป็น `db.thvvvsyujfzntvepmvzo.supabase.co`
   - ดู logs - ไปที่ Streamlit Cloud > App > Logs
   - ลอง reset password - ไปที่ Supabase > Settings > Database > Reset database password

### 📖 อ่านเพิ่มเติม:
- [Supabase Connection Pooler Documentation](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

