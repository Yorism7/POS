# 🔧 วิธีแก้ปัญหา Database Connection Error

## ❌ ปัญหาที่พบ:

```
OperationalError: connection to server at "db.xxxxx.supabase.co" 
(2406:da18:243:7416:b575:fac0:a960:9fcf), port 5432 failed: 
Cannot assign requested address
```

## 🔍 สาเหตุ:

**Streamlit Cloud ไม่รองรับ IPv6** แต่ Supabase Direct Connection ใช้ IPv6 เป็น default

ตามเอกสาร Supabase: [Connecting to Postgres - Connection Pooler](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

## ✅ วิธีแก้ไข:

### วิธีที่ 1: ใช้ Connection Pooler (Transaction Mode) - **แนะนำ**

Transaction Mode เหมาะสำหรับ **serverless/edge functions** เช่น Streamlit Cloud

#### ขั้นตอน:

1. **ไปที่ Supabase Dashboard**
   - ไปที่ https://supabase.com
   - เลือก Project ของคุณ
   - ไปที่ **Settings** > **Database**

2. **หา Connection Pooler URL**
   - กดปุ่ม **"Connect"** (ด้านบนของหน้า)
   - เลือก **"Transaction mode"** (port 6543)
   - คัดลอก Connection string หรือแยกข้อมูล:
     - **Host**: `db.xxxxx.supabase.co` (เหมือนเดิม)
     - **Port**: `6543` (Transaction mode)
     - **User**: `postgres`
     - **Password**: (รหัสผ่าน Database)
     - **Database**: `postgres`

3. **อัปเดต Streamlit Cloud Secrets**
   ```toml
   [database]
   type = "postgresql"
   host = "db.thvvvsyujfzntvepmvzo.supabase.co"
   port = 6543  # ⬅️ เปลี่ยนเป็น 6543 สำหรับ Transaction mode
   user = "postgres"
   password = "your-actual-password"
   database = "postgres"
   ```

4. **Save และ Deploy อีกครั้ง**

---

### วิธีที่ 2: ใช้ Connection Pooler (Session Mode)

Session Mode เหมาะสำหรับ **persistent backend** ที่ต้องการ IPv4

#### ขั้นตอน:

1. **ไปที่ Supabase Dashboard** > **Settings** > **Database**
2. **กด "Connect"** > เลือก **"Session mode"** (port 5432)
3. **อัปเดต Streamlit Cloud Secrets:**
   ```toml
   [database]
   type = "postgresql"
   host = "db.thvvvsyujfzntvepmvzo.supabase.co"
   port = 5432  # ⬅️ Session mode (ยังใช้ port 5432)
   user = "postgres"
   password = "your-actual-password"
   database = "postgres"
   ```

---

## 📊 เปรียบเทียบ Connection Methods:

| Method | Port | IPv6 | IPv4 | เหมาะสำหรับ |
|--------|------|------|------|------------|
| **Direct Connection** | 5432 | ✅ | ❌ | Persistent servers (VMs, containers) |
| **Session Mode Pooler** | 5432 | ✅ | ✅ | Persistent backend ที่ต้องการ IPv4 |
| **Transaction Mode Pooler** | 6543 | ✅ | ✅ | **Serverless/Edge functions** ⭐ |

---

## ⚠️ หมายเหตุสำคัญ:

### Transaction Mode Pooler:
- ✅ รองรับทั้ง IPv4 และ IPv6
- ✅ เหมาะสำหรับ serverless/edge functions
- ✅ Connection pooling อัตโนมัติ
- ⚠️ **ไม่รองรับ Prepared Statements** (SQLAlchemy จะจัดการให้อัตโนมัติ)

### Session Mode Pooler:
- ✅ รองรับทั้ง IPv4 และ IPv6
- ✅ รองรับ Prepared Statements
- ✅ เหมาะสำหรับ persistent backend

---

## 🔍 วิธีตรวจสอบว่าใช้ Connection Pooler:

1. **ดู Connection String:**
   - Transaction mode: `postgres://postgres:[PASSWORD]@db.xxxxx.supabase.co:6543/postgres`
   - Session mode: `postgres://postgres.apbkobhfnmcqqzqeeqss:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`

2. **ดู Port:**
   - `6543` = Transaction mode pooler
   - `5432` = Direct connection หรือ Session mode pooler

---

## 📖 อ่านเพิ่มเติม:

- [Supabase Connection Pooler Documentation](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Connection Management](https://supabase.com/docs/guides/database/managing-connections)
- [Troubleshooting Connection Issues](https://supabase.com/docs/guides/database/connecting-to-postgres#troubleshooting-and-postgres-connection-string-faqs)

---

## ✅ Checklist:

- [ ] ไปที่ Supabase Dashboard > Settings > Database
- [ ] กด "Connect" button
- [ ] เลือก "Transaction mode" (port 6543)
- [ ] คัดลอก Connection string หรือแยกข้อมูล
- [ ] อัปเดต `port = 6543` ใน Streamlit Cloud Secrets
- [ ] ตรวจสอบ password ให้ถูกต้อง
- [ ] Save และ Deploy อีกครั้ง
- [ ] ตรวจสอบ logs ว่าเชื่อมต่อได้แล้ว

---

## 🎯 สรุป:

**สำหรับ Streamlit Cloud:**
- ✅ ใช้ **Transaction Mode Pooler** (port 6543) - **แนะนำที่สุด**
- หรือใช้ **Session Mode Pooler** (port 5432) - ถ้า transaction mode ไม่ได้
- ❌ **อย่าใช้ Direct Connection** (port 5432) - จะ error เพราะไม่รองรับ IPv6

