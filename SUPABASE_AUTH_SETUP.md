# 🔐 คู่มือตั้งค่า Supabase Auth + OAuth

## 🎯 เป้าหมาย

ใช้ Supabase Auth สำหรับ authentication แทนการทำเอง:
- ✅ Email/Password authentication
- ✅ OAuth providers (Google, GitHub, Discord, etc.)
- ✅ Row Level Security (RLS)
- ✅ Session management
- ✅ User management

## 🚀 วิธีตั้งค่า

### ขั้นตอนที่ 1: ตั้งค่า OAuth Providers ใน Supabase

#### 1.1 ไปที่ Supabase Dashboard
1. ไปที่ https://supabase.com
2. เลือก Project ของคุณ
3. ไปที่ **Authentication** > **Providers**

#### 1.2 ตั้งค่า Google OAuth
1. กด **Google** provider
2. เปิดใช้งาน (Enable)
3. ไปที่ [Google Cloud Console](https://console.cloud.google.com)
4. สร้าง OAuth 2.0 Client ID:
   - **Application type**: Web application
   - **Authorized redirect URIs**: 
     ```
     https://your-project.supabase.co/auth/v1/callback
     ```
5. คัดลอก **Client ID** และ **Client Secret**
6. วางใน Supabase Dashboard
7. บันทึก

#### 1.3 ตั้งค่า GitHub OAuth
1. กด **GitHub** provider
2. เปิดใช้งาน (Enable)
3. ไปที่ [GitHub Developer Settings](https://github.com/settings/developers)
4. สร้าง OAuth App:
   - **Application name**: POS System
   - **Homepage URL**: `https://your-app.streamlit.app`
   - **Authorization callback URL**: 
     ```
     https://your-project.supabase.co/auth/v1/callback
     ```
5. คัดลอก **Client ID** และ **Client Secret**
6. วางใน Supabase Dashboard
7. บันทึก

### ขั้นตอนที่ 2: ตั้งค่า Supabase Secrets ใน Streamlit Cloud

1. ไปที่ **Supabase Dashboard** > **Settings** > **API**
2. คัดลอกข้อมูล:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
3. ไปที่ **Streamlit Cloud** > **Settings** > **Secrets**
4. เพิ่ม secrets:
   ```toml
   [supabase]
   url = "https://xxxxx.supabase.co"
   anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   redirect_url = "https://your-app.streamlit.app/auth/callback"
   
   [database]
   type = "postgresql"
   host = "db.xxxxx.supabase.co"
   port = 5432
   user = "postgres"
   password = "your-password"
   database = "postgres"
   ```

### ขั้นตอนที่ 3: ตั้งค่า Row Level Security (RLS)

#### 3.1 เปิดใช้งาน RLS
1. ไปที่ **Supabase Dashboard** > **Database** > **Tables**
2. เลือกตารางที่ต้องการ (เช่น `users`, `sales`)
3. ไปที่ **Policies**
4. กด **Enable RLS**

#### 3.2 สร้าง Policies
```sql
-- ตัวอย่าง: ให้ users อ่านข้อมูลของตัวเองได้
CREATE POLICY "Users can read own data"
ON users FOR SELECT
USING (auth.uid() = id);

-- ตัวอย่าง: ให้ admin อ่านข้อมูลทั้งหมดได้
CREATE POLICY "Admins can read all"
ON users FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);
```

### ขั้นตอนที่ 4: แก้ไขโค้ดให้ใช้ Supabase Auth

#### 4.1 แก้ไข `app.py`
```python
# แทนที่
from utils.auth import require_auth, show_login_page

# ด้วย
from utils.supabase_auth import require_supabase_auth, show_supabase_login_page
```

#### 4.2 แก้ไขทุกหน้า
```python
# แทนที่
from utils.auth import require_auth

# ด้วย
from utils.supabase_auth import require_supabase_auth

# และเปลี่ยน
require_auth()

# เป็น
require_supabase_auth()
```

## 📋 OAuth Providers ที่รองรับ

### ✅ รองรับ:
- **Google** - ต้องตั้งค่าใน Google Cloud Console
- **GitHub** - ต้องตั้งค่าใน GitHub Developer Settings
- **Discord** - ต้องตั้งค่าใน Discord Developer Portal
- **Facebook** - ต้องตั้งค่าใน Facebook Developers
- **Apple** - ต้องตั้งค่าใน Apple Developer
- **Twitter** - ต้องตั้งค่าใน Twitter Developer Portal
- **LinkedIn** - ต้องตั้งค่าใน LinkedIn Developer Portal

### ⚠️ ข้อควรระวัง:
- ต้องตั้งค่า OAuth providers ใน Supabase Dashboard ก่อนใช้งาน
- ต้องตั้งค่า redirect URLs ให้ถูกต้อง
- ต้องมี Client ID และ Client Secret

## 🔒 Security

### ✅ ข้อดี:
- **Supabase จัดการ security** - ไม่ต้องทำเอง
- **Session management** - Supabase จัดการให้
- **Password hashing** - Supabase จัดการให้
- **OAuth flow** - Supabase จัดการให้
- **Row Level Security** - ควบคุม access ได้ละเอียด

### ⚠️ ข้อควรระวัง:
- ใช้ **anon key** สำหรับ client-side
- ใช้ **service role key** เฉพาะ server-side (อย่า expose!)
- ตั้งค่า **RLS policies** ให้ถูกต้อง
- ใช้ **strong passwords**

## 📊 เปรียบเทียบ

| ฟีเจอร์ | Custom Auth | Supabase Auth |
|---------|-------------|---------------|
| Email/Password | ✅ | ✅ |
| OAuth | ❌ | ✅ |
| Session Management | ⚠️ | ✅ |
| Password Security | ⚠️ | ✅ |
| User Management | ⚠️ | ✅ |
| RLS | ❌ | ✅ |
| ง่าย | ⚠️ | ✅ |

## 🎯 สรุป

### ✅ ข้อดีของ Supabase Auth:
1. **รองรับ OAuth** - Google, GitHub, etc.
2. **Security** - Supabase จัดการให้
3. **ง่าย** - ไม่ต้องทำเอง
4. **RLS** - ควบคุม access ได้ละเอียด

### ⚠️ ข้อควรระวัง:
1. ต้องตั้งค่า OAuth providers ก่อน
2. ต้องตั้งค่า RLS policies
3. ต้องใช้ secrets อย่างปลอดภัย

**แนะนำ: ใช้ Supabase Auth สำหรับ production!**

