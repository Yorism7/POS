"""
Void Sale Page - ยกเลิกการขาย
"""

import streamlit as st
from datetime import datetime, timedelta
from database.db import get_session
from database.models import Sale, SaleItem, Product, Menu, User
from utils.helpers import format_currency, format_date
from utils.pagination import paginate_items
import pandas as pd

st.set_page_config(page_title="ยกเลิกการขาย", page_icon="🔄", layout="wide")

def void_sale(sale_id: int, reason: str, user_id: int):
    """Void a sale and restore stock"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return False, "ไม่พบการขาย"
        
        if sale.is_void:
            return False, "การขายนี้ถูกยกเลิกไปแล้ว"
        
        # Restore stock for each item
        for item in sale.sale_items:
            if item.item_type == 'product' and item.product_id:
                product = session.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock_quantity += item.quantity
            
            elif item.item_type == 'menu' and item.menu_id:
                menu = session.query(Menu).filter(Menu.id == item.menu_id).first()
                if menu:
                    for menu_item in menu.menu_items:
                        if menu_item.product:
                            product = session.query(Product).filter(
                                Product.id == menu_item.product.id
                            ).first()
                            if product:
                                quantity_needed = menu_item.quantity * item.quantity
                                product.stock_quantity += quantity_needed
        
        # Mark sale as void
        sale.is_void = True
        sale.void_reason = reason
        sale.voided_by = user_id
        sale.voided_at = datetime.now()
        
        session.commit()
        return True, "ยกเลิกการขายสำเร็จ"
    except Exception as e:
        session.rollback()
        return False, f"เกิดข้อผิดพลาด: {str(e)}"
    finally:
        session.close()

def main():
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth, require_role
    require_auth()
    
    st.title("🔄 ยกเลิกการขาย (Void Sale)")
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถยกเลิกการขายได้")
        return
    
    # Search and filter
    col1, col2, col3 = st.columns(3)
    with col1:
        sale_id_search = st.text_input("🔍 ค้นหาเลขที่การขาย", placeholder="เช่น 000001")
    with col2:
        days = st.number_input("แสดงย้อนหลัง (วัน)", min_value=1, value=7, step=1)
    with col3:
        show_voided = st.checkbox("แสดงการขายที่ยกเลิกแล้ว", value=False)
    
    session = get_session()
    try:
        # Query sales
        query = session.query(Sale)
        
        if sale_id_search and sale_id_search.strip():
            try:
                sale_id = int(sale_id_search.strip())
                query = query.filter(Sale.id == sale_id)
            except ValueError:
                st.warning("⚠️ กรุณากรอกเลขที่การขายเป็นตัวเลข")
                query = query.filter(Sale.id == -1)  # No results
        
        if not show_voided:
            query = query.filter(Sale.is_void == False)
        
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(Sale.created_at >= start_date)
        
        all_sales = query.order_by(Sale.created_at.desc()).all()
        
        # Pagination
        if 'void_sale_page' not in st.session_state:
            st.session_state.void_sale_page = 1
        
        items_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 50], index=0, key="void_sale_items_per_page")
        
        paginated_sales, total_items, total_pages, current_page = paginate_items(
            all_sales,
            st.session_state.void_sale_page,
            items_per_page
        )
        
        st.info(f"📊 แสดง {len(paginated_sales)} จาก {total_items} รายการ (หน้า {current_page}/{total_pages})")
        
        # Pagination controls
        if total_pages > 1:
            col_prev, col_page, col_next = st.columns([1, 3, 1])
            with col_prev:
                if st.button("◀️ ก่อนหน้า", disabled=(current_page == 1), width='stretch', key="void_prev"):
                    st.session_state.void_sale_page = max(1, current_page - 1)
                    st.rerun()
            with col_page:
                st.write(f"หน้า {current_page} / {total_pages}")
            with col_next:
                if st.button("ถัดไป ▶️", disabled=(current_page == total_pages), width='stretch', key="void_next"):
                    st.session_state.void_sale_page = min(total_pages, current_page + 1)
                    st.rerun()
        
        if paginated_sales:
            for sale in paginated_sales:
                void_status = "🔴 ยกเลิกแล้ว" if sale.is_void else "🟢 ปกติ"
                payment_text = "💰 เงินสด" if sale.payment_method == 'cash' else "💳 โอนเงิน"
                
                with st.expander(f"{void_status} เลขที่: {sale.id:06d} - {format_currency(sale.total_amount)} - {format_date(sale.created_at)}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**วันที่:** {format_date(sale.created_at)}")
                        st.write(f"**ยอดรวม:** {format_currency(sale.total_amount)}")
                        st.write(f"**วิธีชำระ:** {payment_text}")
                        st.write(f"**ผู้ขาย:** {sale.creator.username if sale.creator else '-'}")
                    
                    with col2:
                        if sale.is_void:
                            st.write(f"**สถานะ:** 🔴 ยกเลิกแล้ว")
                            st.write(f"**เหตุผล:** {sale.void_reason or '-'}")
                            voided_user = session.query(User).filter(User.id == sale.voided_by).first() if sale.voided_by else None
                            st.write(f"**ยกเลิกโดย:** {voided_user.username if voided_user else '-'}")
                            st.write(f"**วันที่ยกเลิก:** {format_date(sale.voided_at) if sale.voided_at else '-'}")
                        else:
                            st.write(f"**สถานะ:** 🟢 ปกติ")
                    
                    with col3:
                        if not sale.is_void:
                            if st.button("🔄 ยกเลิกการขาย", key=f"void_{sale.id}", width='stretch'):
                                st.session_state[f"voiding_sale_{sale.id}"] = True
                                st.rerun()
                            
                            # Void confirmation dialog
                            if st.session_state.get(f"voiding_sale_{sale.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะยกเลิกการขายเลขที่ {sale.id:06d}?")
                                st.write("**รายการสินค้า:**")
                                for item in sale.sale_items:
                                    item_name = ""
                                    if item.item_type == 'product' and item.product:
                                        item_name = item.product.name
                                    elif item.item_type == 'menu' and item.menu:
                                        item_name = item.menu.name
                                    st.write(f"- {item_name} x {item.quantity:.2f}")
                                
                                reason = st.text_input("เหตุผลในการยกเลิก *", key=f"void_reason_{sale.id}", placeholder="เช่น ผิดพลาด, ลูกค้าต้องการคืน")
                                
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_void_{sale.id}", width='stretch'):
                                        if reason:
                                            with st.spinner("⏳ กำลังยกเลิกการขาย..."):
                                                success, message = void_sale(sale.id, reason, st.session_state.user_id)
                                                if success:
                                                    st.session_state[f"voiding_sale_{sale.id}"] = False
                                                    st.success(f"✅ {message}")
                                                    print(f"[DEBUG] ยกเลิกการขาย - Sale ID: {sale.id}, Reason: {reason}, User: {st.session_state.user_id} - {datetime.now()}")
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ {message}")
                                        else:
                                            st.warning("⚠️ กรุณากรอกเหตุผล")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_void_{sale.id}", width='stretch'):
                                        st.session_state[f"voiding_sale_{sale.id}"] = False
                                        st.rerun()
                    
                    # Sale items
                    st.divider()
                    st.write("**รายการสินค้า:**")
                    items_data = []
                    for item in sale.sale_items:
                        item_name = ""
                        if item.item_type == 'product' and item.product:
                            item_name = item.product.name
                        elif item.item_type == 'menu' and item.menu:
                            item_name = item.menu.name
                        
                        items_data.append({
                            'รายการ': item_name,
                            'ประเภท': 'สินค้า' if item.item_type == 'product' else 'เมนู',
                            'จำนวน': f"{item.quantity:.2f}",
                            'ราคาต่อหน่วย': format_currency(item.unit_price),
                            'รวม': format_currency(item.total_price)
                        })
                    
                    df_items = pd.DataFrame(items_data)
                    st.dataframe(df_items, width='stretch', hide_index=True)
        else:
            st.info("ไม่พบการขาย")
    finally:
        session.close()

if __name__ == "__main__":
    main()

