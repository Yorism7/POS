"""
Customer Order Page - หน้าสำหรับลูกค้าสั่งอาหารผ่าน QR Code
ไม่ต้องล็อคอิน - เปิดให้ลูกค้าทั่วไปใช้งานได้
"""

import streamlit as st
from datetime import datetime
from database.db import get_session
from database.models import Table, Menu, CustomerOrder, OrderItem
from utils.order_utils import get_table_by_qr, create_order, get_order_by_id
from utils.helpers import format_currency
import json

st.set_page_config(
    page_title="สั่งอาหาร",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    # ไม่ต้องล็อคอิน - เปิดให้ทุกคนใช้งานได้
    st.title("🍽️ สั่งอาหาร")
    
    # ตรวจสอบ table_id จาก URL parameter
    try:
        if hasattr(st, 'query_params'):
            query_params = st.query_params
            table_id_param = query_params.get('table_id', None)
        else:
            query_params = st.experimental_get_query_params()
            table_id_param = query_params.get('table_id', [None])[0] if query_params.get('table_id') else None
    except:
        table_id_param = None
    
    # ตรวจสอบ QR Code จาก URL parameter
    qr_data = None
    try:
        if hasattr(st, 'query_params'):
            qr_data = query_params.get('barcode', None)
        else:
            qr_data = query_params.get('barcode', [None])[0] if query_params.get('barcode') else None
    except:
        pass
    
    session = get_session()
    try:
        # หาโต๊ะ
        table = None
        if table_id_param:
            table = session.query(Table).filter(Table.id == int(table_id_param), Table.is_active == True).first()
        elif qr_data:
            table = get_table_by_qr(qr_data)
        
        if not table:
            st.warning("⚠️ ไม่พบโต๊ะ กรุณาสแกน QR Code ที่โต๊ะอีกครั้ง")
            st.info("💡 **วิธีใช้งาน:** สแกน QR Code ที่โต๊ะเพื่อเริ่มสั่งอาหาร")
            
            # แสดง QR Code scanner
            with st.expander("📷 สแกน QR Code ที่โต๊ะ", expanded=True):
                try:
                    from components.barcode_scanner_realtime import barcode_scanner_realtime
                    scanned_qr = barcode_scanner_realtime()
                    if scanned_qr:
                        st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ ไม่สามารถใช้กล้องได้: {str(e)}")
                    st.info("💡 กรุณาพิมพ์เลขโต๊ะหรือสแกน QR Code อีกครั้ง")
            
            # Manual input สำหรับทดสอบ
            with st.expander("🔧 กรอกเลขโต๊ะ (สำหรับทดสอบ)", expanded=False):
                manual_table_id = st.text_input("เลขโต๊ะ", placeholder="เช่น 1, 2, 3...")
                if st.button("ยืนยัน", key="confirm_table"):
                    if manual_table_id:
                        try:
                            table = session.query(Table).filter(Table.id == int(manual_table_id), Table.is_active == True).first()
                            if table:
                                st.success(f"✅ พบโต๊ะ: {table.table_number}")
                                st.rerun()
                            else:
                                st.error("❌ ไม่พบโต๊ะนี้")
                        except:
                            st.error("❌ กรุณากรอกเลขโต๊ะที่ถูกต้อง")
            
            return
        
        # แสดงข้อมูลโต๊ะ
        st.success(f"✅ โต๊ะ: **{table.table_number}** {f'({table.name})' if table.name else ''}")
        
        # ตรวจสอบว่ามีออเดอร์ที่ยังไม่เสร็จหรือไม่
        active_order = session.query(CustomerOrder).filter(
            CustomerOrder.table_id == table.id,
            CustomerOrder.status.in_(['pending', 'confirmed', 'preparing', 'ready'])
        ).order_by(CustomerOrder.created_at.desc()).first()
        
        if active_order:
            st.info(f"📋 คุณมีออเดอร์ที่ยังไม่เสร็จ: **{active_order.order_number}**")
            if st.button("ดูออเดอร์ปัจจุบัน", key="view_order"):
                st.session_state['view_order_id'] = active_order.id
                st.rerun()
        
        # แท็บสำหรับสั่งอาหารและดูออเดอร์
        tab1, tab2 = st.tabs(["📝 สั่งอาหาร", "📋 ออเดอร์ของฉัน"])
        
        with tab1:
            st.subheader("📝 เลือกเมนู")
            
            # แสดงเมนูทั้งหมด
            menus = session.query(Menu).filter(Menu.is_active == True).order_by(Menu.name).all()
            
            if not menus:
                st.warning("⚠️ ยังไม่มีเมนูที่พร้อมขาย")
                return
            
            # เริ่มต้น cart ใน session state
            if 'order_cart' not in st.session_state:
                st.session_state.order_cart = []
            
            # แสดงเมนูใน grid
            cols = st.columns(3)
            for idx, menu in enumerate(menus):
                with cols[idx % 3]:
                    with st.container():
                        # แสดงรูปภาพเมนู
                        if menu.image_path:
                            try:
                                if menu.image_path.startswith(('http://', 'https://')):
                                    st.image(menu.image_path, caption=menu.name, width='stretch', use_container_width=True)
                                else:
                                    import os
                                    if os.path.exists(menu.image_path):
                                        st.image(menu.image_path, caption=menu.name, width='stretch', use_container_width=True)
                            except:
                                pass
                        
                        st.write(f"**{menu.name}**")
                        if menu.description:
                            st.caption(menu.description)
                        st.write(f"💰 {format_currency(menu.price)}")
                        
                        col_qty, col_add = st.columns([1, 1])
                        with col_qty:
                            qty = st.number_input(
                                "จำนวน",
                                min_value=1,
                                value=1,
                                step=1,
                                key=f"qty_menu_{menu.id}",
                                label_visibility="collapsed"
                            )
                        with col_add:
                            if st.button("➕ เพิ่ม", key=f"add_menu_{menu.id}", width='stretch'):
                                # เพิ่มลงตะกร้า
                                item = {
                                    'menu_id': menu.id,
                                    'menu_name': menu.name,
                                    'quantity': qty,
                                    'unit_price': menu.price,
                                    'subtotal': menu.price * qty,
                                    'special_instructions': ''
                                }
                                st.session_state.order_cart.append(item)
                                st.success(f"✅ เพิ่ม {menu.name} จำนวน {qty} ลงตะกร้า")
                                st.rerun()
                        st.divider()
            
            # แสดงตะกร้า
            st.subheader("🛒 ตะกร้าของฉัน")
            
            if st.session_state.order_cart:
                total = 0.0
                for idx, item in enumerate(st.session_state.order_cart):
                    col_name, col_qty, col_price, col_del = st.columns([3, 1, 1, 1])
                    with col_name:
                        st.write(f"**{item['menu_name']}**")
                    with col_qty:
                        st.write(f"x{item['quantity']}")
                    with col_price:
                        st.write(format_currency(item['subtotal']))
                    with col_del:
                        if st.button("🗑️", key=f"del_{idx}", help="ลบ"):
                            st.session_state.order_cart.pop(idx)
                            st.rerun()
                    total += item['subtotal']
                    st.divider()
                
                st.write(f"**ยอดรวม: {format_currency(total)}**")
                
                # ข้อมูลลูกค้า (optional)
                with st.expander("👤 ข้อมูลลูกค้า (ไม่บังคับ)", expanded=False):
                    customer_name = st.text_input("ชื่อ", placeholder="ชื่อของคุณ")
                    customer_phone = st.text_input("เบอร์โทร", placeholder="เบอร์โทรของคุณ")
                
                # หมายเหตุ
                notes = st.text_area("หมายเหตุ", placeholder="เช่น ไม่เผ็ด, ไม่ใส่ผักชี, ฯลฯ")
                
                # ปุ่มยืนยันออเดอร์
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ ยืนยันออเดอร์", key="confirm_order", width='stretch', type="primary"):
                        try:
                            # สร้างออเดอร์
                            order = create_order(
                                table_id=table.id,
                                items=[{
                                    'menu_id': item['menu_id'],
                                    'quantity': item['quantity'],
                                    'special_instructions': item.get('special_instructions', '')
                                } for item in st.session_state.order_cart],
                                customer_name=customer_name if customer_name else None,
                                customer_phone=customer_phone if customer_phone else None,
                                notes=notes if notes else None
                            )
                            
                            # ล้างตะกร้า
                            st.session_state.order_cart = []
                            
                            st.success(f"✅ สั่งอาหารสำเร็จ! เลขที่ออเดอร์: **{order.order_number}**")
                            st.info("📋 คุณสามารถดูสถานะออเดอร์ได้ในแท็บ 'ออเดอร์ของฉัน'")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                
                with col2:
                    if st.button("🗑️ ล้างตะกร้า", key="clear_cart", width='stretch'):
                        st.session_state.order_cart = []
                        st.rerun()
            else:
                st.info("🛒 ตะกร้าว่างเปล่า กรุณาเลือกเมนู")
        
        with tab2:
            st.subheader("📋 ออเดอร์ของฉัน")
            
            # ดึงออเดอร์ทั้งหมดของโต๊ะนี้
            orders = session.query(CustomerOrder).filter(
                CustomerOrder.table_id == table.id
            ).order_by(CustomerOrder.created_at.desc()).limit(10).all()
            
            if not orders:
                st.info("📭 ยังไม่มีออเดอร์")
                return
            
            for order in orders:
                status_colors = {
                    'pending': '🟡',
                    'confirmed': '🔵',
                    'preparing': '🟠',
                    'ready': '🟢',
                    'served': '✅',
                    'completed': '✅',
                    'cancelled': '❌'
                }
                status_texts = {
                    'pending': 'รอยืนยัน',
                    'confirmed': 'ยืนยันแล้ว',
                    'preparing': 'กำลังทำ',
                    'ready': 'พร้อมเสิร์ฟ',
                    'served': 'เสิร์ฟแล้ว',
                    'completed': 'เสร็จสิ้น',
                    'cancelled': 'ยกเลิก'
                }
                
                status_icon = status_colors.get(order.status, '⚪')
                status_text = status_texts.get(order.status, order.status)
                
                with st.expander(f"{status_icon} {order.order_number} - {status_text} - {format_currency(order.total_amount)}"):
                    st.write(f"**วันที่:** {order.created_at.strftime('%d/%m/%Y %H:%M')}")
                    if order.customer_name:
                        st.write(f"**ชื่อ:** {order.customer_name}")
                    if order.customer_phone:
                        st.write(f"**เบอร์โทร:** {order.customer_phone}")
                    if order.notes:
                        st.write(f"**หมายเหตุ:** {order.notes}")
                    
                    st.divider()
                    st.write("**รายการอาหาร:**")
                    
                    # ดึงรายการอาหาร
                    order_items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                    for item in order_items:
                        menu = session.query(Menu).filter(Menu.id == item.menu_id).first()
                        if menu:
                            st.write(f"- {menu.name} x{item.quantity} = {format_currency(item.subtotal)}")
                            if item.special_instructions:
                                st.caption(f"  💬 {item.special_instructions}")
                    
                    st.write(f"**ยอดรวม: {format_currency(order.total_amount)}**")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()

