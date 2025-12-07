# 📊 เปรียบเทียบ Connection Methods สำหรับ Supabase

## 🎯 เลือกใช้ Connection Method ตาม Environment

### ✅ สำหรับ Streamlit Cloud (Serverless) - **แนะนำ: Transaction Pooler**

### ✅ สำหรับ Local Development (มี IPv6) - **ใช้ Direct Connection ได้**

### ✅ สำหรับ Local Development (ไม่มี IPv6) - **ใช้ Session Pooler**

---

## 📋 เปรียบเทียบ Connection Methods

| Method | Port | Host Format | User Format | IPv6 | IPv4 | เหมาะสำหรับ |
|--------|------|-------------|-------------|------|------|------------|
| **Direct Connection** | 5432 | `db.xxxxx.supabase.co` | `postgres` | ✅ | ❌ | Local (มี IPv6), VMs, Containers |
| **Transaction Pooler** | 6543 | `aws-X-REGION.pooler.supabase.com` | `postgres.PROJECT_REF` | ✅ | ✅ | **Serverless/Edge** ⭐ |
| **Session Pooler** | 5432 | `aws-X-REGION.pooler.supabase.com` | `postgres.PROJECT_REF` | ✅ | ✅ | Persistent Backend |

---

## 🔍 ตัวอย่างข้อมูลจาก Supabase Dashboard

### 1. Direct Connection (สำหรับ Local Development)

**จาก Supabase Dashboard > Connect > Direct connection:**

```
Host: db.thvvvsyujfzntvepmvzo.supabase.co
Port: 5432
User: postgres
Database: postgres
Password: [YOUR_PASSWORD]
```

**Connection String:**
```
postgresql://postgres:[YOUR_PASSWORD]@db.thvvvsyujfzntvepmvzo.supabase.co:5432/postgres
```

**⚠️ ข้อจำกัด:**
- ใช้ IPv6 เท่านั้น
- **ไม่รองรับ IPv4** (ต้องซื้อ IPv4 add-on)
- **ไม่เหมาะสำหรับ Streamlit Cloud**

---

### 2. Transaction Pooler (สำหรับ Streamlit Cloud) ⭐

**จาก Supabase Dashboard > Connect > Transaction mode:**

```
Host: aws-1-ap-southeast-1.pooler.supabase.com
Port: 6543
User: postgres.thvvvsyujfzntvepmvzo
Database: postgres
Password: [YOUR_PASSWORD]
Pool Mode: transaction
```

**Connection String:**
```
postgresql://postgres.thvvvsyujfzntvepmvzo:[YOUR_PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

**✅ ข้อดี:**
- รองรับทั้ง IPv4 และ IPv6
- เหมาะสำหรับ serverless/edge functions
- Connection pooling อัตโนมัติ
- **ฟรี** (Shared Pooler)

**⚠️ ข้อจำกัด:**
- ไม่รองรับ PREPARE statements (SQLAlchemy จัดการให้อัตโนมัติ)

---

### 3. Session Pooler (สำหรับ Persistent Backend)

**จาก Supabase Dashboard > Connect > Session mode:**

```
Host: aws-1-ap-southeast-1.pooler.supabase.com
Port: 5432
User: postgres.thvvvsyujfzntvepmvzo
Database: postgres
Password: [YOUR_PASSWORD]
Pool Mode: session
```

**✅ ข้อดี:**
- รองรับทั้ง IPv4 และ IPv6
- รองรับ PREPARE statements
- เหมาะสำหรับ persistent backend

---

## 🎯 คำแนะนำการเลือกใช้

### สำหรับ Streamlit Cloud:
```toml
[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"  # Transaction pooler
port = 6543  # Transaction mode
user = "postgres.thvvvsyujfzntvepmvzo"  # postgres.PROJECT_REF
password = "your-password"
database = "postgres"
```

### สำหรับ Local Development (มี IPv6):
```toml
[database]
type = "postgresql"
host = "db.thvvvsyujfzntvepmvzo.supabase.co"  # Direct connection
port = 5432  # Direct connection
user = "postgres"  # postgres
password = "your-password"
database = "postgres"
```

### สำหรับ Local Development (ไม่มี IPv6):
```toml
[database]
type = "postgresql"
host = "aws-1-ap-southeast-1.pooler.supabase.com"  # Session pooler
port = 5432  # Session mode
user = "postgres.thvvvsyujfzntvepmvzo"  # postgres.PROJECT_REF
password = "your-password"
database = "postgres"
```

---

## 📖 อ่านเพิ่มเติม

- [Supabase Connection Pooler Documentation](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Connection Management](https://supabase.com/docs/guides/database/managing-connections)
- [Troubleshooting Connection Issues](https://supabase.com/docs/guides/database/connecting-to-postgres#troubleshooting-and-postgres-connection-string-faqs)

---

## ✅ สรุป

**สำหรับ Streamlit Cloud:**
- ✅ ใช้ **Transaction Pooler** (port 6543) - **แนะนำที่สุด**
- ❌ **อย่าใช้ Direct Connection** (port 5432) - จะ error เพราะไม่รองรับ IPv6

**สำหรับ Local Development:**
- ✅ ใช้ **Direct Connection** (port 5432) - ถ้า network รองรับ IPv6
- ✅ ใช้ **Session Pooler** (port 5432) - ถ้า network ไม่รองรับ IPv6

