"""
User Management Page - จัดการผู้ใช้
"""

import streamlit as st
from datetime import datetime, timedelta
from database.db import get_session, hash_password
from database.models import User, Customer, Membership, LoyaltyTransaction, Coupon, Attendance, EmployeeShift
from utils.helpers import format_currency, get_customer_membership, create_membership
from utils.attendance import (
    clock_in, clock_out, get_today_attendance, get_attendance_by_date_range,
    get_employee_performance, create_shift, get_shifts_by_date_range
)
import bcrypt

st.set_page_config(page_title="จัดการผู้ใช้", page_icon="👥", layout="wide")

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def main():
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth, require_role
    require_auth()
    
    st.title("👥 จัดการผู้ใช้")
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 รายการผู้ใช้", "➕ เพิ่มผู้ใช้", "👥 จัดการลูกค้า", "🎫 จัดการคูปอง", "⏰ บันทึกเวลา"
    ])
    
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
    
    with tab3:
        st.subheader("👥 จัดการลูกค้า")
        
        # Search customer
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("🔍 ค้นหาลูกค้า (ชื่อ, เบอร์โทร, อีเมล)", placeholder="พิมพ์ชื่อหรือเบอร์โทร...")
        with search_col2:
            search_type = st.selectbox("ประเภท", ["ทั้งหมด", "สมาชิก", "ไม่ใช่สมาชิก"], key="customer_search_type")
        
        # Add new customer
        with st.expander("➕ เพิ่มลูกค้าใหม่"):
            with st.form("add_customer_form"):
                col1, col2 = st.columns(2)
                with col1:
                    customer_name = st.text_input("ชื่อ *", placeholder="ชื่อลูกค้า")
                    customer_phone = st.text_input("เบอร์โทรศัพท์", placeholder="0812345678")
                with col2:
                    customer_email = st.text_input("อีเมล", placeholder="email@example.com")
                    customer_address = st.text_area("ที่อยู่", placeholder="ที่อยู่ลูกค้า")
                
                is_member = st.checkbox("เป็นสมาชิก", value=False)
                member_code = None
                if is_member:
                    member_code = st.text_input("รหัสสมาชิก (เว้นว่างเพื่อสร้างอัตโนมัติ)", placeholder="M000001")
                
                if st.form_submit_button("➕ เพิ่มลูกค้า", type="primary", use_container_width=True):
                    if customer_name:
                        session = get_session()
                        try:
                            # Check if phone already exists
                            existing = None
                            if customer_phone:
                                existing = session.query(Customer).filter(Customer.phone == customer_phone).first()
                            
                            if existing:
                                st.error("❌ เบอร์โทรศัพท์นี้มีอยู่แล้ว")
                            else:
                                customer = Customer(
                                    name=customer_name,
                                    phone=customer_phone if customer_phone else None,
                                    email=customer_email if customer_email else None,
                                    address=customer_address if customer_address else None,
                                    is_member=is_member
                                )
                                session.add(customer)
                                session.commit()
                                session.refresh(customer)
                                
                                # Create membership if needed
                                if is_member:
                                    create_membership(customer.id, member_code if member_code else None)
                                
                                st.success(f"✅ เพิ่มลูกค้า {customer_name} สำเร็จ")
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        finally:
                            session.close()
                    else:
                        st.warning("⚠️ กรุณากรอกชื่อลูกค้า")
        
        # Customer list
        st.divider()
        st.write("**📋 รายการลูกค้า**")
        
        session = get_session()
        try:
            query = session.query(Customer)
            
            # Apply filters
            if search_term:
                query = query.filter(
                    (Customer.name.contains(search_term)) |
                    (Customer.phone.contains(search_term)) |
                    (Customer.email.contains(search_term))
                )
            
            if search_type == "สมาชิก":
                query = query.filter(Customer.is_member == True)
            elif search_type == "ไม่ใช่สมาชิก":
                query = query.filter(Customer.is_member == False)
            
            customers = query.order_by(Customer.name).limit(50).all()
            
            if customers:
                for customer in customers:
                    with st.expander(f"👤 {customer.name} {'⭐ สมาชิก' if customer.is_member else ''}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ชื่อ:** {customer.name}")
                            st.write(f"**เบอร์โทร:** {customer.phone or '-'}")
                            st.write(f"**อีเมล:** {customer.email or '-'}")
                            st.write(f"**ที่อยู่:** {customer.address or '-'}")
                        
                        with col2:
                            if customer.is_member:
                                membership = get_customer_membership(customer.id)
                                if membership:
                                    st.write(f"**รหัสสมาชิก:** {membership.member_code}")
                                    st.write(f"**แต้มสะสม:** {membership.points:.2f} แต้ม")
                                    st.write(f"**ยอดซื้อสะสม:** {format_currency(membership.total_spent)}")
                                    st.write(f"**จำนวนครั้ง:** {membership.total_visits} ครั้ง")
                                    if membership.last_visit:
                                        st.write(f"**เยี่ยมล่าสุด:** {membership.last_visit.strftime('%d/%m/%Y %H:%M')}")
                            
                            # View purchase history
                            if st.button("📊 ดูประวัติการซื้อ", key=f"history_{customer.id}", use_container_width=True):
                                st.session_state[f"view_history_{customer.id}"] = True
                                st.rerun()
                        
                        with col3:
                            if st.button("✏️ แก้ไข", key=f"edit_customer_{customer.id}", use_container_width=True):
                                st.session_state[f"editing_customer_{customer.id}"] = True
                                st.rerun()
                            
                            if customer.is_member:
                                if st.button("⭐ ยกเลิกสมาชิก", key=f"cancel_member_{customer.id}", use_container_width=True):
                                    st.session_state[f"cancel_member_{customer.id}"] = True
                                    st.rerun()
                            else:
                                if st.button("⭐ สมัครสมาชิก", key=f"make_member_{customer.id}", use_container_width=True):
                                    create_membership(customer.id)
                                    customer.is_member = True
                                    session.commit()
                                    st.success("✅ สมัครสมาชิกสำเร็จ")
                                    st.rerun()
                            
                            if st.button("🗑️ ลบ", key=f"delete_customer_{customer.id}", use_container_width=True):
                                st.session_state[f"confirm_delete_customer_{customer.id}"] = True
                                st.rerun()
                            
                            # Confirmation dialog
                            if st.session_state.get(f"confirm_delete_customer_{customer.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบลุกค้า {customer.name}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_customer_{customer.id}", use_container_width=True):
                                        try:
                                            session.delete(customer)
                                            session.commit()
                                            st.session_state[f"confirm_delete_customer_{customer.id}"] = False
                                            st.success(f"✅ ลบลุกค้า {customer.name} สำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_customer_{customer.id}", use_container_width=True):
                                        st.session_state[f"confirm_delete_customer_{customer.id}"] = False
                                        st.rerun()
                        
                        # Edit form
                        if st.session_state.get(f"editing_customer_{customer.id}", False):
                            st.divider()
                            with st.form(f"edit_customer_form_{customer.id}"):
                                new_name = st.text_input("ชื่อ", value=customer.name, key=f"customer_name_{customer.id}")
                                new_phone = st.text_input("เบอร์โทร", value=customer.phone or "", key=f"customer_phone_{customer.id}")
                                new_email = st.text_input("อีเมล", value=customer.email or "", key=f"customer_email_{customer.id}")
                                new_address = st.text_area("ที่อยู่", value=customer.address or "", key=f"customer_address_{customer.id}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 บันทึก", use_container_width=True):
                                        try:
                                            customer.name = new_name
                                            customer.phone = new_phone if new_phone else None
                                            customer.email = new_email if new_email else None
                                            customer.address = new_address if new_address else None
                                            customer.updated_at = datetime.now()
                                            session.commit()
                                            st.session_state[f"editing_customer_{customer.id}"] = False
                                            st.success("✅ บันทึกสำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                        st.session_state[f"editing_customer_{customer.id}"] = False
                                        st.rerun()
                        
                        # Purchase history
                        if st.session_state.get(f"view_history_{customer.id}", False):
                            st.divider()
                            st.write("**📊 ประวัติการซื้อ**")
                            from database.models import Sale
                            sales = session.query(Sale).filter(
                                Sale.customer_id == customer.id,
                                Sale.is_void == False
                            ).order_by(Sale.sale_date.desc()).limit(20).all()
                            
                            if sales:
                                for sale in sales:
                                    st.write(f"**#{sale.id:06d}** - {sale.sale_date.strftime('%d/%m/%Y %H:%M')} - {format_currency(sale.final_amount)}")
                                    if sale.points_earned > 0:
                                        st.caption(f"ได้รับแต้ม: {sale.points_earned:.2f} แต้ม")
                                    if sale.points_used > 0:
                                        st.caption(f"ใช้แต้ม: {sale.points_used:.2f} แต้ม")
                            else:
                                st.info("ยังไม่มีประวัติการซื้อ")
            else:
                st.info("ไม่พบลูกค้า")
        finally:
            session.close()
    
    with tab4:
        st.subheader("🎫 จัดการคูปอง")
        
        # Add new coupon
        with st.expander("➕ เพิ่มคูปองใหม่"):
            with st.form("add_coupon_form"):
                col1, col2 = st.columns(2)
                with col1:
                    coupon_code = st.text_input("รหัสคูปอง *", placeholder="DISCOUNT10").upper()
                    coupon_name = st.text_input("ชื่อคูปอง *", placeholder="ส่วนลด 10%")
                    coupon_description = st.text_area("คำอธิบาย", placeholder="คำอธิบายคูปอง")
                    discount_type = st.selectbox("ประเภทส่วนลด", ["percent", "fixed"], format_func=lambda x: "เปอร์เซ็นต์ (%)" if x == "percent" else "จำนวนเงิน (฿)")
                    discount_value = st.number_input("ค่าส่วนลด", min_value=0.0, step=1.0, value=10.0)
                
                with col2:
                    min_purchase = st.number_input("ยอดซื้อขั้นต่ำ (฿)", min_value=0.0, step=10.0, value=0.0)
                    max_discount = None
                    if discount_type == "percent":
                        max_discount = st.number_input("ส่วนลดสูงสุด (฿)", min_value=0.0, step=10.0, value=0.0)
                        if max_discount == 0:
                            max_discount = None
                    valid_from = st.date_input("วันที่เริ่มต้น", value=datetime.now().date())
                    valid_until = st.date_input("วันที่สิ้นสุด", value=datetime.now().date())
                    usage_limit = st.number_input("จำนวนครั้งที่ใช้ได้ (0 = ไม่จำกัด)", min_value=0, step=1, value=0)
                    if usage_limit == 0:
                        usage_limit = None
                
                if st.form_submit_button("➕ เพิ่มคูปอง", type="primary", use_container_width=True):
                    if coupon_code and coupon_name:
                        session = get_session()
                        try:
                            # Check if code exists
                            existing = session.query(Coupon).filter(Coupon.code == coupon_code).first()
                            if existing:
                                st.error("❌ รหัสคูปองนี้มีอยู่แล้ว")
                            else:
                                coupon = Coupon(
                                    code=coupon_code,
                                    name=coupon_name,
                                    description=coupon_description if coupon_description else None,
                                    discount_type=discount_type,
                                    discount_value=discount_value,
                                    min_purchase=min_purchase,
                                    max_discount=max_discount,
                                    valid_from=datetime.combine(valid_from, datetime.min.time()),
                                    valid_until=datetime.combine(valid_until, datetime.max.time()),
                                    usage_limit=usage_limit,
                                    used_count=0,
                                    is_active=True
                                )
                                session.add(coupon)
                                session.commit()
                                st.success(f"✅ เพิ่มคูปอง {coupon_code} สำเร็จ")
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        finally:
                            session.close()
                    else:
                        st.warning("⚠️ กรุณากรอกรหัสและชื่อคูปอง")
        
        # Coupon list
        st.divider()
        st.write("**📋 รายการคูปอง**")
        
        session = get_session()
        try:
            coupons = session.query(Coupon).order_by(Coupon.created_at.desc()).all()
            
            if coupons:
                for coupon in coupons:
                    status = "✅ ใช้งานได้" if coupon.is_active else "❌ ปิดใช้งาน"
                    status_color = "green" if coupon.is_active else "red"
                    
                    with st.expander(f"🎫 {coupon.code} - {coupon.name} ({status})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**รหัส:** {coupon.code}")
                            st.write(f"**ชื่อ:** {coupon.name}")
                            if coupon.description:
                                st.write(f"**คำอธิบาย:** {coupon.description}")
                            discount_text = f"{coupon.discount_value}%" if coupon.discount_type == "percent" else f"{format_currency(coupon.discount_value)}"
                            st.write(f"**ส่วนลด:** {discount_text}")
                            if coupon.max_discount:
                                st.write(f"**ส่วนลดสูงสุด:** {format_currency(coupon.max_discount)}")
                            st.write(f"**ยอดซื้อขั้นต่ำ:** {format_currency(coupon.min_purchase)}")
                        
                        with col2:
                            st.write(f"**วันที่เริ่ม:** {coupon.valid_from.strftime('%d/%m/%Y')}")
                            st.write(f"**วันที่สิ้นสุด:** {coupon.valid_until.strftime('%d/%m/%Y')}")
                            usage_text = f"{coupon.used_count}/{coupon.usage_limit}" if coupon.usage_limit else f"{coupon.used_count}/ไม่จำกัด"
                            st.write(f"**ใช้แล้ว:** {usage_text}")
                            st.write(f"**สถานะ:** {'เปิดใช้งาน' if coupon.is_active else 'ปิดใช้งาน'}")
                        
                        with col3:
                            if st.button("✏️ แก้ไข", key=f"edit_coupon_{coupon.id}", use_container_width=True):
                                st.session_state[f"editing_coupon_{coupon.id}"] = True
                                st.rerun()
                            
                            if coupon.is_active:
                                if st.button("❌ ปิดใช้งาน", key=f"deactivate_coupon_{coupon.id}", use_container_width=True):
                                    coupon.is_active = False
                                    session.commit()
                                    st.success("✅ ปิดใช้งานคูปองสำเร็จ")
                                    st.rerun()
                            else:
                                if st.button("✅ เปิดใช้งาน", key=f"activate_coupon_{coupon.id}", use_container_width=True):
                                    coupon.is_active = True
                                    session.commit()
                                    st.success("✅ เปิดใช้งานคูปองสำเร็จ")
                                    st.rerun()
                            
                            if st.button("🗑️ ลบ", key=f"delete_coupon_{coupon.id}", use_container_width=True):
                                st.session_state[f"confirm_delete_coupon_{coupon.id}"] = True
                                st.rerun()
                            
                            # Confirmation dialog
                            if st.session_state.get(f"confirm_delete_coupon_{coupon.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบคูปอง {coupon.code}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_coupon_{coupon.id}", use_container_width=True):
                                        try:
                                            session.delete(coupon)
                                            session.commit()
                                            st.session_state[f"confirm_delete_coupon_{coupon.id}"] = False
                                            st.success(f"✅ ลบคูปอง {coupon.code} สำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_coupon_{coupon.id}", use_container_width=True):
                                        st.session_state[f"confirm_delete_coupon_{coupon.id}"] = False
                                        st.rerun()
            else:
                st.info("ยังไม่มีคูปอง")
        finally:
            session.close()
    
    with tab5:
        st.subheader("⏰ บันทึกเวลาเข้า-ออกงาน")
        
        # Current user attendance
        st.write("**📅 บันทึกเวลาของฉัน**")
        
        today_attendance = get_today_attendance(st.session_state.user_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if today_attendance and today_attendance.clock_in and not today_attendance.clock_out:
                st.info(f"✅ เข้างานแล้ว: {today_attendance.clock_in.strftime('%H:%M:%S')}")
                if st.button("🕐 ออกงาน", type="primary", use_container_width=True, key="clock_out_btn"):
                    result = clock_out(st.session_state.user_id)
                    if result:
                        st.success(f"✅ ออกงานแล้ว: {result.clock_out.strftime('%H:%M:%S')}")
                        st.info(f"⏱️ ทำงานทั้งหมด: {result.total_hours:.2f} ชั่วโมง")
                        st.rerun()
                    else:
                        st.error("❌ ไม่สามารถออกงานได้")
            elif today_attendance and today_attendance.clock_out:
                st.success(f"✅ เข้างาน: {today_attendance.clock_in.strftime('%H:%M:%S') if today_attendance.clock_in else '-'}")
                st.success(f"✅ ออกงาน: {today_attendance.clock_out.strftime('%H:%M:%S')}")
                st.info(f"⏱️ ทำงานทั้งหมด: {today_attendance.total_hours:.2f} ชั่วโมง")
            else:
                if st.button("🕐 เข้างาน", type="primary", use_container_width=True, key="clock_in_btn"):
                    result = clock_in(st.session_state.user_id)
                    if result:
                        st.success(f"✅ เข้างานแล้ว: {result.clock_in.strftime('%H:%M:%S')}")
                        st.rerun()
                    else:
                        st.error("❌ ไม่สามารถเข้างานได้ (อาจเข้างานแล้ว)")
        
        with col2:
            # View attendance history
            if st.button("📊 ดูประวัติการทำงาน", use_container_width=True, key="view_attendance_history"):
                st.session_state['view_attendance_history'] = True
                st.rerun()
        
        # Attendance history
        if st.session_state.get('view_attendance_history', False):
            st.divider()
            st.write("**📊 ประวัติการทำงาน**")
            
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30), key="attendance_start")
            with col_end:
                end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date(), key="attendance_end")
            
            attendances = get_attendance_by_date_range(
                st.session_state.user_id,
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
            
            if attendances:
                attendance_data = []
                for att in attendances:
                    attendance_data.append({
                        'วันที่': att.attendance_date.strftime('%d/%m/%Y'),
                        'เข้า': att.clock_in.strftime('%H:%M:%S') if att.clock_in else '-',
                        'ออก': att.clock_out.strftime('%H:%M:%S') if att.clock_out else '-',
                        'ชั่วโมง': f"{att.total_hours:.2f}",
                        'สาย': 'ใช่' if att.is_late else 'ไม่',
                        'ขาด': 'ใช่' if att.is_absent else 'ไม่'
                    })
                
                import pandas as pd
                df = pd.DataFrame(attendance_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Summary
                total_hours = sum(a.total_hours for a in attendances if a.total_hours)
                st.metric("⏱️ ชั่วโมงทำงานรวม", f"{total_hours:.2f} ชั่วโมง")
            else:
                st.info("ไม่มีประวัติการทำงานในช่วงเวลานี้")
        
        # Admin section - Employee management
        if st.session_state.role == 'admin':
            st.divider()
            st.write("**👥 จัดการพนักงาน (Admin Only)**")
            
            # Employee performance
            admin_tab1, admin_tab2 = st.tabs(["📊 ประสิทธิภาพพนักงาน", "📅 จัดการกะงาน"])
            
            with admin_tab1:
                session = get_session()
                try:
                    users = session.query(User).filter(User.role == 'staff').all()
                    
                    if users:
                        selected_user = st.selectbox(
                            "เลือกพนักงาน",
                            users,
                            format_func=lambda u: u.username,
                            key="performance_user_select"
                        )
                        
                        if selected_user:
                            perf_start, perf_end = st.columns(2)
                            with perf_start:
                                perf_start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30), key="perf_start")
                            with perf_end:
                                perf_end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date(), key="perf_end")
                            
                            performance = get_employee_performance(
                                selected_user.id,
                                datetime.combine(perf_start_date, datetime.min.time()),
                                datetime.combine(perf_end_date, datetime.max.time())
                            )
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("วันทำงาน", f"{performance['total_days']} วัน")
                            with col2:
                                st.metric("ชั่วโมงทำงาน", f"{performance['total_hours']:.2f} ชม.")
                            with col3:
                                st.metric("ยอดขายรวม", format_currency(performance['total_sales']))
                            with col4:
                                st.metric("จำนวนการขาย", f"{performance['sales_count']} ครั้ง")
                            
                            st.metric("ยอดขายเฉลี่ย", format_currency(performance['avg_sale']))
                    else:
                        st.info("ไม่มีพนักงาน")
                finally:
                    session.close()
            
            with admin_tab2:
                st.write("**📅 จัดการกะงาน**")
                session = get_session()
                try:
                    users = session.query(User).filter(User.role == 'staff').all()
                    
                    if users:
                        with st.form("create_shift_form"):
                            shift_user = st.selectbox(
                                "พนักงาน",
                                users,
                                format_func=lambda u: u.username,
                                key="shift_user_select"
                            )
                            shift_date = st.date_input("วันที่", value=datetime.now().date(), key="shift_date_input")
                            col_start, col_end = st.columns(2)
                            with col_start:
                                shift_start = st.time_input("เวลาเริ่ม", value=datetime.now().time(), key="shift_start_time")
                            with col_end:
                                shift_end = st.time_input("เวลาสิ้นสุด", value=datetime.now().time(), key="shift_end_time")
                            break_duration = st.number_input("เวลาพัก (นาที)", min_value=0, value=0, key="break_duration_input")
                            shift_notes = st.text_area("หมายเหตุ", key="shift_notes_input")
                            
                            if st.form_submit_button("➕ สร้างกะงาน", use_container_width=True):
                                shift_datetime = datetime.combine(shift_date, datetime.min.time())
                                shift_start_dt = datetime.combine(shift_date, shift_start)
                                shift_end_dt = datetime.combine(shift_date, shift_end)
                                
                                result = create_shift(
                                    shift_user.id,
                                    shift_datetime,
                                    shift_start_dt,
                                    shift_end_dt,
                                    break_duration,
                                    shift_notes if shift_notes else None
                                )
                                
                                if result:
                                    st.success(f"✅ สร้างกะงานสำเร็จ")
                                    st.rerun()
                                else:
                                    st.error("❌ ไม่สามารถสร้างกะงานได้")
                    else:
                        st.info("ไม่มีพนักงาน")
                finally:
                    session.close()

if __name__ == "__main__":
    main()

