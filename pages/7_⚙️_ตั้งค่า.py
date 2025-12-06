"""
Settings Page - ตั้งค่าระบบ
"""

import streamlit as st
import os
import shutil
from datetime import datetime
from database.db import DB_PATH, DB_DIR

st.set_page_config(page_title="ตั้งค่า", page_icon="⚙️", layout="wide")

def main():
    st.title("⚙️ ตั้งค่า")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏪 ตั้งค่าร้าน", "🧾 ตั้งค่าใบเสร็จ", "💾 สำรองข้อมูล"])
    
    with tab1:
        st.subheader("🏪 ตั้งค่าร้าน")
        
        # Store settings (stored in session state for now, can be moved to database)
        if 'store_name' not in st.session_state:
            st.session_state.store_name = "ร้านขายของชำและอาหารตามสั่ง"
        if 'store_address' not in st.session_state:
            st.session_state.store_address = ""
        if 'store_phone' not in st.session_state:
            st.session_state.store_phone = ""
        if 'store_tax_id' not in st.session_state:
            st.session_state.store_tax_id = ""
        
        with st.form("store_settings_form"):
            store_name = st.text_input("ชื่อร้าน *", value=st.session_state.store_name)
            store_address = st.text_area("ที่อยู่", value=st.session_state.store_address)
            store_phone = st.text_input("เบอร์โทรศัพท์", value=st.session_state.store_phone)
            store_tax_id = st.text_input("เลขประจำตัวผู้เสียภาษี", value=st.session_state.store_tax_id)
            
            if st.form_submit_button("💾 บันทึก", type="primary", use_container_width=True):
                if store_name:
                    st.session_state.store_name = store_name
                    st.session_state.store_address = store_address
                    st.session_state.store_phone = store_phone
                    st.session_state.store_tax_id = store_tax_id
                    st.success("✅ บันทึกการตั้งค่าสำเร็จ")
                else:
                    st.warning("⚠️ กรุณากรอกชื่อร้าน")
        
        # Display current settings
        st.divider()
        st.write("**การตั้งค่าปัจจุบัน:**")
        st.write(f"ชื่อร้าน: {st.session_state.store_name}")
        st.write(f"ที่อยู่: {st.session_state.store_address or '-'}")
        st.write(f"เบอร์โทรศัพท์: {st.session_state.store_phone or '-'}")
        st.write(f"เลขประจำตัวผู้เสียภาษี: {st.session_state.store_tax_id or '-'}")
    
    with tab2:
        st.subheader("🧾 ตั้งค่าใบเสร็จ")
        
        # Receipt settings
        if 'receipt_footer' not in st.session_state:
            st.session_state.receipt_footer = "ขอบคุณที่ใช้บริการ"
        if 'receipt_show_tax' not in st.session_state:
            st.session_state.receipt_show_tax = False
        if 'receipt_tax_rate' not in st.session_state:
            st.session_state.receipt_tax_rate = 7.0
        
        with st.form("receipt_settings_form"):
            receipt_footer = st.text_input("ข้อความท้ายใบเสร็จ", value=st.session_state.receipt_footer)
            receipt_show_tax = st.checkbox("แสดงภาษีมูลค่าเพิ่ม", value=st.session_state.receipt_show_tax)
            receipt_tax_rate = st.number_input("อัตราภาษี (%)", min_value=0.0, max_value=100.0, value=st.session_state.receipt_tax_rate, step=0.1)
            
            if st.form_submit_button("💾 บันทึก", type="primary", use_container_width=True):
                st.session_state.receipt_footer = receipt_footer
                st.session_state.receipt_show_tax = receipt_show_tax
                st.session_state.receipt_tax_rate = receipt_tax_rate
                st.success("✅ บันทึกการตั้งค่าใบเสร็จสำเร็จ")
        
        # Display current settings
        st.divider()
        st.write("**การตั้งค่าใบเสร็จปัจจุบัน:**")
        st.write(f"ข้อความท้ายใบเสร็จ: {st.session_state.receipt_footer}")
        st.write(f"แสดงภาษีมูลค่าเพิ่ม: {'ใช่' if st.session_state.receipt_show_tax else 'ไม่ใช่'}")
        if st.session_state.receipt_show_tax:
            st.write(f"อัตราภาษี: {st.session_state.receipt_tax_rate}%")
    
    with tab3:
        st.subheader("💾 สำรองข้อมูล")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**สำรองข้อมูล**")
            st.write("ดาวน์โหลดไฟล์ฐานข้อมูลเพื่อสำรองข้อมูล")
            
            if os.path.exists(DB_PATH):
                file_size = os.path.getsize(DB_PATH)
                st.info(f"ขนาดไฟล์: {file_size / 1024:.2f} KB")
                
                with open(DB_PATH, 'rb') as f:
                    st.download_button(
                        "📥 ดาวน์โหลดฐานข้อมูล",
                        f.read(),
                        file_name=f"pos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                        mime="application/x-sqlite3",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ ไม่พบไฟล์ฐานข้อมูล")
        
        with col2:
            st.write("**กู้คืนข้อมูล**")
            st.write("อัปโหลดไฟล์ฐานข้อมูลเพื่อกู้คืนข้อมูล")
            st.warning("⚠️ การกู้คืนข้อมูลจะเขียนทับข้อมูลปัจจุบันทั้งหมด!")
            
            uploaded_file = st.file_uploader(
                "เลือกไฟล์ฐานข้อมูล",
                type=['db', 'sqlite', 'sqlite3'],
                help="อัปโหลดไฟล์ .db หรือ .sqlite"
            )
            
            if uploaded_file is not None:
                if st.button("🔄 กู้คืนข้อมูล", type="primary", use_container_width=True):
                    try:
                        # Backup current database
                        if os.path.exists(DB_PATH):
                            backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            shutil.copy2(DB_PATH, backup_path)
                            st.info(f"✅ สำรองข้อมูลปัจจุบันไว้ที่: {backup_path}")
                        
                        # Save uploaded file
                        with open(DB_PATH, 'wb') as f:
                            f.write(uploaded_file.read())
                        
                        st.success("✅ กู้คืนข้อมูลสำเร็จ")
                        st.info("⚠️ กรุณารีสตาร์ทแอปพลิเคชันเพื่อให้การเปลี่ยนแปลงมีผล")
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        
        st.divider()
        st.write("**ข้อมูลระบบ**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**เส้นทางฐานข้อมูล:**")
            st.code(DB_PATH)
        with col2:
            if os.path.exists(DB_PATH):
                mod_time = datetime.fromtimestamp(os.path.getmtime(DB_PATH))
                st.write(f"**แก้ไขล่าสุด:**")
                st.write(mod_time.strftime("%d/%m/%Y %H:%M:%S"))
        
        # Database info
        st.divider()
        st.write("**ข้อมูลฐานข้อมูล**")
        
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            st.write(f"**จำนวนตาราง:** {len(tables)}")
            st.write("**รายชื่อตาราง:**")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                st.write(f"- {table[0]}: {count} แถว")
            
            conn.close()
        except Exception as e:
            st.error(f"❌ ไม่สามารถอ่านข้อมูลฐานข้อมูล: {str(e)}")

if __name__ == "__main__":
    main()

