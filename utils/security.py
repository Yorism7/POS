"""
Security Functions for POS System
"""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

# Simple in-memory rate limiting (for production, use Redis or similar)
_login_attempts: Dict[str, list] = {}
_session_timeout_minutes = 60  # 1 hour

def check_login_rate_limit(username: str, max_attempts: int = 5, window_seconds: int = 300) -> Tuple[bool, Optional[str]]:
    """Check if login attempts exceed rate limit"""
    now = time.time()
    
    if username not in _login_attempts:
        _login_attempts[username] = []
    
    # Remove old attempts outside the window
    _login_attempts[username] = [
        attempt_time for attempt_time in _login_attempts[username]
        if now - attempt_time < window_seconds
    ]
    
    if len(_login_attempts[username]) >= max_attempts:
        return False, f"ลองเข้าสู่ระบบมากเกินไป กรุณารอ {window_seconds // 60} นาที"
    
    return True, None

def record_login_attempt(username: str, success: bool):
    """Record login attempt"""
    if success:
        # Clear attempts on successful login
        if username in _login_attempts:
            _login_attempts[username] = []
    else:
        # Record failed attempt
        if username not in _login_attempts:
            _login_attempts[username] = []
        _login_attempts[username].append(time.time())

def check_session_timeout(last_activity: Optional[datetime]) -> bool:
    """Check if session has timed out"""
    if not last_activity:
        return True
    
    timeout_threshold = datetime.now() - timedelta(minutes=_session_timeout_minutes)
    return last_activity < timeout_threshold

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace('"', "&quot;").replace("'", "&#x27;")
    return text.strip()

