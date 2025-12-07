# 🔍 วิธีตรวจสอบ Streamlit Cloud Secrets

## ❌ ปัญหาที่พบ:

Error แสดงว่าเชื่อมต่อไปที่ Direct Connection (`db.thvvvsyujfzntvepmvzo.supabase.co:5432`) 
แม้ว่าจะตั้งค่า Transaction Pooler (`aws-1-ap-southeast-1.pooler.supabase.com:6543`) แล้ว

## 🔍 สาเหตุที่เป็นไปได้:

1. **Streamlit Cloud Secrets ยังไม่ได้อัปเดต** - ข้อมูลเก่ายังอยู่ใน cache
2. **ข้อมูลใน Secrets ไม่ถูกต้อง** - host, port, user ไม่ตรงกับ Transaction Pooler
3. **App ยังไม่ได้ restart** - ต้อง restart app หลังอัปเดต Secrets

## ✅ วิธีแก้ไข:

### ขั้นตอนที่ 1: ตรวจสอบ Streamlit Cloud Secrets

1. ไปที่ **Streamlit Cloud Dashboard**
2. เลือก **App** ของคุณ
3. ไปที่ **Settings** > **Secrets**
4. **ตรวจสอบข้อมูล** ว่าถูกต้องหรือไม่:

```toml
[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"  # ⬅️ ต้องเป็น Transaction pooler host
port = 6543  # ⬅️ ต้องเป็น 6543 (Transaction mode)
user = "postgres.thvvvsyujfzntvepmvzo"  # ⬅️ ต้องเป็น postgres.PROJECT_REF
password = "Yoyo25252525*-01461"  # ⬅️ ต้องเป็น password จริง
database = "postgres"
```

### ขั้นตอนที่ 2: อัปเดต Secrets (ถ้ายังไม่ถูกต้อง)

1. **แก้ไขข้อมูล** ใน Streamlit Cloud Secrets:
   - ตรวจสอบว่า `host` เป็น `aws-1-ap-southeast-1.pooler.supabase.com` (ไม่ใช่ `db.thvvvsyujfzntvepmvzo.supabase.co`)
   - ตรวจสอบว่า `port` เป็น `6543` (ไม่ใช่ `5432`)
   - ตรวจสอบว่า `user` เป็น `postgres.thvvvsyujfzntvepmvzo` (ไม่ใช่ `postgres`)

2. **Save** Secrets

### ขั้นตอนที่ 3: Restart App

1. ไปที่ **Streamlit Cloud Dashboard** > **App** ของคุณ
2. กดปุ่ม **"⋮"** (สามจุด) > **"Restart app"**
3. หรือ **Redeploy** app อีกครั้ง

### ขั้นตอนที่ 4: ตรวจสอบ Logs

1. ไปที่ **Streamlit Cloud Dashboard** > **App** > **Logs**
2. **ดู debug messages:**
   ```
   [DEBUG] Reading database config from Streamlit secrets:
   [DEBUG]   type: postgresql
   [DEBUG]   host: aws-1-ap-southeast-1.pooler.supabase.com
   [DEBUG]   port: 6543
   [DEBUG]   user: postgres.thvvvsyujfzntvepmvzo
   [DEBUG]   database: postgres
   [DEBUG] ✅ Using PostgreSQL connection: postgresql://postgres.thvvvsyujfzntvepmvzo:***@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```

3. **ถ้าเห็น host เป็น `db.thvvvsyujfzntvepmvzo.supabase.co`** = Secrets ยังไม่ได้อัปเดต
4. **ถ้าเห็น host เป็น `aws-1-ap-southeast-1.pooler.supabase.com`** = Secrets ถูกต้องแล้ว

---

## 📋 Checklist:

- [ ] ตรวจสอบ Streamlit Cloud Secrets ว่าถูกต้อง
- [ ] ตรวจสอบว่า `host` เป็น Transaction pooler host (`aws-1-ap-southeast-1.pooler.supabase.com`)
- [ ] ตรวจสอบว่า `port` เป็น `6543` (Transaction mode)
- [ ] ตรวจสอบว่า `user` เป็น `postgres.thvvvsyujfzntvepmvzo` (รูปแบบ: `postgres.PROJECT_REF`)
- [ ] ตรวจสอบว่า `password` ถูกต้อง
- [ ] Save Secrets
- [ ] Restart App
- [ ] ตรวจสอบ Logs ว่าใช้ connection string ถูกต้อง

---

## 🔍 ตัวอย่าง Debug Output ที่ถูกต้อง:

```
[DEBUG] Reading database config from Streamlit secrets:
[DEBUG]   type: postgresql
[DEBUG]   host: aws-1-ap-southeast-1.pooler.supabase.com
[DEBUG]   port: 6543
[DEBUG]   user: postgres.thvvvsyujfzntvepmvzo
[DEBUG]   database: postgres
[DEBUG]   password: ***
[DEBUG] ✅ Using PostgreSQL connection: postgresql://postgres.thvvvsyujfzntvepmvzo:***@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
[DEBUG] 🔗 Final DATABASE_URL: postgresql://postgres.thvvvsyujfzntvepmvzo:***@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

---

## ❌ ตัวอย่าง Debug Output ที่ผิด (ยังใช้ Direct Connection):

```
[DEBUG] Reading database config from Streamlit secrets:
[DEBUG]   type: postgresql
[DEBUG]   host: db.thvvvsyujfzntvepmvzo.supabase.co  # ⬅️ ผิด! ต้องเป็น Transaction pooler host
[DEBUG]   port: 5432  # ⬅️ ผิด! ต้องเป็น 6543
[DEBUG]   user: postgres  # ⬅️ ผิด! ต้องเป็น postgres.thvvvsyujfzntvepmvzo
```

**ถ้าเห็นแบบนี้ = ต้องอัปเดต Streamlit Cloud Secrets อีกครั้ง**

---

## 💡 Tips:

1. **หลังจากอัปเดต Secrets ต้อง Restart App** - Streamlit Cloud จะ cache secrets
2. **ตรวจสอบ Logs ทุกครั้ง** - จะเห็น debug messages ที่บอกว่าอ่านค่าอะไร
3. **ใช้ Transaction Pooler สำหรับ Streamlit Cloud** - Direct Connection จะ error เพราะไม่รองรับ IPv6

