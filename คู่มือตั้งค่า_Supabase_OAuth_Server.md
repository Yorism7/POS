# 🔐 คู่มือตั้งค่า Supabase OAuth Server

## 🎯 เป้าหมาย

ตั้งค่า Supabase OAuth Server เพื่อให้ระบบ POS ทำหน้าที่เป็น **Identity Provider (OAuth Server)** สำหรับแอปพลิเคชันอื่นๆ

## ⚠️ หมายเหตุสำคัญ

**Supabase OAuth Server** หมายถึง:
- ✅ ระบบ POS ของคุณสามารถทำหน้าที่เป็น **OAuth Provider** ได้
- ✅ แอปพลิเคชันอื่นๆ สามารถใช้ระบบ POS ของคุณเพื่อ login ได้
- ✅ รองรับ OAuth 2.0 standard

## 🚀 วิธีตั้งค่า

### ขั้นตอนที่ 1: เปิดใช้งาน OAuth Server

1. ไปที่ **Supabase Dashboard**
2. เลือก **Project** ของคุณ
3. ไปที่ **Authentication** > **OAuth Server**
4. กด **"Enable the Supabase OAuth Server"**
5. ตั้งค่า:
   - **Site URL**: `https://pos-ez.streamlit.app` (URL ของ Streamlit app)
   - **Authorization Path**: `/oauth/consent` (path สำหรับ consent screen)
   - **Allow Dynamic OAuth Apps**: (เปิดถ้าต้องการให้ register apps แบบ dynamic)

### ขั้นตอนที่ 2: สร้าง OAuth Application

1. ไปที่ **Authentication** > **OAuth Apps**
2. กด **"New OAuth App"**
3. ตั้งค่า:
   - **Name**: ชื่อแอปพลิเคชัน (เช่น "Mobile App", "Admin Panel")
   - **Redirect URIs**: 
     ```
     https://your-app.com/callback
     https://your-app.com/auth/callback
     ```
   - **Scopes**: เลือก permissions ที่ต้องการ
4. บันทึก
5. **คัดลอก Client ID และ Client Secret** (จะใช้ในแอปพลิเคชันอื่นๆ)

### ขั้นตอนที่ 3: สร้าง Consent Screen ใน Streamlit

สร้างหน้า `/oauth/consent` ใน Streamlit app:

```python
# pages/oauth_consent.py หรือสร้าง route ใน app.py
import streamlit as st
from utils.supabase_auth import get_supabase_client

def oauth_consent():
    """OAuth consent screen"""
    st.title("🔐 Authorization Request")
    
    # Get OAuth parameters from query string
    query_params = st.experimental_get_query_params()
    client_id = query_params.get('client_id', [None])[0]
    redirect_uri = query_params.get('redirect_uri', [None])[0]
    scope = query_params.get('scope', [None])[0]
    state = query_params.get('state', [None])[0]
    
    if not client_id or not redirect_uri:
        st.error("❌ Invalid OAuth request")
        return
    
    # Check if user is authenticated
    supabase = get_supabase_client()
    if not supabase:
        st.error("❌ Supabase not configured")
        return
    
    user = supabase.auth.get_user()
    if not user:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        from utils.supabase_auth import show_supabase_login_page
        show_supabase_login_page()
        return
    
    # Show consent screen
    st.info(f"**แอปพลิเคชัน:** {client_id}")
    st.info(f"**ต้องการเข้าถึง:** {scope or 'basic profile'}")
    st.info(f"**Redirect to:** {redirect_uri}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ อนุญาต", type="primary", use_container_width=True):
            # Generate authorization code
            # Redirect to redirect_uri with code
            code = generate_authorization_code(client_id, user.user.id)
            redirect_url = f"{redirect_uri}?code={code}&state={state}"
            st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_url}">', unsafe_allow_html=True)
    
    with col2:
        if st.button("❌ ปฏิเสธ", use_container_width=True):
            error_url = f"{redirect_uri}?error=access_denied&state={state}"
            st.markdown(f'<meta http-equiv="refresh" content="0; url={error_url}">', unsafe_allow_html=True)
```

### ขั้นตอนที่ 4: สร้าง Authorization Code Endpoint

```python
def generate_authorization_code(client_id: str, user_id: str) -> str:
    """Generate OAuth authorization code"""
    import secrets
    import hashlib
    from datetime import datetime, timedelta
    
    # Generate code
    code = secrets.token_urlsafe(32)
    
    # Store in database (with expiration)
    # TODO: Store code in database with client_id, user_id, expiration
    
    return code
```

### ขั้นตอนที่ 5: สร้าง Token Endpoint

```python
def exchange_code_for_token(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange authorization code for access token"""
    # Verify code
    # Verify client_id and client_secret
    # Generate access token
    # Return token
    pass
```

## 📋 OAuth Flow

### 1. Authorization Request
```
Client App → https://pos-ez.streamlit.app/oauth/consent?client_id=xxx&redirect_uri=yyy
```

### 2. User Consent
```
User → Login (if not authenticated)
User → Approve/Deny access
```

### 3. Authorization Code
```
Redirect → https://client-app.com/callback?code=xxx&state=yyy
```

### 4. Token Exchange
```
Client App → POST /oauth/token
Body: {
  "code": "xxx",
  "client_id": "yyy",
  "client_secret": "zzz",
  "grant_type": "authorization_code"
}
```

### 5. Access Token
```
Response: {
  "access_token": "xxx",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

## 🔒 Security

### ✅ Best Practices:
1. **Validate redirect_uri** - ตรวจสอบว่า redirect_uri อยู่ใน whitelist
2. **Use HTTPS** - ใช้ HTTPS เสมอ
3. **Short-lived codes** - Authorization code ควร expire เร็ว (10 นาที)
4. **Secure tokens** - ใช้ strong random tokens
5. **Validate client** - ตรวจสอบ client_id และ client_secret

## 📝 ตัวอย่างการใช้งาน

### สำหรับ Client Application:

```python
# 1. Redirect user to authorization endpoint
auth_url = "https://pos-ez.streamlit.app/oauth/consent"
params = {
    "client_id": "your-client-id",
    "redirect_uri": "https://your-app.com/callback",
    "response_type": "code",
    "scope": "read write",
    "state": "random-state-string"
}
redirect_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

# 2. User approves → Get authorization code
# 3. Exchange code for token
token_response = requests.post("https://pos-ez.streamlit.app/oauth/token", data={
    "code": authorization_code,
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "grant_type": "authorization_code"
})

# 4. Use access token
access_token = token_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
```

## 🎯 สรุป

### ✅ Supabase OAuth Server:
- ระบบ POS ทำหน้าที่เป็น **OAuth Provider**
- แอปพลิเคชันอื่นๆ สามารถใช้ระบบ POS เพื่อ login ได้
- รองรับ OAuth 2.0 standard

### ⚠️ ข้อควรระวัง:
1. ต้องสร้าง consent screen ใน Streamlit
2. ต้องสร้าง token endpoint
3. ต้องจัดการ authorization codes
4. ต้อง validate clients

**แนะนำ: ใช้ Supabase OAuth Server สำหรับ production!**

