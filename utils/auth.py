"""
Authentication Helper Functions
ฟังก์ชันช่วยสำหรับการตรวจสอบ authentication และ redirect
"""

import streamlit as st
from typing import Optional

def check_persistent_login():
    """
    ตรวจสอบว่ามี persistent login หรือไม่ และ auto-login ถ้ามี
    """
    # ตรวจสอบว่ามี remember_token ใน session_state หรือไม่
    remember_token = st.session_state.get('remember_token')
    
    if remember_token and not st.session_state.get('authenticated', False):
        from utils.persistent_login import get_user_from_token
        user_data = get_user_from_token(remember_token)
        
        if user_data:
            # Auto-login
            st.session_state.authenticated = True
            st.session_state.user_id = user_data['id']
            st.session_state.username = user_data['username']
            st.session_state.role = user_data['role']
            from datetime import datetime
            st.session_state.last_activity = datetime.now()
            return True
    
    # ถ้าไม่มี token ใน session_state ให้ตรวจสอบจาก database (สำหรับกรณีที่ refresh)
    if not st.session_state.get('authenticated', False):
        from utils.persistent_login import get_saved_username
        from database.db import get_session
        from database.models import SavedLogin
        from datetime import datetime
        
        saved_username = get_saved_username()
        if saved_username:
            session = get_session()
            try:
                # หา saved login ที่ active ล่าสุด
                saved_login = session.query(SavedLogin).filter(
                    SavedLogin.username == saved_username,
                    SavedLogin.is_active == True
                ).order_by(SavedLogin.last_used_at.desc()).first()
                
                if saved_login:
                    # ตรวจสอบว่าหมดอายุหรือไม่
                    if not saved_login.expires_at or saved_login.expires_at > datetime.now():
                        # ใช้ token นี้เพื่อ auto-login
                        st.session_state.remember_token = saved_login.remember_token
                        from utils.persistent_login import get_user_from_token
                        user_data = get_user_from_token(saved_login.remember_token)
                        
                        if user_data:
                            # Auto-login
                            st.session_state.authenticated = True
                            st.session_state.user_id = user_data['id']
                            st.session_state.username = user_data['username']
                            st.session_state.role = user_data['role']
                            st.session_state.last_activity = datetime.now()
                            return True
            finally:
                session.close()
    
    return False

def require_auth(redirect_to_login: bool = True) -> bool:
    """
    ตรวจสอบว่า user ได้ล็อคอินแล้วหรือไม่
    ถ้าไม่ได้ล็อคอินและ redirect_to_login=True จะแสดงหน้า login และหยุดการทำงาน
    
    Args:
        redirect_to_login: ถ้า True จะแสดงหน้า login และหยุดการทำงาน
    
    Returns:
        True ถ้า authenticated, False ถ้าไม่ได้ authenticated
    """
    # ตรวจสอบ persistent login ก่อน
    if not st.session_state.get('authenticated', False):
        check_persistent_login()
    
    # ตรวจสอบ authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        if redirect_to_login:
            # แสดงหน้า login และหยุดการทำงาน
            show_login_page()
            st.stop()
        return False
    return True

def show_login_page():
    """
    แสดงหน้า login
    """
    st.title("🔐 เข้าสู่ระบบ POS")
    st.warning("⚠️ กรุณาเข้าสู่ระบบก่อนใช้งาน")
    
    # Load saved username if exists
    from utils.persistent_login import get_saved_username
    saved_username = get_saved_username()
    
    with st.form("login_form"):
        username = st.text_input("ชื่อผู้ใช้", value=saved_username)
        password = st.text_input("รหัสผ่าน", type="password")
        remember_me = st.checkbox("💾 จดจำการล็อคอิน", value=st.session_state.get('remember_me', False))
        submit = st.form_submit_button("เข้าสู่ระบบ", type="primary", use_container_width=True)
        
        if submit:
            if username and password:
                # Import here to avoid circular import
                from utils.security import check_login_rate_limit, record_login_attempt
                from utils.validators import validate_username
                from database.db import get_session
                from database.models import User
                from datetime import datetime
                import bcrypt
                
                # Check rate limiting
                can_login, rate_limit_msg = check_login_rate_limit(username)
                if not can_login:
                    st.error(f"❌ {rate_limit_msg}")
                    return
                
                # Validate input
                username_valid, username_error = validate_username(username)
                if not username_valid:
                    st.error(f"❌ {username_error}")
                    record_login_attempt(username, False)
                    return
                
                session = get_session()
                try:
                    user = session.query(User).filter(User.username == username).first()
                    
                    # Verify password
                    def verify_password(password: str, hashed: str) -> bool:
                        """Verify password against hash"""
                        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
                    
                    if user and verify_password(password, user.password_hash):
                        record_login_attempt(username, True)
                        st.session_state.authenticated = True
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.role = user.role
                        st.session_state.last_activity = datetime.now()
                        
                        # Save persistent login if remember me is checked
                        if remember_me:
                            from utils.persistent_login import save_login, set_saved_username
                            remember_token = save_login(user.id, user.username, remember_forever=True)
                            if remember_token:
                                st.session_state.remember_token = remember_token
                                st.session_state.remember_me = True
                                set_saved_username(user.username)  # บันทึก username ล่าสุด
                        else:
                            # Clear any existing saved login
                            from utils.persistent_login import clear_saved_login
                            clear_saved_login(user_id=user.id)
                            if 'remember_token' in st.session_state:
                                del st.session_state.remember_token
                            st.session_state.remember_me = False
                        
                        st.success(f"✅ ยินดีต้อนรับ {user.username}!")
                        st.rerun()
                    else:
                        record_login_attempt(username, False)
                        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                except Exception as e:
                    record_login_attempt(username, False)
                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                finally:
                    session.close()
            else:
                st.warning("⚠️ กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")

def require_role(required_role: str, redirect_to_login: bool = True) -> bool:
    """
    ตรวจสอบว่า user มี role ที่ต้องการหรือไม่
    
    Args:
        required_role: role ที่ต้องการ ('admin' หรือ 'staff')
        redirect_to_login: ถ้า True จะแสดงหน้า login และหยุดการทำงาน
    
    Returns:
        True ถ้ามี role ที่ต้องการ, False ถ้าไม่มี
    """
    # ตรวจสอบ authentication ก่อน
    if not require_auth(redirect_to_login):
        return False
    
    # ตรวจสอบ role
    user_role = st.session_state.get('role', '')
    if user_role != required_role:
        st.error(f"❌ เฉพาะผู้ที่มีบทบาท '{required_role}' เท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        st.info(f"💡 บทบาทปัจจุบันของคุณ: {user_role}")
        st.stop()
        return False
    
    return True

