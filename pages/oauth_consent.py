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
    # Use new st.query_params API (Streamlit 1.28+)
    try:
        # Try new API first
        if hasattr(st, 'query_params'):
            query_params_raw = st.query_params
            # Convert to dict format for compatibility
            query_params = {}
            for key, value in query_params_raw.items():
                if isinstance(value, list):
                    query_params[key] = value
                else:
                    query_params[key] = [value]
        else:
            # Fallback to experimental API (deprecated)
            query_params = st.experimental_get_query_params()
    except Exception as e:
        # Fallback to experimental API if new API fails
        try:
            query_params = st.experimental_get_query_params()
        except:
            query_params = {}
    
    # Debug: Show all query parameters
    with st.expander("🔍 Debug: Query Parameters"):
        st.json(dict(query_params))
    
    client_id = query_params.get('client_id', [None])[0]
    redirect_uri = query_params.get('redirect_uri', [None])[0]
    scope = query_params.get('scope', ['read'])[0]
    state = query_params.get('state', [None])[0]
    response_type = query_params.get('response_type', ['code'])[0]
    
    # Validate parameters
    if not client_id or not redirect_uri:
        st.error("❌ Invalid OAuth request: Missing client_id or redirect_uri")
        st.info("💡 Required parameters: client_id, redirect_uri")
        
        st.divider()
        st.subheader("📖 วิธีใช้งาน OAuth Server")
        
        st.markdown("""
        ### ขั้นตอนที่ 1: สร้าง OAuth App ใน Supabase
        
        1. ไปที่ **Supabase Dashboard** > **Authentication** > **OAuth Apps**
        2. กด **"New OAuth App"**
        3. ตั้งค่า:
           - **Name**: ชื่อแอปพลิเคชัน
           - **Redirect URIs**: `https://your-app.com/callback`
        4. **คัดลอก Client ID และ Client Secret**
        
        ### ขั้นตอนที่ 2: ทดสอบ OAuth Flow
        
        **ตัวอย่าง Authorization URL:**
        ```
        https://pos-ez.streamlit.app/oauth/consent?
        client_id=YOUR_CLIENT_ID&
        redirect_uri=https://your-app.com/callback&
        response_type=code&
        scope=read&
        state=random-state-string
        ```
        
        **หรือใช้ลิงก์ทดสอบ:**
        """)
        
        # Test form
        with st.form("test_oauth_form"):
            st.subheader("🧪 ทดสอบ OAuth Flow")
            test_client_id = st.text_input("Client ID", placeholder="your-client-id")
            test_redirect_uri = st.text_input("Redirect URI", placeholder="https://your-app.com/callback", value="https://example.com/callback")
            test_scope = st.text_input("Scope", value="read")
            test_state = st.text_input("State (optional)", value="test-state-123")
            
            if st.form_submit_button("🔗 สร้าง Authorization URL", type="primary", width='stretch'):
                if test_client_id and test_redirect_uri:
                    # Build query string
                    import urllib.parse
                    params = {
                        'client_id': test_client_id,
                        'redirect_uri': test_redirect_uri,
                        'response_type': 'code',
                        'scope': test_scope,
                        'state': test_state
                    }
                    query_string = urllib.parse.urlencode(params)
                    
                    # Get current base URL
                    # Use relative URL (works for both local and Streamlit Cloud)
                    auth_url = f"/oauth/consent?{query_string}"
                    
                    st.success("✅ สร้าง URL สำเร็จ!")
                    st.code(auth_url, language=None)
                    
                    # Use JavaScript redirect instead of st.experimental_set_query_params
                    # This avoids the Streamlit API conflict
                    st.markdown(f"""
                    <script>
                        // Auto-redirect after 1 second
                        setTimeout(function() {{
                            window.location.href = '{auth_url}';
                        }}, 1000);
                    </script>
                    """, unsafe_allow_html=True)
                    
                    st.info("🔄 กำลัง redirect ไปที่ Authorization URL... (1 วินาที)")
                    st.markdown(f'<a href="{auth_url}" target="_self" style="display: inline-block; padding: 10px 20px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">🔗 เปิด Authorization URL ทันที</a>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ กรุณากรอก Client ID และ Redirect URI")
        
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
        if st.button("✅ อนุญาต", type="primary", width='stretch'):
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
        if st.button("❌ ปฏิเสธ", width='stretch'):
            # Build error redirect URL
            error_url = f"{redirect_uri}?error=access_denied"
            if state:
                error_url += f"&state={state}"
            
            st.error("❌ ปฏิเสธแล้ว กำลัง redirect...")
            st.markdown(f'<meta http-equiv="refresh" content="1; url={error_url}">', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

