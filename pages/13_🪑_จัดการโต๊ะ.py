"""
Table Management Page - จัดการโต๊ะและสร้าง QR Code
"""

import streamlit as st
from database.db import get_session
from database.models import Table
from utils.order_utils import generate_table_qr_code
import base64
from datetime import datetime

st.set_page_config(page_title="จัดการโต๊ะ", page_icon="🪑", layout="wide")

def main():
    # ต้องล็อคอิน
    from utils.auth import require_auth
    require_auth()
    
    st.title("🪑 จัดการโต๊ะ")
    
    session = get_session()
    try:
        # แท็บ
        tab1, tab2 = st.tabs(["📋 รายการโต๊ะ", "➕ เพิ่มโต๊ะ"])
        
        with tab1:
            st.subheader("📋 รายการโต๊ะทั้งหมด")
            
            tables = session.query(Table).order_by(Table.table_number).all()
            
            if not tables:
                st.info("📭 ยังไม่มีโต๊ะ")
            else:
                # แสดงโต๊ะใน grid
                cols = st.columns(3)
                for idx, table in enumerate(tables):
                    with cols[idx % 3]:
                        with st.container():
                            status_icon = "🟢" if table.is_active else "🔴"
                            st.write(f"{status_icon} **โต๊ะ {table.table_number}**")
                            if table.name:
                                st.caption(table.name)
                            st.caption(f"ที่นั่ง: {table.capacity} คน")
                            
                            # แสดง QR Code
                            if table.qr_code:
                                st.image(
                                    f"data:image/png;base64,{table.qr_code}",
                                    caption=f"QR Code สำหรับโต๊ะ {table.table_number}",
                                    width=200
                                )
                            
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️ แก้ไข", key=f"edit_{table.id}", width='stretch'):
                                    st.session_state[f"editing_table_{table.id}"] = True
                                    st.rerun()
                            
                            with col_del:
                                if st.button("🗑️ ลบ", key=f"delete_{table.id}", width='stretch'):
                                    st.session_state[f"confirm_delete_{table.id}"] = True
                                    st.rerun()
                            
                            # แก้ไข
                            if st.session_state.get(f"editing_table_{table.id}", False):
                                with st.form(f"edit_table_form_{table.id}"):
                                    new_name = st.text_input("ชื่อโต๊ะ", value=table.name or "", key=f"table_name_{table.id}")
                                    new_capacity = st.number_input("จำนวนที่นั่ง", min_value=1, value=table.capacity, key=f"table_capacity_{table.id}")
                                    is_active = st.checkbox("เปิดใช้งาน", value=table.is_active, key=f"table_active_{table.id}")
                                    
                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        if st.form_submit_button("💾 บันทึก", width='stretch'):
                                            table.name = new_name if new_name else None
                                            table.capacity = new_capacity
                                            table.is_active = is_active
                                            session.commit()
                                            st.session_state[f"editing_table_{table.id}"] = False
                                            st.success("✅ บันทึกสำเร็จ")
                                            st.rerun()
                                    with col_cancel:
                                        if st.form_submit_button("❌ ยกเลิก", width='stretch'):
                                            st.session_state[f"editing_table_{table.id}"] = False
                                            st.rerun()
                            
                            # ยืนยันลบ
                            if st.session_state.get(f"confirm_delete_{table.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบโต๊ะ {table.table_number}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_{table.id}", width='stretch'):
                                        session.delete(table)
                                        session.commit()
                                        st.session_state[f"confirm_delete_{table.id}"] = False
                                        st.success("✅ ลบสำเร็จ")
                                        st.rerun()
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_{table.id}", width='stretch'):
                                        st.session_state[f"confirm_delete_{table.id}"] = False
                                        st.rerun()
                            
                            # สร้าง/อัพเดท QR Code
                            st.divider()
                            if st.button("📱 สร้าง QR Code", key=f"qr_{table.id}", width='stretch'):
                                try:
                                    # รับ base URL
                                    base_url = st.text_input(
                                        "Base URL ของแอป",
                                        value="https://pos-ez.streamlit.app",
                                        key=f"base_url_{table.id}"
                                    )
                                    
                                    if base_url:
                                        qr_img, qr_url = generate_table_qr_code(table.id, base_url)
                                        table.qr_code = qr_img
                                        session.commit()
                                        
                                        st.success("✅ สร้าง QR Code สำเร็จ")
                                        st.image(
                                            f"data:image/png;base64,{qr_img}",
                                            caption=f"QR Code สำหรับโต๊ะ {table.table_number}",
                                            width=300
                                        )
                                        st.code(qr_url, language=None)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                            
                            st.divider()
        
        with tab2:
            st.subheader("➕ เพิ่มโต๊ะใหม่")
            
            with st.form("add_table_form"):
                table_number = st.text_input("หมายเลขโต๊ะ *", placeholder="เช่น T1, T2, 1, 2...")
                table_name = st.text_input("ชื่อโต๊ะ (ไม่บังคับ)", placeholder="เช่น โต๊ะริมหน้าต่าง")
                capacity = st.number_input("จำนวนที่นั่ง", min_value=1, value=4)
                is_active = st.checkbox("เปิดใช้งาน", value=True)
                
                if st.form_submit_button("➕ เพิ่มโต๊ะ", width='stretch', type="primary"):
                    if not table_number:
                        st.error("❌ กรุณากรอกหมายเลขโต๊ะ")
                    else:
                        # ตรวจสอบว่ามีโต๊ะนี้อยู่แล้วหรือไม่
                        existing = session.query(Table).filter(Table.table_number == table_number).first()
                        if existing:
                            st.error(f"❌ มีโต๊ะ {table_number} อยู่แล้ว")
                        else:
                            new_table = Table(
                                table_number=table_number,
                                name=table_name if table_name else None,
                                capacity=capacity,
                                is_active=is_active
                            )
                            session.add(new_table)
                            session.commit()
                            
                            st.success(f"✅ เพิ่มโต๊ะ {table_number} สำเร็จ")
                            
                            # สร้าง QR Code อัตโนมัติ
                            try:
                                base_url = st.text_input(
                                    "Base URL ของแอป (สำหรับสร้าง QR Code)",
                                    value="https://pos-ez.streamlit.app",
                                    key="base_url_new"
                                )
                                
                                if base_url:
                                    qr_img, qr_url = generate_table_qr_code(new_table.id, base_url)
                                    new_table.qr_code = qr_img
                                    session.commit()
                                    st.success("✅ สร้าง QR Code สำเร็จ")
                                    st.image(
                                        f"data:image/png;base64,{qr_img}",
                                        caption=f"QR Code สำหรับโต๊ะ {new_table.table_number}",
                                        width=300
                                    )
                            except Exception as e:
                                st.warning(f"⚠️ ไม่สามารถสร้าง QR Code ได้: {str(e)}")
                            
                            st.rerun()
    
    finally:
        session.close()

if __name__ == "__main__":
    main()

