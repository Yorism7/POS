"""
Supabase Authentication Integration
ใช้ Supabase Auth สำหรับ authentication และ OAuth
รองรับ Email/Password และ OAuth providers (Google, GitHub, etc.)
"""

import streamlit as st
from typing import Optional, Dict, Any
import os

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

def get_supabase_client() -> Optional[Client]:
    """
    สร้าง Supabase client จาก Streamlit secrets หรือ environment variables
    รองรับทั้ง Publishable key (แบบใหม่) และ anon_key (แบบเก่า)
    
    Returns:
        Supabase Client หรือ None ถ้าไม่สามารถสร้างได้
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            supabase_config = st.secrets['supabase']
            url = supabase_config.get('url')
            
            # รองรับทั้ง publishable_key (แบบใหม่) และ anon_key (แบบเก่า)
            key = supabase_config.get('publishable_key') or supabase_config.get('anon_key')
            
            if url and key:
                return create_client(url, key)
        
        # Try environment variables
        url = os.environ.get('SUPABASE_URL')
        # รองรับทั้ง publishable_key และ anon_key
        key = os.environ.get('SUPABASE_PUBLISHABLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
        
        if url and key:
            return create_client(url, key)
        
        return None
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        return None

def supabase_login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Login ด้วย Email/Password ผ่าน Supabase Auth
    
    Args:
        email: Email address
        password: Password
    
    Returns:
        User data dict หรือ None ถ้า login ไม่สำเร็จ
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                'id': response.user.id,
                'email': response.user.email,
                'user_metadata': response.user.user_metadata or {},
                'session': response.session
            }
        return None
    except Exception as e:
        print(f"Supabase login error: {e}")
        return None

def supabase_signup(email: str, password: str, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    สมัครสมาชิกใหม่ผ่าน Supabase Auth
    
    Args:
        email: Email address
        password: Password
        metadata: Additional user metadata (เช่น username, role)
    
    Returns:
        User data dict หรือ None ถ้า signup ไม่สำเร็จ
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata or {}
            }
        })
        
        if response.user:
            return {
                'id': response.user.id,
                'email': response.user.email,
                'user_metadata': response.user.user_metadata or {}
            }
        return None
    except Exception as e:
        print(f"Supabase signup error: {e}")
        return None

def supabase_oauth_login(provider: str) -> str:
    """
    เริ่มต้น OAuth login flow (Google, GitHub, etc.)
    
    Args:
        provider: OAuth provider ('google', 'github', 'discord', etc.)
    
    Returns:
        OAuth URL สำหรับ redirect
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Get redirect URL
        redirect_url = st.secrets.get('supabase', {}).get('redirect_url', 
            os.environ.get('SUPABASE_REDIRECT_URL', 
            f"{st.get_option('server.baseUrlPath') or ''}/auth/callback"))
        
        response = supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": redirect_url
            }
        })
        
        return response.url
    except Exception as e:
        print(f"Supabase OAuth error: {e}")
        return None

def supabase_logout():
    """
    Logout จาก Supabase Auth
    """
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        print(f"Supabase logout error: {e}")
        return False

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    ดึงข้อมูล user ปัจจุบันจาก Supabase session
    
    Returns:
        User data dict หรือ None ถ้าไม่ได้ login
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        user = supabase.auth.get_user()
        if user:
            return {
                'id': user.user.id,
                'email': user.user.email,
                'user_metadata': user.user.user_metadata or {}
            }
        return None
    except Exception as e:
        print(f"Get current user error: {e}")
        return None

def require_supabase_auth(redirect_to_login: bool = True) -> bool:
    """
    ตรวจสอบว่า user ได้ล็อคอินผ่าน Supabase แล้วหรือไม่
    
    Args:
        redirect_to_login: ถ้า True จะแสดงหน้า login และหยุดการทำงาน
    
    Returns:
        True ถ้า authenticated, False ถ้าไม่ได้ authenticated
    """
    user = get_current_user()
    
    if not user:
        if redirect_to_login:
            show_supabase_login_page()
            st.stop()
        return False
    
    # Store in session state
    st.session_state.authenticated = True
    st.session_state.user_id = user['id']
    st.session_state.email = user['email']
    st.session_state.user_metadata = user.get('user_metadata', {})
    st.session_state.role = user.get('user_metadata', {}).get('role', 'staff')
    
    return True

