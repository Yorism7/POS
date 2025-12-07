"""
ระบบ POS สำหรับร้านขายของชำและอาหารตามสั่ง
Main Streamlit Application
"""

import streamlit as st
from database.db import init_db, get_session
from database.models import User
from utils.security import check_login_rate_limit, record_login_attempt
from utils.validators import validate_username, validate_password
import bcrypt
from datetime import datetime

# ตั้งค่า page config
st.set_page_config(
    page_title="ระบบ POS",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS สำหรับ responsive design
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        .stButton>button {
            width: 100%;
            font-size: 0.9rem;
        }
        h1 {
            font-size: 1.5rem;
        }
        h2 {
            font-size: 1.3rem;
        }
        h3 {
            font-size: 1.1rem;
        }
    }
    .stButton>button {
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stDataFrame {
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
    }
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .stButton>button {
            min-height: 48px;
            font-size: 1rem;
            padding: 0.75rem 1rem;
        }
        .stNumberInput>div>div>input {
            font-size: 1rem;
            min-height: 48px;
        }
        .stTextInput>div>div>input {
            font-size: 1rem;
            min-height: 48px;
        }
        .stSelectbox>div>div {
            font-size: 1rem;
            min-height: 48px;
        }
        .stRadio>div {
            gap: 0.5rem;
        }
        .stRadio>div>label {
            padding: 0.75rem;
            font-size: 0.9rem;
        }
        /* Touch-friendly spacing */
        .element-container {
            margin-bottom: 1rem;
        }
        /* Larger touch targets */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }
    /* Touch-friendly buttons */
    .stButton>button:active {
        transform: scale(0.98);
    }
    /* Better mobile scrolling */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def init_session_state():
    """Initialize session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = None
    if 'remember_me' not in st.session_state:
        st.session_state.remember_me = False
    if 'remember_token' not in st.session_state:
        st.session_state.remember_token = None

def create_default_admin():
    """Create default admin user if not exists"""
    session = get_session()
    try:
        admin = session.query(User).filter(User.username == 'admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=hash_password('admin'),
                role='admin'
            )
            session.add(admin)
            session.commit()
            print(f"[DEBUG] สร้างผู้ใช้ admin เริ่มต้นสำเร็จ - {datetime.now()}")
            st.info("✅ สร้างผู้ใช้ admin เริ่มต้นแล้ว (username: admin, password: admin)")
        else:
            print(f"[DEBUG] พบผู้ใช้ admin อยู่แล้ว - {datetime.now()}")
    except Exception as e:
        print(f"[DEBUG] เกิดข้อผิดพลาดในการสร้างผู้ใช้เริ่มต้น: {str(e)} - {datetime.now()}")
        st.error(f"❌ เกิดข้อผิดพลาดในการสร้างผู้ใช้เริ่มต้น: {str(e)}")
    finally:
        session.close()

def login_page():
    """Login page"""
    st.title("🔐 เข้าสู่ระบบ POS")
    
    # Load saved username if exists
    saved_username = st.session_state.get('saved_username', '')
    
    with st.form("login_form"):
        username = st.text_input("ชื่อผู้ใช้", value=saved_username)
        password = st.text_input("รหัสผ่าน", type="password")
        remember_me = st.checkbox("💾 จดจำการล็อคอิน", value=st.session_state.get('remember_me', False))
        submit = st.form_submit_button("เข้าสู่ระบบ", width='stretch')
        
        if submit:
            if username and password:
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
                    if user and verify_password(password, user.password_hash):
                        record_login_attempt(username, True)
                        st.session_state.authenticated = True
                        st.session_state.user_id = user.id
                        st.session_state.username = user.username
                        st.session_state.role = user.role
                        st.session_state.last_activity = datetime.now()
                        
                        # Save login info if remember me is checked
                        if remember_me:
                            st.session_state.remember_me = True
                            st.session_state.saved_username = user.username
                        else:
                            st.session_state.remember_me = False
                            st.session_state.saved_username = None
                        
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

def main():
    """Main application"""
    init_session_state()
    
    # Initialize database
    init_db()
    create_default_admin()
    
    # ตรวจสอบว่าอยู่ในหน้าสำหรับลูกค้าทั่วไปหรือไม่ (ไม่ต้องล็อคอิน)
    current_page = st.query_params.get('page', [None])[0] if hasattr(st, 'query_params') and st.query_params.get('page') else None
    # ตรวจสอบจากชื่อไฟล์หน้า
    import os
    script_path = os.path.basename(__file__)
    # ตรวจสอบว่าอยู่ในหน้า 11_🍽️_สั่งอาหาร.py หรือไม่
    # Streamlit จะโหลดหน้าโดยอัตโนมัติ ดังนั้นเราต้องตรวจสอบจากชื่อหน้า
    # แต่เนื่องจาก app.py เป็น main page เราจะตรวจสอบในหน้า 11_🍽️_สั่งอาหาร.py แทน
    
    # Check persistent login first (เฉพาะสำหรับผู้ใช้ที่ล็อคอิน)
    from utils.auth import check_persistent_login
    check_persistent_login()
    
    # Check authentication (ข้ามสำหรับหน้าสั่งอาหาร)
    # หน้า 11_🍽️_สั่งอาหาร.py จะจัดการ authentication เอง
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.title(f"👤 {st.session_state.username}")
        st.caption(f"บทบาท: {st.session_state.role}")
        
        if st.button("🚪 ออกจากระบบ", width='stretch'):
            # Clear persistent login if exists
            if 'remember_token' in st.session_state:
                from utils.persistent_login import clear_saved_login
                clear_saved_login(remember_token=st.session_state.remember_token)
                del st.session_state.remember_token
            
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.remember_me = False
            st.rerun()
    
    # Main content - Pages will be loaded automatically by Streamlit
    st.title("💰 ระบบ POS")
    st.caption("ระบบ Point of Sale สำหรับร้านขายของชำและอาหารตามสั่ง")

if __name__ == "__main__":
    main()

