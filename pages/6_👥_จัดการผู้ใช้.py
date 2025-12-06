"""
User Management Page - จัดการผู้ใช้
"""

import streamlit as st
from datetime import datetime
from database.db import get_session, hash_password
from database.models import User
import bcrypt

st.set_page_config(page_title="จัดการผู้ใช้", page_icon="👥", layout="wide")

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def main():
    st.title("👥 จัดการผู้ใช้")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["📋 รายการผู้ใช้", "➕ เพิ่มผู้ใช้"])
    
    with tab1:
        st.subheader("📋 รายการผู้ใช้ทั้งหมด")
        
        session = get_session()
        try:
            users = session.query(User).order_by(User.username).all()
            
            if users:
                for user in users:
                    with st.expander(f"👤 {user.username} - {user.role}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ชื่อผู้ใช้:** {user.username}")
                            st.write(f"**บทบาท:** {user.role}")
                            st.write(f"**สร้างเมื่อ:** {user.created_at.strftime('%d/%m/%Y %H:%M')}")
                        
                        with col2:
                            if st.button("✏️ แก้ไข", key=f"edit_{user.id}", use_container_width=True):
                                st.session_state[f"editing_user_{user.id}"] = True
                                st.rerun()
                            
                            # Don't allow deleting yourself
                            if user.id == st.session_state.user_id:
                                st.info("⚠️ ไม่สามารถลบตัวเองได้")
                            else:
                                if st.button("🗑️ ลบ", key=f"delete_{user.id}", use_container_width=True):
                                    st.session_state[f"confirm_delete_user_{user.id}"] = True
                                    st.rerun()
                                
                                # Confirmation dialog
                                if st.session_state.get(f"confirm_delete_user_{user.id}", False):
                                    st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบผู้ใช้ {user.username}?")
                                    col_yes, col_no = st.columns(2)
                                    with col_yes:
                                        if st.button("✅ ยืนยัน", key=f"yes_delete_user_{user.id}", use_container_width=True):
                                            try:
                                                session.delete(user)
                                                session.commit()
                                                st.session_state[f"confirm_delete_user_{user.id}"] = False
                                                st.success(f"✅ ลบผู้ใช้ {user.username} สำเร็จ")
                                                st.rerun()
                                            except Exception as e:
                                                session.rollback()
                                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                    with col_no:
                                        if st.button("❌ ยกเลิก", key=f"no_delete_user_{user.id}", use_container_width=True):
                                            st.session_state[f"confirm_delete_user_{user.id}"] = False
                                            st.rerun()
                        
                        with col3:
                            if st.button("🔑 เปลี่ยนรหัสผ่าน", key=f"change_pass_{user.id}", use_container_width=True):
                                st.session_state[f"changing_pass_{user.id}"] = True
                                st.rerun()
                        
                        # Edit form
                        if st.session_state.get(f"editing_user_{user.id}", False):
                            st.divider()
                            with st.form(f"edit_user_form_{user.id}"):
                                new_username = st.text_input("ชื่อผู้ใช้", value=user.username, key=f"username_{user.id}")
                                new_role = st.selectbox(
                                    "บทบาท",
                                    ["admin", "staff"],
                                    index=0 if user.role == 'admin' else 1,
                                    key=f"role_{user.id}"
                                )
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 บันทึก", use_container_width=True):
                                        if new_username:
                                            try:
                                                # Check if username already exists (except current user)
                                                existing = session.query(User).filter(
                                                    User.username == new_username,
                                                    User.id != user.id
                                                ).first()
                                                
                                                if existing:
                                                    st.error("❌ ชื่อผู้ใช้นี้มีอยู่แล้ว")
                                                else:
                                                    user.username = new_username
                                                    user.role = new_role
                                                    session.commit()
                                                    st.session_state[f"editing_user_{user.id}"] = False
                                                    st.success("✅ บันทึกสำเร็จ")
                                                    st.rerun()
                                            except Exception as e:
                                                session.rollback()
                                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                        else:
                                            st.warning("⚠️ กรุณากรอกชื่อผู้ใช้")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                        st.session_state[f"editing_user_{user.id}"] = False
                                        st.rerun()
                        
                        # Change password form
                        if st.session_state.get(f"changing_pass_{user.id}", False):
                            st.divider()
                            with st.form(f"change_pass_form_{user.id}"):
                                new_password = st.text_input("รหัสผ่านใหม่", type="password", key=f"new_pass_{user.id}")
                                confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password", key=f"confirm_pass_{user.id}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 เปลี่ยนรหัสผ่าน", use_container_width=True):
                                        if new_password:
                                            if new_password == confirm_password:
                                                try:
                                                    user.password_hash = hash_password(new_password)
                                                    session.commit()
                                                    st.session_state[f"changing_pass_{user.id}"] = False
                                                    st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ")
                                                    st.rerun()
                                                except Exception as e:
                                                    session.rollback()
                                                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                            else:
                                                st.error("❌ รหัสผ่านไม่ตรงกัน")
                                        else:
                                            st.warning("⚠️ กรุณากรอกรหัสผ่าน")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                        st.session_state[f"changing_pass_{user.id}"] = False
                                        st.rerun()
            else:
                st.info("ไม่มีผู้ใช้")
        finally:
            session.close()
    
    with tab2:
        st.subheader("➕ เพิ่มผู้ใช้ใหม่")
        
        session = get_session()
        try:
            with st.form("add_user_form"):
                username = st.text_input("ชื่อผู้ใช้ *", placeholder="username")
                password = st.text_input("รหัสผ่าน *", type="password", placeholder="password")
                confirm_password = st.text_input("ยืนยันรหัสผ่าน *", type="password", placeholder="confirm password")
                role = st.selectbox("บทบาท *", ["staff", "admin"], index=0)
                
                if st.form_submit_button("➕ เพิ่มผู้ใช้", type="primary", use_container_width=True):
                    if username and password:
                        if password == confirm_password:
                            # Check if username exists
                            existing = session.query(User).filter(User.username == username).first()
                            if existing:
                                st.error("❌ ชื่อผู้ใช้นี้มีอยู่แล้ว")
                            else:
                                try:
                                    user = User(
                                        username=username,
                                        password_hash=hash_password(password),
                                        role=role
                                    )
                                    session.add(user)
                                    session.commit()
                                    st.success(f"✅ เพิ่มผู้ใช้ {username} สำเร็จ")
                                    st.rerun()
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        else:
                            st.error("❌ รหัสผ่านไม่ตรงกัน")
                    else:
                        st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
        finally:
            session.close()
    
    # Change own password
    st.divider()
    st.subheader("🔑 เปลี่ยนรหัสผ่านของฉัน")
    
    with st.form("change_own_password"):
        current_password = st.text_input("รหัสผ่านปัจจุบัน", type="password")
        new_password = st.text_input("รหัสผ่านใหม่", type="password")
        confirm_new_password = st.text_input("ยืนยันรหัสผ่านใหม่", type="password")
        
        if st.form_submit_button("🔑 เปลี่ยนรหัสผ่าน", type="primary", use_container_width=True):
            session = get_session()
            try:
                user = session.query(User).filter(User.id == st.session_state.user_id).first()
                if user:
                    if verify_password(current_password, user.password_hash):
                        if new_password:
                            if new_password == confirm_new_password:
                                user.password_hash = hash_password(new_password)
                                session.commit()
                                st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ")
                                st.rerun()
                            else:
                                st.error("❌ รหัสผ่านใหม่ไม่ตรงกัน")
                        else:
                            st.warning("⚠️ กรุณากรอกรหัสผ่านใหม่")
                    else:
                        st.error("❌ รหัสผ่านปัจจุบันไม่ถูกต้อง")
            except Exception as e:
                session.rollback()
                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            finally:
                session.close()

if __name__ == "__main__":
    main()

