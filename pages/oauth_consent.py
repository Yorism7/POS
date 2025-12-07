"""
OAuth Consent Screen
หน้า consent สำหรับ OAuth Server
"""

import streamlit as st
from utils.supabase_auth import get_supabase_client, require_supabase_auth
import secrets
from datetime import datetime, timedelta

st.set_page_config(
    page_title="OAuth Consent",
    page_icon="🔐",
    layout="centered"
)

def generate_authorization_code(client_id: str, user_id: str, redirect_uri: str) -> str:
    """
    Generate OAuth authorization code
    
    Args:
        client_id: OAuth client ID
        user_id: User ID
        redirect_uri: Redirect URI
    
    Returns:
        Authorization code
    """
    # Generate random code
    code = secrets.token_urlsafe(32)
    
    # Store in session state (in production, store in database)
    if 'oauth_codes' not in st.session_state:
        st.session_state.oauth_codes = {}
    
    # Store code with expiration (10 minutes)
    st.session_state.oauth_codes[code] = {
        'client_id': client_id,
        'user_id': user_id,
        'redirect_uri': redirect_uri,
        'expires_at': datetime.now() + timedelta(minutes=10)
    }
    
    return code

def main():
    """OAuth consent screen"""
    st.title("🔐 Authorization Request")
    
    # Get OAuth parameters from query string
    query_params = st.experimental_get_query_params()
    client_id = query_params.get('client_id', [None])[0]
    redirect_uri = query_params.get('redirect_uri', [None])[0]
    scope = query_params.get('scope', ['read'])[0]
    state = query_params.get('state', [None])[0]
    response_type = query_params.get('response_type', ['code'])[0]
    
    # Validate parameters
    if not client_id or not redirect_uri:
        st.error("❌ Invalid OAuth request: Missing client_id or redirect_uri")
        st.info("💡 Required parameters: client_id, redirect_uri")
        return
    
    if response_type != 'code':
        st.error(f"❌ Unsupported response_type: {response_type}")
        st.info("💡 Only 'code' response type is supported")
        return
    
    # Check if user is authenticated
    supabase = get_supabase_client()
    if not supabase:
        st.error("❌ Supabase not configured")
        st.info("💡 Please configure Supabase secrets")
        return
    
    # Check authentication
    try:
        user_response = supabase.auth.get_user()
        if not user_response or not user_response.user:
            st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
            from utils.supabase_auth import show_supabase_login_page
            show_supabase_login_page()
            return
        
        user = user_response.user
    except Exception as e:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        from utils.supabase_auth import show_supabase_login_page
        show_supabase_login_page()
        return
    
    # Show consent screen
    st.divider()
    st.subheader("📱 แอปพลิเคชันขออนุญาต")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("**Client ID:**")
        st.write("**Redirect URI:**")
        st.write("**Scope:**")
        st.write("**User:**")
    
    with col2:
        st.code(client_id)
        st.code(redirect_uri)
        st.code(scope)
        st.write(f"👤 {user.email}")
    
    st.divider()
    st.info(f"💡 แอปพลิเคชันนี้ต้องการเข้าถึง: **{scope}**")
    st.warning("⚠️ ตรวจสอบให้แน่ใจว่าแอปพลิเคชันนี้เชื่อถือได้")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ อนุญาต", type="primary", use_container_width=True):
            # Generate authorization code
            code = generate_authorization_code(client_id, user.id, redirect_uri)
            
            # Build redirect URL
            redirect_url = f"{redirect_uri}?code={code}"
            if state:
                redirect_url += f"&state={state}"
            
            st.success("✅ อนุญาตแล้ว กำลัง redirect...")
            st.markdown(f'<meta http-equiv="refresh" content="1; url={redirect_url}">', unsafe_allow_html=True)
            st.info(f"🔄 Redirecting to: {redirect_uri}")
    
    with col2:
        if st.button("❌ ปฏิเสธ", use_container_width=True):
            # Build error redirect URL
            error_url = f"{redirect_uri}?error=access_denied"
            if state:
                error_url += f"&state={state}"
            
            st.error("❌ ปฏิเสธแล้ว กำลัง redirect...")
            st.markdown(f'<meta http-equiv="refresh" content="1; url={error_url}">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

