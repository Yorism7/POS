"""
Kitchen Queue Management Page - จัดการคิวทำอาหาร
สำหรับพนักงานครัวและผู้จัดการ
"""

import streamlit as st
from datetime import datetime
from database.db import get_session
from database.models import KitchenQueue, CustomerOrder, Menu, Table, User, OrderStatus
from utils.order_utils import update_queue_status, update_order_status
from utils.helpers import format_currency
from sqlalchemy import or_

st.set_page_config(page_title="จัดการคิว", page_icon="👨‍🍳", layout="wide")

def main():
    # ต้องล็อคอิน
    from utils.auth import require_auth
    require_auth()
    
    st.title("👨‍🍳 จัดการคิวทำอาหาร")
    
    session = get_session()
    try:
        # ฟิลเตอร์สถานะ
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            status_filter = st.selectbox(
                "สถานะ",
                ["ทั้งหมด", "pending", "preparing", "ready", "completed"],
                key="queue_status_filter"
            )
        with col2:
            search_term = st.text_input("🔍 ค้นหา (เลขออเดอร์, ชื่อเมนู)", placeholder="ค้นหา...")
        with col3:
            auto_refresh = st.checkbox("🔄 Auto Refresh", value=True, help="รีเฟรชอัตโนมัติทุก 5 วินาที")
        
        # Auto refresh
        if auto_refresh:
            import time
            time.sleep(5)
            st.rerun()
        
        # Query คิว
        query = session.query(KitchenQueue).join(CustomerOrder).join(Menu)
        
        if status_filter != "ทั้งหมด":
            query = query.filter(KitchenQueue.status == status_filter)
        
        if search_term:
            query = query.filter(
                or_(
                    CustomerOrder.order_number.contains(search_term),
                    Menu.name.contains(search_term)
                )
            )
        
        # เรียงตาม priority และ created_at
        queue_items = query.order_by(
            KitchenQueue.priority.desc(),
            KitchenQueue.created_at.asc()
        ).all()
        
        if not queue_items:
            st.info("📭 ไม่มีคิว")
            return
        
        # แสดงคิวตามสถานะ
        status_groups = {
            'pending': [],
            'preparing': [],
            'ready': [],
            'completed': []
        }
        
        for item in queue_items:
            if item.status in status_groups:
                status_groups[item.status].append(item)
        
        # แสดงคิวที่ยังไม่เสร็จ
        tabs = st.tabs(["⏳ รอทำ", "👨‍🍳 กำลังทำ", "✅ พร้อมเสิร์ฟ", "✔️ เสร็จแล้ว"])
        
        with tabs[0]:
            st.subheader("⏳ รอทำ")
            if status_groups['pending']:
                display_queue_items(status_groups['pending'], session, 'pending')
            else:
                st.info("📭 ไม่มีคิวที่รอทำ")
        
        with tabs[1]:
            st.subheader("👨‍🍳 กำลังทำ")
            if status_groups['preparing']:
                display_queue_items(status_groups['preparing'], session, 'preparing')
            else:
                st.info("📭 ไม่มีคิวที่กำลังทำ")
        
        with tabs[2]:
            st.subheader("✅ พร้อมเสิร์ฟ")
            if status_groups['ready']:
                display_queue_items(status_groups['ready'], session, 'ready')
            else:
                st.info("📭 ไม่มีคิวที่พร้อมเสิร์ฟ")
        
        with tabs[3]:
            st.subheader("✔️ เสร็จแล้ว")
            # แสดงแค่ 20 รายการล่าสุด
            completed_items = status_groups['completed'][:20]
            if completed_items:
                display_queue_items(completed_items, session, 'completed')
            else:
                st.info("📭 ไม่มีคิวที่เสร็จแล้ว")
    
    finally:
        session.close()

def display_queue_items(items, session, current_status):
    """แสดงรายการคิว"""
    current_user_id = st.session_state.get('user_id')
    
    for item in items:
        order = session.query(CustomerOrder).filter(CustomerOrder.id == item.order_id).first()
        menu = session.query(Menu).filter(Menu.id == item.menu_id).first()
        table = session.query(Table).filter(Table.id == order.table_id).first() if order and order.table_id else None
        
        if not order or not menu:
            continue
        
        # สร้าง card สำหรับแต่ละคิว
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.write(f"**{menu.name}** x{item.quantity}")
                st.caption(f"📋 {order.order_number} | 🪑 โต๊ะ: {table.table_number if table else 'N/A'}")
                if item.notes:
                    st.caption(f"💬 {item.notes}")
                if item.special_instructions:
                    st.caption(f"📝 {item.special_instructions}")
            
            with col2:
                if current_status == 'pending':
                    st.write("⏳ รอทำ")
                    if st.button("👨‍🍳 เริ่มทำ", key=f"start_{item.id}", width='stretch'):
                        try:
                            update_queue_status(item.id, 'preparing', current_user_id)
                            st.success("✅ เริ่มทำแล้ว")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                
                elif current_status == 'preparing':
                    st.write("👨‍🍳 กำลังทำ")
                    if item.started_at:
                        st.caption(f"เริ่ม: {item.started_at.strftime('%H:%M')}")
                    if st.button("✅ พร้อมเสิร์ฟ", key=f"ready_{item.id}", width='stretch'):
                        try:
                            update_queue_status(item.id, 'ready', current_user_id)
                            st.success("✅ อัพเดทเป็นพร้อมเสิร์ฟแล้ว")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                
                elif current_status == 'ready':
                    st.write("✅ พร้อมเสิร์ฟ")
                    if item.completed_at:
                        st.caption(f"เสร็จ: {item.completed_at.strftime('%H:%M')}")
                    if st.button("✔️ เสร็จสิ้น", key=f"complete_{item.id}", width='stretch'):
                        try:
                            update_queue_status(item.id, 'completed', current_user_id)
                            
                            # ตรวจสอบว่าออเดอร์นี้เสร็จหมดหรือยัง
                            remaining_queue = session.query(KitchenQueue).filter(
                                KitchenQueue.order_id == order.id,
                                KitchenQueue.status != 'completed'
                            ).count()
                            
                            if remaining_queue == 0:
                                # อัพเดทสถานะออเดอร์เป็น ready
                                update_order_status(order.id, 'ready')
                            
                            st.success("✅ เสร็จสิ้น")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                
                elif current_status == 'completed':
                    st.write("✔️ เสร็จแล้ว")
                    if item.completed_at:
                        st.caption(f"เสร็จ: {item.completed_at.strftime('%H:%M')}")
                    if item.prepared_by:
                        preparer = session.query(User).filter(User.id == item.prepared_by).first()
                        if preparer:
                            st.caption(f"โดย: {preparer.username}")
            
            with col3:
                st.caption(f"เวลา: {item.created_at.strftime('%H:%M')}")
                if item.started_at:
                    duration = (datetime.now() - item.started_at).total_seconds() / 60
                    st.caption(f"⏱️ {int(duration)} นาที")
            
            st.divider()

if __name__ == "__main__":
    main()

