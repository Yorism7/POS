"""
Return/Refund Page - คืนสินค้า
"""

import streamlit as st
from datetime import datetime, timedelta
from database.db import get_session
from database.models import Sale, SaleItem, Product, Menu, StockTransaction
from utils.helpers import format_currency, format_date
from utils.pagination import paginate_items
import pandas as pd

st.set_page_config(page_title="คืนสินค้า", page_icon="↩️", layout="wide")

def process_return(sale_id: int, return_items: list, reason: str, user_id: int):
    """Process return/refund"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return False, "ไม่พบการขาย"
        
        if sale.is_void:
            return False, "ไม่สามารถคืนสินค้าจากการขายที่ถูกยกเลิกแล้ว"
        
        total_refund = 0.0
        
        # Process each return item
        for return_item in return_items:
            sale_item_id = return_item['sale_item_id']
            return_quantity = return_item['quantity']
            
            sale_item = session.query(SaleItem).filter(SaleItem.id == sale_item_id).first()
            if not sale_item:
                continue
            
            if return_quantity > sale_item.quantity:
                return False, f"จำนวนที่คืนเกินจำนวนที่ขาย (ขาย {sale_item.quantity:.2f})"
            
            # Calculate refund amount
            refund_per_item = (sale_item.total_price / sale_item.quantity) * return_quantity
            total_refund += refund_per_item
            
            # Restore stock
            if sale_item.item_type == 'product' and sale_item.product_id:
                product = session.query(Product).filter(Product.id == sale_item.product_id).first()
                if product:
                    product.stock_quantity += return_quantity
                    
                    # Create stock transaction
                    transaction = StockTransaction(
                        product_id=product.id,
                        transaction_type='in',
                        quantity=return_quantity,
                        unit_price=product.cost_price,
                        total_cost=product.cost_price * return_quantity,
                        reason=f'คืนสินค้า - Sale #{sale_id}',
                        created_by=user_id
                    )
                    session.add(transaction)
            
            elif sale_item.item_type == 'menu' and sale_item.menu_id:
                menu = session.query(Menu).filter(Menu.id == sale_item.menu_id).first()
                if menu:
                    for menu_item in menu.menu_items:
                        if menu_item.product:
                            product = session.query(Product).filter(
                                Product.id == menu_item.product.id
                            ).first()
                            if product:
                                quantity_needed = menu_item.quantity * return_quantity
                                product.stock_quantity += quantity_needed
                                
                                # Create stock transaction
                                transaction = StockTransaction(
                                    product_id=product.id,
                                    transaction_type='in',
                                    quantity=quantity_needed,
                                    unit_price=product.cost_price,
                                    total_cost=product.cost_price * quantity_needed,
                                    reason=f'คืนเมนู {menu.name} - Sale #{sale_id}',
                                    created_by=user_id
                                )
                                session.add(transaction)
        
        # Update sale total (reduce)
        sale.total_amount -= total_refund
        sale.final_amount -= total_refund
        if sale.final_amount < 0:
            sale.final_amount = 0
        
        session.commit()
        return True, f"คืนสินค้าสำเร็จ จำนวนเงินคืน: {format_currency(total_refund)}"
    except Exception as e:
        session.rollback()
        return False, f"เกิดข้อผิดพลาด: {str(e)}"
    finally:
        session.close()

def main():
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth
    require_auth()
    
    st.title("↩️ คืนสินค้า (Return/Refund)")
    
    # Search sale
    col1, col2 = st.columns([2, 1])
    with col1:
        sale_id_search = st.text_input("🔍 ค้นหาเลขที่การขาย", placeholder="เช่น 000001", key="return_sale_search")
    with col2:
        days = st.number_input("แสดงย้อนหลัง (วัน)", min_value=1, value=7, step=1, key="return_days")
    
    session = get_session()
    try:
        if sale_id_search and sale_id_search.strip():
            try:
                sale_id = int(sale_id_search.strip())
                sale = session.query(Sale).filter(Sale.id == sale_id).first()
                
                if sale:
                    if sale.is_void:
                        st.error("❌ ไม่สามารถคืนสินค้าจากการขายที่ถูกยกเลิกแล้ว")
                    else:
                        st.success(f"✅ พบการขายเลขที่ {sale.id:06d}")
                        
                        # Show sale details
                        st.subheader("📋 รายละเอียดการขาย")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**เลขที่:** {sale.id:06d}")
                            st.write(f"**วันที่:** {format_date(sale.created_at)}")
                            st.write(f"**ยอดรวม:** {format_currency(sale.total_amount)}")
                        with col2:
                            if sale.discount_amount > 0:
                                st.write(f"**ส่วนลด:** {format_currency(sale.discount_amount)}")
                            st.write(f"**ยอดสุดท้าย:** {format_currency(sale.final_amount)}")
                            payment_text = "💰 เงินสด" if sale.payment_method == 'cash' else "💳 โอนเงิน"
                            st.write(f"**วิธีชำระ:** {payment_text}")
                        with col3:
                            st.write(f"**ผู้ขาย:** {sale.creator.username if sale.creator else '-'}")
                        
                        st.divider()
                        
                        # Return form
                        st.subheader("↩️ เลือกรายการที่ต้องการคืน")
                        
                        return_items = []
                        for item in sale.sale_items:
                            item_name = ""
                            if item.item_type == 'product' and item.product:
                                item_name = item.product.name
                            elif item.item_type == 'menu' and item.menu:
                                item_name = item.menu.name
                            
                            col_name, col_qty, col_return = st.columns([3, 1, 1])
                            with col_name:
                                st.write(f"**{item_name}**")
                                st.caption(f"ขาย: {item.quantity:.2f} | ราคา: {format_currency(item.unit_price)} | รวม: {format_currency(item.total_price)}")
                            with col_qty:
                                return_qty = st.number_input(
                                    "จำนวนคืน",
                                    min_value=0.0,
                                    max_value=float(item.quantity),
                                    value=0.0,
                                    step=0.01,
                                    key=f"return_qty_{item.id}",
                                    label_visibility="collapsed"
                                )
                            with col_return:
                                if return_qty > 0:
                                    return_items.append({
                                        'sale_item_id': item.id,
                                        'quantity': return_qty,
                                        'name': item_name
                                    })
                                    refund_amount = (item.total_price / item.quantity) * return_qty
                                    st.write(f"คืน: {format_currency(refund_amount)}")
                            
                            st.divider()
                        
                        if return_items:
                            total_refund = sum(
                                (session.query(SaleItem).filter(SaleItem.id == item['sale_item_id']).first().total_price / 
                                 session.query(SaleItem).filter(SaleItem.id == item['sale_item_id']).first().quantity) * item['quantity']
                                for item in return_items
                            )
                            
                            st.info(f"💰 จำนวนเงินคืนรวม: {format_currency(total_refund)}")
                            
                            reason = st.text_input("เหตุผลในการคืน *", placeholder="เช่น สินค้าชำรุด, ลูกค้าต้องการคืน")
                            
                            if st.button("↩️ คืนสินค้า", type="primary", use_container_width=True):
                                if reason:
                                    with st.spinner("⏳ กำลังประมวลผลการคืนสินค้า..."):
                                        success, message = process_return(sale.id, return_items, reason, st.session_state.user_id)
                                        if success:
                                            st.success(f"✅ {message}")
                                            print(f"[DEBUG] คืนสินค้า - Sale ID: {sale.id}, Items: {len(return_items)}, User: {st.session_state.user_id} - {datetime.now()}")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {message}")
                                else:
                                    st.warning("⚠️ กรุณากรอกเหตุผล")
                else:
                    st.warning("⚠️ ไม่พบการขาย")
            except ValueError:
                st.warning("⚠️ กรุณากรอกเลขที่การขายเป็นตัวเลข")
    finally:
        session.close()

if __name__ == "__main__":
    main()