def show_supabase_login_page():
    """
    แสดงหน้า login ที่รองรับ Supabase Auth และ OAuth
    """
    st.title("🔐 เข้าสู่ระบบ POS")
    
    if not SUPABASE_AVAILABLE:
        st.error("❌ Supabase client ไม่พร้อมใช้งาน")
        st.info("💡 กรุณาติดตั้ง: pip install supabase")
        st.info("💡 และตั้งค่า Supabase secrets ใน Streamlit Cloud")
        # Fallback to regular login
        from utils.auth import show_login_page
        show_login_page()
        return
    
    # Check if Supabase is configured
    supabase = get_supabase_client()
    if not supabase:
        st.warning("⚠️ ไม่พบ Supabase configuration - ใช้ระบบ login แบบเดิม")
        st.info("💡 ต้องการใช้ Supabase Auth? ตั้งค่า Supabase secrets ใน Streamlit Cloud")
        # Fallback to regular login
        from utils.auth import show_login_page
        show_login_page()
        return
    
    # Tabs for different login methods
    tab1, tab2 = st.tabs(["📧 Email/Password", "🔗 OAuth (Google, GitHub)"])
    
    with tab1:
        st.subheader("เข้าสู่ระบบด้วย Email/Password")
        
        with st.form("supabase_login_form"):
            email = st.text_input("📧 Email", placeholder="your@email.com")
            password = st.text_input("🔒 รหัสผ่าน", type="password")
            remember_me = st.checkbox("💾 จดจำการล็อคอิน")
            submit = st.form_submit_button("เข้าสู่ระบบ", type="primary", width='stretch')
            
            if submit:
                if email and password:
                    user = supabase_login(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user['id']
                        st.session_state.email = user['email']
                        st.session_state.user_metadata = user.get('user_metadata', {})
                        st.session_state.role = user.get('user_metadata', {}).get('role', 'staff')
                        
                        if remember_me:
                            st.session_state.remember_me = True
                            st.session_state.saved_email = user['email']
                        
                        st.success(f"✅ ยินดีต้อนรับ {user['email']}!")
                        st.rerun()
                    else:
                        st.error("❌ Email หรือรหัสผ่านไม่ถูกต้อง")
                else:
                    st.warning("⚠️ กรุณากรอก Email และรหัสผ่าน")
        
        # Sign up link
        st.divider()
        with st.expander("📝 ยังไม่มีบัญชี? สมัครสมาชิก"):
            with st.form("supabase_signup_form"):
                st.subheader("สมัครสมาชิก")
                new_email = st.text_input("📧 Email", key="signup_email", placeholder="your@email.com")
                new_password = st.text_input("🔒 รหัสผ่าน", type="password", key="signup_password")
                confirm_password = st.text_input("🔒 ยืนยันรหัสผ่าน", type="password", key="signup_confirm")
                username = st.text_input("👤 ชื่อผู้ใช้", key="signup_username")
                role = st.selectbox("🎭 บทบาท", ["staff", "admin"], key="signup_role")
                signup_submit = st.form_submit_button("สมัครสมาชิก", type="primary", width='stretch')
                
                if signup_submit:
                    if new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("❌ รหัสผ่านไม่ตรงกัน")
                        elif len(new_password) < 6:
                            st.error("❌ รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
                        else:
                            metadata = {}
                            if username:
                                metadata['username'] = username
                            metadata['role'] = role
                            
                            user = supabase_signup(new_email, new_password, metadata)
                            if user:
                                st.success("✅ สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
                            else:
                                st.error("❌ ไม่สามารถสมัครสมาชิกได้ (อาจมี Email นี้อยู่แล้ว)")
                    else:
                        st.warning("⚠️ กรุณากรอกข้อมูลให้ครบ")
    
    with tab2:
        st.subheader("เข้าสู่ระบบด้วย OAuth")
        st.info("💡 เลือกผู้ให้บริการ OAuth ที่ต้องการ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔵 Google", width='stretch', type="primary"):
                oauth_url = supabase_oauth_login('google')
                if oauth_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={oauth_url}">', unsafe_allow_html=True)
                    st.info("🔄 กำลัง redirect ไปยัง Google...")
                else:
                    st.error("❌ ไม่สามารถเริ่ม OAuth flow ได้")
        
        with col2:
            if st.button("⚫ GitHub", width='stretch', type="primary"):
                oauth_url = supabase_oauth_login('github')
                if oauth_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={oauth_url}">', unsafe_allow_html=True)
                    st.info("🔄 กำลัง redirect ไปยัง GitHub...")
                else:
                    st.error("❌ ไม่สามารถเริ่ม OAuth flow ได้")
        
        # Add more OAuth providers if needed
        st.info("💡 OAuth providers อื่นๆ: Discord, Facebook, Apple, Twitter, LinkedIn")
        st.warning("⚠️ ต้องตั้งค่า OAuth providers ใน Supabase Dashboard ก่อนใช้งาน")

