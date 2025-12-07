# 🔍 วิธีตรวจสอบว่า Streamlit Cloud Secrets ถูกต้อง

## ❌ ปัญหา: ระบบยังใช้ SQLite แทน Supabase

หากคุณเห็นข้อความว่า:
```
⚠️ WARNING: Using SQLite in /tmp - data will be LOST on restart!
```

นั่นหมายความว่าระบบยังไม่ได้เชื่อมต่อ Supabase PostgreSQL

## ✅ วิธีแก้ไข

### ขั้นตอนที่ 1: ตรวจสอบ Streamlit Cloud Secrets

1. **ไปที่ Streamlit Cloud Dashboard**
   - ไปที่ https://share.streamlit.io
   - Sign in ด้วย GitHub
   - เลือก App ของคุณ (pos-ez)

2. **เปิด Settings > Secrets**
   - คลิกที่ App ของคุณ
   - ไปที่เมนู **Settings** (⚙️)
   - เลือก **Secrets** (🔐)

3. **ตรวจสอบว่ามี `[database]` section หรือไม่**

   ควรจะมีหน้าตาแบบนี้:
   ```toml
   [database]
   type = "postgresql"
   host = "aws-1-ap-southeast-1.pooler.supabase.com"
   port = 6543
   user = "postgres.thvvvsyujfzntvepmvzo"
   database = "postgres"
   password = "YOUR_PASSWORD_HERE"
   ```

### ขั้นตอนที่ 2: เพิ่ม/แก้ไข Secrets

หากไม่มี `[database]` section:

1. **คลิก "Edit secrets"**
2. **เพิ่ม section นี้:**
   ```toml
   [database]
   type = "postgresql"
   host = "aws-1-ap-southeast-1.pooler.supabase.com"
   port = 6543
   user = "postgres.thvvvsyujfzntvepmvzo"
   database = "postgres"
   password = "YOUR_SUPABASE_PASSWORD"
   ```

3. **แก้ไขค่า:**
   - `password`: ใส่ password ของ Supabase database ของคุณ
     - หาได้ที่: Supabase Dashboard > Settings > Database > Database password
   - `host`: ตรวจสอบว่าเป็น Transaction Pooler (port 6543)
   - `user`: ตรวจสอบว่าเป็น `postgres.PROJECT_REF` (ไม่ใช่แค่ `postgres`)

4. **คลิก "Save"**

### ขั้นตอนที่ 3: Restart App

1. **ไปที่ App Settings**
2. **คลิก "Reboot app"** หรือ **"Redeploy"**
3. **รอให้ app restart** (ประมาณ 1-2 นาที)

### ขั้นตอนที่ 4: ตรวจสอบ Logs

1. **ไปที่ App**
2. **คลิก "Manage app"** (มุมล่างขวา)
3. **เลือก "Logs"**
4. **ตรวจสอบ debug messages:**

   ✅ **ถ้าถูกต้อง** จะเห็น:
   ```
   [DEBUG] 🌐 Running on Streamlit Cloud - checking for database secrets...
   [DEBUG] Reading database config from Streamlit secrets:
   [DEBUG]   type: postgresql
   [DEBUG]   host: aws-1-ap-southeast-1.pooler.supabase.com
   [DEBUG]   port: 6543
   [DEBUG]   user: postgres.thvvvsyujfzntvepmvzo
   [DEBUG]   database: postgres
   [DEBUG] ✅ Using PostgreSQL connection: postgresql://postgres.thvvvsyujfzntvepmvzo:***@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```

   ❌ **ถ้ายังไม่ถูกต้อง** จะเห็น:
   ```
   [DEBUG] ⚠️ 'database' not found in st.secrets
   [DEBUG] Available secrets keys: [...]
   ⚠️ WARNING: Using SQLite in /tmp - data will be LOST on restart!
   ```

## 🔍 วิธีหาข้อมูล Supabase

### 1. หา Database Password
- ไปที่ Supabase Dashboard
- Settings > Database
- ดูที่ "Database password"
- ถ้าลืม password: คลิก "Reset database password"

### 2. หา Connection Info (Transaction Pooler)
- ไปที่ Supabase Dashboard
- Settings > Database
- ดูที่ "Connection string" > "Transaction mode"
- หรือดูที่ "Connection pooling" > "Transaction mode"
- ควรจะเป็น:
  ```
  Host: aws-1-ap-southeast-1.pooler.supabase.com
  Port: 6543
  User: postgres.thvvvsyujfzntvepmvzo
  Database: postgres
  ```

## ⚠️ ข้อผิดพลาดที่พบบ่อย

### 1. ใช้ Direct Connection (port 5432)
❌ **ผิด:**
```toml
host = "db.thvvvsyujfzntvepmvzo.supabase.co"
port = 5432
```

✅ **ถูกต้อง:**
```toml
host = "aws-1-ap-southeast-1.pooler.supabase.com"
port = 6543
```

### 2. ใช้ user ผิด
❌ **ผิด:**
```toml
user = "postgres"
```

✅ **ถูกต้อง:**
```toml
user = "postgres.thvvvsyujfzntvepmvzo"
```

### 3. ไม่มี `[database]` section
❌ **ผิด:** ไม่มี section เลย หรือมีแต่ section อื่น

✅ **ถูกต้อง:** ต้องมี `[database]` section พร้อมทุก field

## 📝 ตัวอย่าง Secrets ที่ถูกต้อง

```toml
[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"
port = 6543
user = "postgres.thvvvsyujfzntvepmvzo"
database = "postgres"
password = "your_actual_password_here"

[supabase]
url = "https://thvvvsyujfzntvepmvzo.supabase.co"
publishable_key = "sb_publishable_kvb5ahfcTvBjAhweDea-CA_xD1leVIa"
```

## ✅ ตรวจสอบว่าเชื่อมต่อได้แล้ว

หลังจาก restart app แล้ว:

1. **ไปที่หน้า "⚙️ ตั้งค่า"**
2. **ดูที่ debug messages** (ถ้ามี)
3. **ลองสร้างข้อมูล Mockup** - ถ้าสำเร็จแสดงว่าเชื่อมต่อได้แล้ว
4. **ตรวจสอบ Supabase Dashboard** - ดูว่ามีตารางและข้อมูลหรือไม่

## 💡 Tips

- **อย่าลืม restart app** หลังจากแก้ไข secrets
- **ตรวจสอบ logs** เป็นประจำ
- **ใช้ Transaction Pooler** (port 6543) เสมอสำหรับ Streamlit Cloud
- **อย่าใช้ Direct Connection** (port 5432) เพราะจะ fail

## 📞 ถ้ายังมีปัญหา

1. ตรวจสอบ logs ใน Streamlit Cloud
2. ตรวจสอบ Supabase Dashboard ว่า database ทำงานปกติหรือไม่
3. ดูคู่มือ: `คู่มือตั้งค่า_Streamlit_Cloud_Supabase.md`
4. ดูคู่มือ: `วิธีแก้ปัญหา_Database_Connection_Error.md`

