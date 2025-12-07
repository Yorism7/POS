"""
Persistent Login Management
จัดการการล็อคอินที่จดจำไว้ถาวร
"""

from database.db import get_session, engine
from database.models import User, SavedLogin
from datetime import datetime, timedelta
import secrets
import hashlib

def ensure_saved_logins_table():
    """
    ตรวจสอบและสร้าง table saved_logins ถ้ายังไม่มี
    """
    try:
        # Try to query to check if table exists
        session = get_session()
        try:
            session.query(SavedLogin).limit(1).all()
            session.close()
            return True
        except Exception as e:
            session.close()
            error_msg = str(e).lower()
            if 'does not exist' in error_msg or 'no such table' in error_msg or 'relation' in error_msg or 'undefinedtable' in error_msg:
                print(f"[INFO] Creating saved_logins table...")
                SavedLogin.__table__.create(bind=engine, checkfirst=True)
                print(f"[INFO] ✅ saved_logins table created successfully")
                return True
            else:
                raise
    except Exception as e:
        print(f"[ERROR] Failed to ensure saved_logins table: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_remember_token() -> str:
    """
    สร้าง remember token สำหรับ auto-login
    
    Returns:
        Token string
    """
    return secrets.token_urlsafe(32)

def save_login(user_id: int, username: str, remember_forever: bool = True) -> str:
    """
    บันทึกการล็อคอินเพื่อจดจำไว้ถาวร
    
    Args:
        user_id: ID ของ user
        username: Username ของ user
        remember_forever: ถ้า True จะไม่หมดอายุ, ถ้า False จะหมดอายุใน 30 วัน
    
    Returns:
        Remember token
    """
    # Ensure table exists first
    ensure_saved_logins_table()
    
    session = get_session()
    try:
        # ลบ saved login เก่าของ user นี้ (ถ้ามี)
        old_logins = session.query(SavedLogin).filter(
            SavedLogin.user_id == user_id,
            SavedLogin.is_active == True
        ).all()
        for old_login in old_logins:
            old_login.is_active = False
        
        # สร้าง saved login ใหม่
        remember_token = generate_remember_token()
        expires_at = None if remember_forever else datetime.now() + timedelta(days=30)
        
        saved_login = SavedLogin(
            user_id=user_id,
            username=username,
            remember_token=remember_token,
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.now(),
            last_used_at=datetime.now()
        )
        
        session.add(saved_login)
        session.commit()
        
        return remember_token
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to save login: {e}")
        return None
    finally:
        session.close()

def get_user_from_token(remember_token: str) -> dict:
    """
    ดึงข้อมูล user จาก remember token
    
    Args:
        remember_token: Remember token
    
    Returns:
        Dictionary ของ user data หรือ None ถ้าไม่พบหรือหมดอายุ
    """
    if not remember_token:
        return None
    
    # Ensure table exists first
    ensure_saved_logins_table()
    
    session = get_session()
    try:
        saved_login = session.query(SavedLogin).filter(
            SavedLogin.remember_token == remember_token,
            SavedLogin.is_active == True
        ).first()
        
        if not saved_login:
            return None
        
        # ตรวจสอบว่าหมดอายุหรือไม่
        if saved_login.expires_at and saved_login.expires_at < datetime.now():
            saved_login.is_active = False
            session.commit()
            return None
        
        # อัพเดท last_used_at
        saved_login.last_used_at = datetime.now()
        session.commit()
        
        # ดึงข้อมูล user
        user = session.query(User).filter(User.id == saved_login.user_id).first()
        if not user:
            return None
        
        return {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    except Exception as e:
        print(f"[ERROR] Failed to get user from token: {e}")
        return None
    finally:
        session.close()

def clear_saved_login(user_id: int = None, remember_token: str = None):
    """
    ลบ saved login
    
    Args:
        user_id: ID ของ user (ถ้าต้องการลบทั้งหมดของ user)
        remember_token: Remember token (ถ้าต้องการลบเฉพาะ token นี้)
    """
    session = get_session()
    try:
        if remember_token:
            saved_login = session.query(SavedLogin).filter(
                SavedLogin.remember_token == remember_token
            ).first()
            if saved_login:
                saved_login.is_active = False
        elif user_id:
            saved_logins = session.query(SavedLogin).filter(
                SavedLogin.user_id == user_id,
                SavedLogin.is_active == True
            ).all()
            for saved_login in saved_logins:
                saved_login.is_active = False
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to clear saved login: {e}")
    finally:
        session.close()

def get_saved_username() -> str:
    """
    ดึง username ที่บันทึกไว้ล่าสุด (สำหรับแสดงในฟอร์ม login)
    ใช้ StoreSetting เพื่อเก็บ username ล่าสุด
    
    Returns:
        Username หรือ empty string
    """
    try:
        from utils.store_settings import get_setting, ensure_store_settings_table
        # Ensure table exists first
        ensure_store_settings_table()
        return get_setting('last_login_username', '')
    except Exception as e:
        print(f"[ERROR] Failed to get saved username: {e}")
        return ""

def set_saved_username(username: str):
    """
    บันทึก username ล่าสุด
    
    Args:
        username: Username ที่จะบันทึก
    """
    try:
        from utils.store_settings import set_setting, ensure_store_settings_table
        # Ensure table exists first
        ensure_store_settings_table()
        set_setting('last_login_username', username, 'Username ที่ล็อคอินล่าสุด')
    except Exception as e:
        print(f"[ERROR] Failed to set saved username: {e}")

