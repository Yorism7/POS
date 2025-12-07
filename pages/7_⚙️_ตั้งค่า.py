"""
Settings Page - ตั้งค่าระบบ
"""

import streamlit as st
import os
import shutil
from datetime import datetime, timedelta
from database.db import DB_PATH, DB_DIR, get_session
from database.models import Expense, ExpenseCategory, Promotion, PromotionRule, Product, Menu, Category
from utils.expense import (
    get_expenses_by_date_range, get_expense_summary, get_daily_expenses,
    create_expense_category, get_all_expense_categories
)
from utils.helpers import format_currency
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ตั้งค่า", page_icon="⚙️", layout="wide")

def main():
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth, require_role
    require_auth()
    
    st.title("⚙️ ตั้งค่า")
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        return
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏪 ตั้งค่าร้าน", "🧾 ตั้งค่าใบเสร็จ", "💾 สำรองข้อมูล", 
        "💰 จัดการค่าใช้จ่าย", "🎁 จัดการโปรโมชั่น", "📦 ข้อมูล Mockup"
    ])
    
    with tab1:
        # Database Connection Status
        st.subheader("🔌 สถานะการเชื่อมต่อ Database")
        
        # Get database info
        from database.db import DATABASE_URL, is_postgresql, is_mysql, is_sqlite, DB_PATH
        import os
        
        # Check if running on Streamlit Cloud
        is_streamlit_cloud = os.environ.get('STREAMLIT_CLOUD', '').lower() == 'true'
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if is_postgresql:
                st.success("✅ PostgreSQL (Supabase)")
                db_type = "PostgreSQL"
            elif is_mysql:
                st.success("✅ MySQL")
                db_type = "MySQL"
            else:
                if is_streamlit_cloud:
                    st.error("❌ SQLite (⚠️ ไม่ถาวร!)")
                else:
                    st.warning("⚠️ SQLite (Local)")
                db_type = "SQLite"
        
        with col2:
            if is_postgresql or is_mysql:
                # Parse connection info
                try:
                    if is_postgresql:
                        # postgresql://user:pass@host:port/db
                        parts = DATABASE_URL.replace('postgresql://', '').split('@')
                        if len(parts) == 2:
                            user_pass = parts[0].split(':')
                            host_db = parts[1].split('/')
                            if len(host_db) == 2:
                                host_port = host_db[0].split(':')
                                host = host_port[0] if len(host_port) > 0 else "Unknown"
                                port = host_port[1] if len(host_port) > 1 else "5432"
                                database = host_db[1] if len(host_db) > 1 else "Unknown"
                                
                                st.metric("Host", host)
                                st.metric("Port", port)
                                st.metric("Database", database)
                    elif is_mysql:
                        # mysql+pymysql://user:pass@host:port/db
                        parts = DATABASE_URL.replace('mysql+pymysql://', '').split('@')
                        if len(parts) == 2:
                            user_pass = parts[0].split(':')
                            host_db = parts[1].split('/')
                            if len(host_db) == 2:
                                host_port = host_db[0].split(':')
                                host = host_port[0] if len(host_port) > 0 else "Unknown"
                                port = host_port[1] if len(host_port) > 1 else "3306"
                                database = host_db[1] if len(host_db) > 1 else "Unknown"
                                
                                st.metric("Host", host)
                                st.metric("Port", port)
                                st.metric("Database", database)
                except Exception as e:
                    st.error(f"❌ ไม่สามารถอ่าน connection info: {e}")
            else:
                st.metric("Database File", DB_PATH if DB_PATH else "Unknown")
                if is_streamlit_cloud:
                    st.error("⚠️ ข้อมูลจะหายเมื่อ restart!")
        
        with col3:
                    # Test connection
            if st.button("🔍 ทดสอบการเชื่อมต่อ", use_container_width=True):
                with st.spinner("กำลังทดสอบการเชื่อมต่อ..."):
                    try:
                        session = get_session()
                        try:
                            # Try a simple query
                            from database.models import Category
                            count = session.query(Category).count()
                            st.success(f"✅ เชื่อมต่อสำเร็จ! (พบ {count} หมวดหมู่)")
                        except Exception as e:
                            st.error(f"❌ เชื่อมต่อล้มเหลว: {str(e)}")
                        finally:
                            session.close()
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        
        # Warnings and Info
        if is_sqlite and is_streamlit_cloud:
            st.error("""
            ⚠️ **คำเตือน: กำลังใช้ SQLite บน Streamlit Cloud!**
            
            - ข้อมูลจะหายเมื่อ app restart
            - ข้อมูลจะหายเมื่อ redeploy
            - **ไม่แนะนำสำหรับ production!**
            
            💡 **วิธีแก้ไข:**
            1. ไปที่ Streamlit Cloud Dashboard > Settings > Secrets
            2. เพิ่ม `[database]` section:
            ```toml
            [database]
            type = "postgresql"
            host = "aws-1-ap-southeast-1.pooler.supabase.com"
            port = 6543
            user = "postgres.thvvvsyujfzntvepmvzo"
            database = "postgres"
            password = "YOUR_PASSWORD"
            ```
            3. Restart app
            4. ดูคู่มือ: `วิธีตรวจสอบ_Streamlit_Cloud_Secrets_ถูกต้อง.md`
            """)
        elif is_postgresql:
            st.success("✅ กำลังใช้ Supabase PostgreSQL - ข้อมูลจะเก็บถาวร!")
            
            # Check if using Transaction Pooler
            if 'pooler.supabase.com' in DATABASE_URL and ':6543' in DATABASE_URL:
                st.info("✅ ใช้ Transaction Pooler (แนะนำสำหรับ Streamlit Cloud)")
            elif 'db.' in DATABASE_URL and '.supabase.co:5432' in DATABASE_URL:
                st.warning("⚠️ ใช้ Direct Connection - อาจจะ fail บน Streamlit Cloud! ควรใช้ Transaction Pooler (port 6543)")
        
        st.divider()
        
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
        
        # PromptPay QR Settings
        if 'promptpay_phone' not in st.session_state:
            st.session_state.promptpay_phone = ""
        if 'promptpay_citizen_id' not in st.session_state:
            st.session_state.promptpay_citizen_id = ""
        if 'promptpay_type' not in st.session_state:
            st.session_state.promptpay_type = "phone"  # phone or citizen_id
        
        with st.form("store_settings_form"):
            st.markdown("#### 📋 ข้อมูลร้าน")
            store_name = st.text_input("ชื่อร้าน *", value=st.session_state.store_name)
            store_address = st.text_area("ที่อยู่", value=st.session_state.store_address)
            store_phone = st.text_input("เบอร์โทรศัพท์", value=st.session_state.store_phone)
            store_tax_id = st.text_input("เลขประจำตัวผู้เสียภาษี", value=st.session_state.store_tax_id)
            
            st.divider()
            st.markdown("#### 💰 ตั้งค่าพร้อมเพย์ (PromptPay)")
            st.info("💡 ตั้งค่าข้อมูลพร้อมเพย์สำหรับสร้าง QR Code ชำระเงิน")
            
            promptpay_type = st.radio(
                "ประเภทบัญชีพร้อมเพย์",
                ["phone", "citizen_id"],
                format_func=lambda x: "เบอร์โทรศัพท์" if x == "phone" else "เลขบัตรประชาชน",
                index=0 if st.session_state.promptpay_type == "phone" else 1,
                horizontal=True
            )
            
            if promptpay_type == "phone":
                promptpay_phone = st.text_input(
                    "เบอร์โทรศัพท์พร้อมเพย์ *",
                    value=st.session_state.promptpay_phone,
                    placeholder="08XXXXXXXX",
                    help="กรอกเบอร์โทรศัพท์ที่ลงทะเบียนพร้อมเพย์ (ไม่ต้องใส่ - หรือเว้นวรรค)"
                )
                promptpay_citizen_id = ""
            else:
                promptpay_citizen_id = st.text_input(
                    "เลขบัตรประชาชนพร้อมเพย์ *",
                    value=st.session_state.promptpay_citizen_id,
                    placeholder="1234567890123",
                    help="กรอกเลขบัตรประชาชนที่ลงทะเบียนพร้อมเพย์ (13 หลัก)"
                )
                promptpay_phone = ""
            
            if st.form_submit_button("💾 บันทึก", type="primary", use_container_width=True):
                if store_name:
                    st.session_state.store_name = store_name
                    st.session_state.store_address = store_address
                    st.session_state.store_phone = store_phone
                    st.session_state.store_tax_id = store_tax_id
                    st.session_state.promptpay_type = promptpay_type
                    st.session_state.promptpay_phone = promptpay_phone
                    st.session_state.promptpay_citizen_id = promptpay_citizen_id
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
        
        st.divider()
        st.write("**💰 ตั้งค่าพร้อมเพย์:**")
        if st.session_state.promptpay_type == "phone":
            if st.session_state.promptpay_phone:
                st.write(f"ประเภท: เบอร์โทรศัพท์")
                st.write(f"เบอร์โทรศัพท์: {st.session_state.promptpay_phone}")
            else:
                st.warning("⚠️ ยังไม่ได้ตั้งค่าเบอร์โทรศัพท์พร้อมเพย์")
        else:
            if st.session_state.promptpay_citizen_id:
                st.write(f"ประเภท: เลขบัตรประชาชน")
                st.write(f"เลขบัตรประชาชน: {st.session_state.promptpay_citizen_id}")
            else:
                st.warning("⚠️ ยังไม่ได้ตั้งค่าเลขบัตรประชาชนพร้อมเพย์")
    
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
    
    with tab4:
        st.subheader("💰 จัดการค่าใช้จ่าย")
        
        expense_tab1, expense_tab2, expense_tab3 = st.tabs(["📝 บันทึกค่าใช้จ่าย", "📊 รายงานค่าใช้จ่าย", "📁 จัดการหมวดหมู่"])
        
        with expense_tab1:
            # Add expense
            with st.expander("➕ เพิ่มค่าใช้จ่าย", expanded=True):
                with st.form("add_expense_form"):
                    categories = get_all_expense_categories()
                    if categories:
                        category_options = {cat.id: cat.name for cat in categories}
                        selected_category_id = st.selectbox(
                            "หมวดหมู่ *",
                            options=list(category_options.keys()),
                            format_func=lambda x: category_options[x],
                            key="expense_category_select"
                        )
                    else:
                        st.warning("⚠️ ยังไม่มีหมวดหมู่ค่าใช้จ่าย กรุณาสร้างหมวดหมู่ก่อน")
                        selected_category_id = None
                    
                    expense_amount = st.number_input("จำนวนเงิน (฿) *", min_value=0.0, step=10.0, value=0.0, key="expense_amount_input")
                    expense_date = st.date_input("วันที่ *", value=datetime.now().date(), key="expense_date_input")
                    expense_description = st.text_area("คำอธิบาย", placeholder="รายละเอียดค่าใช้จ่าย...", key="expense_desc_input")
                    
                    if st.form_submit_button("➕ เพิ่มค่าใช้จ่าย", type="primary", use_container_width=True):
                        if selected_category_id and expense_amount > 0:
                            session = get_session()
                            try:
                                expense = Expense(
                                    category_id=selected_category_id,
                                    amount=expense_amount,
                                    description=expense_description if expense_description else None,
                                    expense_date=datetime.combine(expense_date, datetime.min.time()),
                                    created_by=st.session_state.user_id
                                )
                                session.add(expense)
                                session.commit()
                                st.success(f"✅ บันทึกค่าใช้จ่าย {format_currency(expense_amount)} สำเร็จ")
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                            finally:
                                session.close()
                        else:
                            st.warning("⚠️ กรุณากรอกหมวดหมู่และจำนวนเงิน")
            
            # Expense list
            st.divider()
            st.write("**📋 รายการค่าใช้จ่าย**")
            
            col_start, col_end = st.columns(2)
            with col_start:
                expense_start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30), key="expense_list_start")
            with col_end:
                expense_end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date(), key="expense_list_end")
            
            expenses = get_expenses_by_date_range(
                datetime.combine(expense_start_date, datetime.min.time()),
                datetime.combine(expense_end_date, datetime.max.time())
            )
            
            if expenses:
                expense_data = []
                for exp in expenses:
                    expense_data.append({
                        'วันที่': exp.expense_date.strftime('%d/%m/%Y'),
                        'หมวดหมู่': exp.category.name,
                        'จำนวนเงิน': format_currency(exp.amount),
                        'คำอธิบาย': exp.description or '-',
                        'ผู้บันทึก': exp.creator.username if exp.creator else '-'
                    })
                
                df = pd.DataFrame(expense_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Total
                total_expenses = sum(e.amount for e in expenses)
                st.metric("💰 ค่าใช้จ่ายรวม", format_currency(total_expenses))
            else:
                st.info("ไม่มีค่าใช้จ่ายในช่วงเวลานี้")
        
        with expense_tab2:
            st.write("**📊 รายงานค่าใช้จ่าย**")
            
            report_start, report_end = st.columns(2)
            with report_start:
                report_start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30), key="expense_report_start")
            with report_end:
                report_end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date(), key="expense_report_end")
            
            summary = get_expense_summary(
                datetime.combine(report_start_date, datetime.min.time()),
                datetime.combine(report_end_date, datetime.max.time())
            )
            
            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 ค่าใช้จ่ายรวม", format_currency(summary['total']))
            with col2:
                st.metric("📁 จำนวนหมวดหมู่", len(summary['by_category']))
            
            # Chart by category
            if summary['by_category']:
                st.divider()
                st.write("**📊 ค่าใช้จ่ายตามหมวดหมู่**")
                
                df_category = pd.DataFrame(summary['by_category'])
                fig = px.pie(
                    df_category,
                    values='total',
                    names='name',
                    title="ค่าใช้จ่ายตามหมวดหมู่"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                df_category['total'] = df_category['total'].apply(lambda x: format_currency(x))
                df_category.columns = ['ID', 'หมวดหมู่', 'จำนวนเงิน']
                st.dataframe(df_category[['หมวดหมู่', 'จำนวนเงิน']], use_container_width=True, hide_index=True)
            
            # Daily expenses chart
            st.divider()
            st.write("**📈 ค่าใช้จ่ายรายวัน**")
            daily_expenses = get_daily_expenses(
                datetime.combine(report_start_date, datetime.min.time()),
                datetime.combine(report_end_date, datetime.max.time())
            )
            
            if daily_expenses:
                df_daily = pd.DataFrame(daily_expenses)
                df_daily['date'] = pd.to_datetime(df_daily['date'])
                
                fig = px.line(
                    df_daily,
                    x='date',
                    y='total',
                    labels={'date': 'วันที่', 'total': 'ค่าใช้จ่าย (฿)'},
                    title="ค่าใช้จ่ายรายวัน"
                )
                fig.update_layout(height=400, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลค่าใช้จ่าย")
        
        with expense_tab3:
            st.write("**📁 จัดการหมวดหมู่ค่าใช้จ่าย**")
            
            # Add category
            with st.expander("➕ เพิ่มหมวดหมู่"):
                with st.form("add_category_form"):
                    cat_name = st.text_input("ชื่อหมวดหมู่ *", placeholder="เช่น ค่าเช่า, ค่าไฟ, วัตถุดิบ...", key="new_category_name")
                    cat_description = st.text_area("คำอธิบาย", placeholder="รายละเอียดหมวดหมู่...", key="new_category_desc")
                    
                    if st.form_submit_button("➕ เพิ่มหมวดหมู่", type="primary", use_container_width=True):
                        if cat_name:
                            result = create_expense_category(cat_name, cat_description if cat_description else None)
                            if result:
                                st.success(f"✅ เพิ่มหมวดหมู่ {cat_name} สำเร็จ")
                                st.rerun()
                            else:
                                st.error("❌ ไม่สามารถเพิ่มหมวดหมู่ได้")
                        else:
                            st.warning("⚠️ กรุณากรอกชื่อหมวดหมู่")
            
            # Category list
            st.divider()
            st.write("**📋 รายการหมวดหมู่**")
            
            categories = get_all_expense_categories()
            if categories:
                for cat in categories:
                    with st.expander(f"📁 {cat.name}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**คำอธิบาย:** {cat.description or '-'}")
                            st.write(f"**สถานะ:** {'เปิดใช้งาน' if cat.is_active else 'ปิดใช้งาน'}")
                        with col2:
                            if st.button("🗑️ ลบ", key=f"delete_category_{cat.id}", use_container_width=True):
                                session = get_session()
                                try:
                                    # Check if category has expenses
                                    expense_count = session.query(Expense).filter(Expense.category_id == cat.id).count()
                                    if expense_count > 0:
                                        st.warning(f"⚠️ ไม่สามารถลบได้ มีค่าใช้จ่าย {expense_count} รายการ")
                                    else:
                                        session.delete(cat)
                                        session.commit()
                                        st.success(f"✅ ลบหมวดหมู่ {cat.name} สำเร็จ")
                                        st.rerun()
                                except Exception as e:
                                    session.rollback()
                                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                finally:
                                    session.close()
            else:
                st.info("ยังไม่มีหมวดหมู่ค่าใช้จ่าย")
                
                # Create default categories
                if st.button("➕ สร้างหมวดหมู่เริ่มต้น", use_container_width=True):
                    default_categories = [
                        ("ค่าเช่า", "ค่าเช่าร้าน"),
                        ("ค่าไฟ", "ค่าไฟฟ้า"),
                        ("ค่าน้ำ", "ค่าน้ำประปา"),
                        ("วัตถุดิบ", "ซื้อวัตถุดิบ"),
                        ("ค่าจ้าง", "ค่าจ้างพนักงาน"),
                        ("อื่นๆ", "ค่าใช้จ่ายอื่นๆ")
                    ]
                    
                    created = 0
                    for name, desc in default_categories:
                        result = create_expense_category(name, desc)
                        if result:
                            created += 1
                    
                    if created > 0:
                        st.success(f"✅ สร้างหมวดหมู่เริ่มต้น {created} หมวดหมู่สำเร็จ")
                        st.rerun()
    
    with tab5:
        st.subheader("🎁 จัดการโปรโมชั่น")
        
        # Add promotion
        with st.expander("➕ เพิ่มโปรโมชั่น", expanded=False):
            with st.form("add_promotion_form"):
                promo_name = st.text_input("ชื่อโปรโมชั่น *", key="promo_name")
                promo_description = st.text_area("คำอธิบาย", key="promo_desc")
                promo_type = st.selectbox(
                    "ประเภทโปรโมชั่น *",
                    ["discount", "buy_x_get_y", "time_based", "member_only"],
                    format_func=lambda x: {
                        "discount": "ส่วนลด",
                        "buy_x_get_y": "ซื้อ X แถม Y",
                        "time_based": "ตามเวลา",
                        "member_only": "สมาชิกเท่านั้น"
                    }[x],
                    key="promo_type_select"
                )
                
                discount_type = None
                discount_value = None
                max_discount = None
                buy_quantity = None
                get_quantity = None
                time_start = None
                time_end = None
                days_of_week = None
                
                if promo_type == "discount":
                    discount_type = st.selectbox("ประเภทส่วนลด", ["percent", "fixed"], 
                                                format_func=lambda x: "เปอร์เซ็นต์" if x == "percent" else "จำนวนเงิน",
                                                key="promo_discount_type")
                    discount_value = st.number_input("ค่าส่วนลด", min_value=0.0, step=1.0, key="promo_discount_value")
                    if discount_type == "percent":
                        max_discount = st.number_input("ส่วนลดสูงสุด (฿)", min_value=0.0, step=10.0, value=0.0, key="promo_max_discount")
                        if max_discount == 0:
                            max_discount = None
                elif promo_type == "buy_x_get_y":
                    buy_quantity = st.number_input("ซื้อ (X)", min_value=1, step=1, value=1, key="promo_buy_qty")
                    get_quantity = st.number_input("แถม (Y)", min_value=1, step=1, value=1, key="promo_get_qty")
                elif promo_type == "time_based":
                    time_start = st.time_input("เวลาเริ่ม", value=datetime.now().time(), key="promo_time_start")
                    time_end = st.time_input("เวลาสิ้นสุด", value=datetime.now().time(), key="promo_time_end")
                    days_of_week = st.multiselect(
                        "วันในสัปดาห์",
                        ["0", "1", "2", "3", "4", "5", "6"],
                        format_func=lambda x: ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"][int(x)],
                        key="promo_days"
                    )
                    days_of_week = ",".join(days_of_week) if days_of_week else None
                
                min_purchase = st.number_input("ยอดซื้อขั้นต่ำ (฿)", min_value=0.0, step=10.0, value=0.0, key="promo_min_purchase")
                
                col_start, col_end = st.columns(2)
                with col_start:
                    valid_from = st.date_input("วันที่เริ่มต้น", value=datetime.now().date(), key="promo_valid_from")
                with col_end:
                    valid_until = st.date_input("วันที่สิ้นสุด", value=datetime.now().date() + timedelta(days=30), key="promo_valid_until")
                
                if st.form_submit_button("➕ เพิ่มโปรโมชั่น", type="primary", use_container_width=True):
                    if promo_name:
                        session = get_session()
                        try:
                            promotion = Promotion(
                                name=promo_name,
                                description=promo_description if promo_description else None,
                                promotion_type=promo_type,
                                discount_type=discount_type,
                                discount_value=discount_value,
                                min_purchase=min_purchase,
                                max_discount=max_discount,
                                buy_quantity=buy_quantity,
                                get_quantity=get_quantity,
                                time_start=time_start.strftime('%H:%M') if time_start else None,
                                time_end=time_end.strftime('%H:%M') if time_end else None,
                                days_of_week=days_of_week,
                                valid_from=datetime.combine(valid_from, datetime.min.time()),
                                valid_until=datetime.combine(valid_until, datetime.max.time()),
                                is_active=True
                            )
                            session.add(promotion)
                            session.commit()
                            st.success(f"✅ เพิ่มโปรโมชั่น {promo_name} สำเร็จ")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        finally:
                            session.close()
                    else:
                        st.warning("⚠️ กรุณากรอกชื่อโปรโมชั่น")
        
        # Promotion list
        st.divider()
        st.write("**📋 รายการโปรโมชั่น**")
        
        session = get_session()
        try:
            promotions = session.query(Promotion).order_by(Promotion.created_at.desc()).all()
            
            if promotions:
                for promo in promotions:
                    status = "✅ เปิดใช้งาน" if promo.is_active else "❌ ปิดใช้งาน"
                    with st.expander(f"🎁 {promo.name} ({status})"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**ประเภท:** {promo.promotion_type}")
                            if promo.description:
                                st.write(f"**คำอธิบาย:** {promo.description}")
                            st.write(f"**ยอดซื้อขั้นต่ำ:** {format_currency(promo.min_purchase)}")
                            st.write(f"**วันที่เริ่ม:** {promo.valid_from.strftime('%d/%m/%Y')}")
                            st.write(f"**วันที่สิ้นสุด:** {promo.valid_until.strftime('%d/%m/%Y')}")
                        with col2:
                            if promo.is_active:
                                if st.button("❌ ปิดใช้งาน", key=f"deactivate_promo_{promo.id}", use_container_width=True):
                                    promo.is_active = False
                                    session.commit()
                                    st.success("✅ ปิดใช้งานโปรโมชั่นสำเร็จ")
                                    st.rerun()
                            else:
                                if st.button("✅ เปิดใช้งาน", key=f"activate_promo_{promo.id}", use_container_width=True):
                                    promo.is_active = True
                                    session.commit()
                                    st.success("✅ เปิดใช้งานโปรโมชั่นสำเร็จ")
                                    st.rerun()
                            
                            if st.button("🗑️ ลบ", key=f"delete_promo_{promo.id}", use_container_width=True):
                                session.delete(promo)
                                session.commit()
                                st.success("✅ ลบโปรโมชั่นสำเร็จ")
                                st.rerun()
            else:
                st.info("ยังไม่มีโปรโมชั่น")
        finally:
            session.close()
    
    with tab6:
        st.subheader("📦 สร้างข้อมูล Mockup")
        st.info("💡 สร้างข้อมูลตัวอย่างสำหรับทดสอบระบบ รวมสินค้า, เมนูก๋วยเตี๋ยว, และวัตถุดิบ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 ข้อมูลที่จะสร้าง")
            st.markdown("""
            **หมวดหมู่ (4 หมวด):**
            - อาหารแห้ง
            - เครื่องดื่ม
            - วัตถุดิบ
            - อื่นๆ
            
            **สินค้า (30 รายการ):**
            - อาหารแห้ง: 10 รายการ (บะหมี่, ข้าวสาร, น้ำตาล, เกลือ, น้ำมันพืช, ซอสหอยนางรม, น้ำปลา, พริกแกง, กะทิ, ถั่วลิสง)
            - เครื่องดื่ม: 8 รายการ (น้ำดื่ม, โค้ก, เป๊ปซี่, น้ำส้ม, ชาเขียว, กาแฟสำเร็จรูป, นม, น้ำแข็ง)
            - วัตถุดิบ: 12 รายการ (เส้นก๋วยเตี๋ยว, หมูสับ, ไก่สับ, กุ้ง, ไข่ไก่, ผักบุ้ง, ถั่วงอก, ต้นหอม, ผักชี, พริกขี้หนู, กระเทียม, หอมแดง)
            """)
        
        with col2:
            st.markdown("#### 🍜 เมนูก๋วยเตี๋ยว (20 เมนู)")
            st.markdown("""
            - ก๋วยเตี๋ยวน้ำใส - ฿50
            - ก๋วยเตี๋ยวต้มยำ - ฿55
            - ก๋วยเตี๋ยวน้ำใสไก่ - ฿50
            - ก๋วยเตี๋ยวต้มยำกุ้ง - ฿70
            - ก๋วยเตี๋ยวผัดซีอิ๊ว - ฿55
            - ก๋วยเตี๋ยวแห้ง - ฿50
            - และอีก 14 เมนู...
            
            **ทุกเมนูมี BOM (Bill of Materials) ครบถ้วน**
            """)
        
        st.divider()
        
        # ตรวจสอบข้อมูลที่มีอยู่แล้ว
        db_session = get_session()
        try:
            existing_products = db_session.query(Product).count()
            existing_menus = db_session.query(Menu).count()
            existing_categories = db_session.query(Category).count()
            
            st.markdown("#### 📊 ข้อมูลปัจจุบัน")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("หมวดหมู่", existing_categories)
            with col2:
                st.metric("สินค้า", existing_products)
            with col3:
                st.metric("เมนู", existing_menus)
        finally:
            db_session.close()
        
        st.divider()
        
        # ปุ่มสร้างข้อมูล Mockup
        st.markdown("#### 🚀 สร้างข้อมูล Mockup")
        
        if st.button("✨ สร้างข้อมูล Mockup", type="primary", use_container_width=True):
            with st.spinner("🔄 กำลังสร้างข้อมูล Mockup... กรุณารอสักครู่"):
                try:
                    # Import และเรียกใช้ฟังก์ชันสร้างข้อมูล
                    from scripts.create_mockup_data import create_mockup_data
                    
                    # Capture output
                    import io
                    import sys
                    from contextlib import redirect_stdout, redirect_stderr
                    
                    output = io.StringIO()
                    error_output = io.StringIO()
                    
                    with redirect_stdout(output), redirect_stderr(error_output):
                        create_mockup_data()
                    
                    stdout_text = output.getvalue()
                    stderr_text = error_output.getvalue()
                    
                    # แสดงผลลัพธ์
                    if stderr_text:
                        st.error(f"❌ เกิดข้อผิดพลาด:\n```\n{stderr_text}\n```")
                    else:
                        st.success("✅ สร้างข้อมูล Mockup สำเร็จ!")
                        
                        # แสดงสรุป
                        st.markdown("#### 📝 สรุปข้อมูลที่สร้าง")
                        st.info(f"""
                        - ✅ หมวดหมู่: 4 หมวด
                        - ✅ สินค้า: 30 รายการ
                        - ✅ เมนูก๋วยเตี๋ยว: 20 เมนู พร้อม BOM
                        """)
                        
                        # แสดง debug output (ถ้ามี)
                        if stdout_text and "[DEBUG]" in stdout_text:
                            with st.expander("🔍 ดูรายละเอียด"):
                                st.code(stdout_text)
                        
                        st.balloons()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                    import traceback
                    with st.expander("🔍 ดูรายละเอียดข้อผิดพลาด"):
                        st.code(traceback.format_exc())
        
        # ปุ่มลบข้อมูล Mockup (ถ้าต้องการ)
        st.divider()
        st.markdown("#### 🗑️ ลบข้อมูล Mockup")
        st.warning("⚠️ การลบข้อมูล Mockup จะลบสินค้าและเมนูทั้งหมด (ยกเว้นข้อมูลที่มีการใช้งาน)")
        
        if st.button("🗑️ ลบข้อมูล Mockup", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_delete_mockup', False):
                with st.spinner("🔄 กำลังลบข้อมูล Mockup..."):
                    try:
                        from scripts.clear_mockup_data import clear_mockup_data
                        
                        import io
                        from contextlib import redirect_stdout, redirect_stderr
                        
                        output = io.StringIO()
                        error_output = io.StringIO()
                        
                        with redirect_stdout(output), redirect_stderr(error_output):
                            clear_mockup_data()
                        
                        stderr_text = error_output.getvalue()
                        
                        if stderr_text:
                            st.error(f"❌ เกิดข้อผิดพลาด:\n```\n{stderr_text}\n```")
                        else:
                            st.success("✅ ลบข้อมูล Mockup สำเร็จ!")
                            st.session_state.confirm_delete_mockup = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        import traceback
                        with st.expander("🔍 ดูรายละเอียดข้อผิดพลาด"):
                            st.code(traceback.format_exc())
            else:
                st.session_state.confirm_delete_mockup = True
                st.warning("⚠️ กรุณากดปุ่มอีกครั้งเพื่อยืนยันการลบ")

if __name__ == "__main__":
    main()

