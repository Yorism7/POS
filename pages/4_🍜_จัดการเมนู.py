"""
Menu Management Page - จัดการเมนูอาหาร
"""

import streamlit as st
from datetime import datetime
from database.db import get_session
from database.models import Menu, MenuItem, Product
from utils.helpers import format_currency, calculate_menu_cost
from utils.pagination import paginate_items

st.set_page_config(page_title="จัดการเมนู", page_icon="🍜", layout="wide")

def main():
    st.title("🍜 จัดการเมนู")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["📋 รายการเมนู", "➕ เพิ่มเมนู"])
    
    with tab1:
        st.subheader("📋 รายการเมนูทั้งหมด")
        
        session = get_session()
        try:
            # Filter
            col1, col2 = st.columns(2)
            with col1:
                show_active = st.checkbox("แสดงเฉพาะเมนูที่เปิดขาย", value=True)
            with col2:
                search_term = st.text_input("🔍 ค้นหาเมนู", placeholder="ชื่อเมนู...")
            
            # Query menus
            query = session.query(Menu)
            
            if show_active:
                query = query.filter(Menu.is_active == True)
            
            if search_term:
                query = query.filter(Menu.name.contains(search_term))
            
            all_menus = query.order_by(Menu.name).all()
            
            # Pagination
            if 'menu_page' not in st.session_state:
                st.session_state.menu_page = 1
            
            items_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 50], index=0, key="menu_items_per_page")
            
            paginated_menus, total_items, total_pages, current_page = paginate_items(
                all_menus,
                st.session_state.menu_page,
                items_per_page
            )
            
            st.info(f"📊 แสดง {len(paginated_menus)} จาก {total_items} รายการ (หน้า {current_page}/{total_pages})")
            
            # Pagination controls
            if total_pages > 1:
                col_prev, col_page, col_next = st.columns([1, 3, 1])
                with col_prev:
                    if st.button("◀️ ก่อนหน้า", disabled=(current_page == 1), use_container_width=True, key="menu_prev"):
                        st.session_state.menu_page = max(1, current_page - 1)
                        st.rerun()
                with col_page:
                    st.write(f"หน้า {current_page} / {total_pages}")
                with col_next:
                    if st.button("ถัดไป ▶️", disabled=(current_page == total_pages), use_container_width=True, key="menu_next"):
                        st.session_state.menu_page = min(total_pages, current_page + 1)
                        st.rerun()
            
            if paginated_menus:
                for menu in paginated_menus:
                    # Calculate menu cost
                    menu_cost = calculate_menu_cost(menu.id)
                    profit = menu.price - menu_cost
                    profit_margin = (profit / menu.price * 100) if menu.price > 0 else 0
                    
                    status_icon = "🟢" if menu.is_active else "🔴"
                    with st.expander(f"{status_icon} {menu.name} - {format_currency(menu.price)}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**คำอธิบาย:** {menu.description or '-'}")
                            st.write(f"**ราคาขาย:** {format_currency(menu.price)}")
                            st.write(f"**สถานะ:** {'เปิดขาย' if menu.is_active else 'ปิดขาย'}")
                        
                        with col2:
                            st.write(f"**ต้นทุน:** {format_currency(menu_cost)}")
                            st.write(f"**กำไร:** {format_currency(profit)}")
                            st.write(f"**อัตรากำไร:** {profit_margin:.2f}%")
                        
                        with col3:
                            if st.button("✏️ แก้ไข", key=f"edit_{menu.id}", use_container_width=True):
                                st.session_state[f"editing_menu_{menu.id}"] = True
                                st.rerun()
                            
                            if st.button("🗑️ ลบ", key=f"delete_{menu.id}", use_container_width=True):
                                st.session_state[f"confirm_delete_menu_{menu.id}"] = True
                                st.rerun()
                            
                            # Confirmation dialog
                            if st.session_state.get(f"confirm_delete_menu_{menu.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบเมนู {menu.name}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_menu_{menu.id}", use_container_width=True):
                                        try:
                                            session.delete(menu)
                                            session.commit()
                                            st.session_state[f"confirm_delete_menu_{menu.id}"] = False
                                            st.success(f"✅ ลบเมนู {menu.name} สำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_menu_{menu.id}", use_container_width=True):
                                        st.session_state[f"confirm_delete_menu_{menu.id}"] = False
                                        st.rerun()
                        
                        # Menu items (BOM)
                        st.divider()
                        st.write("**วัตถุดิบ (BOM):**")
                        menu_items = session.query(MenuItem).filter(MenuItem.menu_id == menu.id).all()
                        
                        if menu_items:
                            bom_data = []
                            for item in menu_items:
                                bom_data.append({
                                    'วัตถุดิบ': item.product.name if item.product else '-',
                                    'จำนวน': f"{item.quantity:.2f} {item.product.unit if item.product else ''}",
                                    'ราคาต้นทุน': format_currency(item.product.cost_price if item.product else 0),
                                    'รวม': format_currency((item.product.cost_price * item.quantity) if item.product else 0)
                                })
                            
                            import pandas as pd
                            df_bom = pd.DataFrame(bom_data)
                            st.dataframe(df_bom, use_container_width=True, hide_index=True)
                        else:
                            st.info("ยังไม่มีวัตถุดิบ")
                        
                        # Edit form
                        if st.session_state.get(f"editing_menu_{menu.id}", False):
                            st.divider()
                            with st.form(f"edit_menu_form_{menu.id}"):
                                new_name = st.text_input("ชื่อเมนู", value=menu.name, key=f"menu_name_{menu.id}")
                                new_description = st.text_area("คำอธิบาย", value=menu.description or "", key=f"menu_desc_{menu.id}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_price = st.number_input("ราคาขาย", min_value=0.0, value=float(menu.price), key=f"menu_price_{menu.id}")
                                with col2:
                                    new_active = st.checkbox("เปิดขาย", value=menu.is_active, key=f"menu_active_{menu.id}")
                                
                                # Edit BOM
                                st.write("**แก้ไขวัตถุดิบ:**")
                                products = session.query(Product).order_by(Product.name).all()
                                
                                # Show current items
                                current_items = session.query(MenuItem).filter(MenuItem.menu_id == menu.id).all()
                                for idx, item in enumerate(current_items):
                                    col_prod, col_qty, col_del = st.columns([3, 1, 1])
                                    with col_prod:
                                        st.write(item.product.name if item.product else '-')
                                    with col_qty:
                                        new_qty = st.number_input(
                                            "จำนวน",
                                            min_value=0.01,
                                            value=float(item.quantity),
                                            step=0.01,
                                            key=f"bom_qty_{menu.id}_{item.id}"
                                        )
                                        item.quantity = new_qty
                                    with col_del:
                                        if st.button("🗑️", key=f"del_bom_{menu.id}_{item.id}"):
                                            session.delete(item)
                                            session.commit()
                                            st.rerun()
                                
                                # Add new item
                                col_add_prod, col_add_qty, col_add_btn = st.columns([3, 1, 1])
                                with col_add_prod:
                                    new_product_id = st.selectbox(
                                        "เพิ่มวัตถุดิบ",
                                        options=[None] + [p.id for p in products],
                                        format_func=lambda x: session.query(Product).filter(Product.id == x).first().name if x else "เลือกวัตถุดิบ",
                                        key=f"new_product_{menu.id}"
                                    )
                                with col_add_qty:
                                    new_item_qty = st.number_input(
                                        "จำนวน",
                                        min_value=0.01,
                                        value=1.0,
                                        step=0.01,
                                        key=f"new_qty_{menu.id}",
                                        label_visibility="collapsed"
                                    )
                                with col_add_btn:
                                    if st.form_submit_button("➕ เพิ่ม", key=f"add_bom_{menu.id}"):
                                        if new_product_id:
                                            # Check if already exists
                                            existing = session.query(MenuItem).filter(
                                                MenuItem.menu_id == menu.id,
                                                MenuItem.product_id == new_product_id
                                            ).first()
                                            
                                            if existing:
                                                existing.quantity += new_item_qty
                                            else:
                                                new_item = MenuItem(
                                                    menu_id=menu.id,
                                                    product_id=new_product_id,
                                                    quantity=new_item_qty
                                                )
                                                session.add(new_item)
                                            session.commit()
                                            st.rerun()
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 บันทึก", use_container_width=True):
                                        try:
                                            menu.name = new_name
                                            menu.description = new_description
                                            menu.price = new_price
                                            menu.is_active = new_active
                                            menu.updated_at = datetime.now()
                                            
                                            # Update BOM quantities
                                            for item in current_items:
                                                item.quantity = st.session_state.get(f"bom_qty_{menu.id}_{item.id}", item.quantity)
                                            
                                            session.commit()
                                            st.session_state[f"editing_menu_{menu.id}"] = False
                                            st.success("✅ บันทึกสำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                        st.session_state[f"editing_menu_{menu.id}"] = False
                                        st.rerun()
            else:
                st.info("ไม่พบเมนู")
        finally:
            session.close()
    
    with tab2:
        st.subheader("➕ เพิ่มเมนูใหม่")
        
        session = get_session()
        try:
            with st.form("add_menu_form"):
                name = st.text_input("ชื่อเมนู *", placeholder="เช่น ก๋วยเตี๋ยวน้ำใส")
                description = st.text_area("คำอธิบาย", placeholder="คำอธิบายเมนู...")
                
                col1, col2 = st.columns(2)
                with col1:
                    price = st.number_input("ราคาขาย *", min_value=0.0, value=0.0)
                with col2:
                    is_active = st.checkbox("เปิดขาย", value=True)
                
                st.divider()
                st.write("**วัตถุดิบ (BOM):**")
                
                products = session.query(Product).order_by(Product.name).all()
                bom_items = []
                
                # BOM builder
                if 'bom_items' not in st.session_state:
                    st.session_state.bom_items = []
                
                # Display current BOM items
                for idx, bom_item in enumerate(st.session_state.bom_items):
                    col_prod, col_qty, col_del = st.columns([3, 1, 1])
                    with col_prod:
                        product = session.query(Product).filter(Product.id == bom_item['product_id']).first()
                        st.write(product.name if product else '-')
                    with col_qty:
                        st.write(f"{bom_item['quantity']:.2f} {product.unit if product else ''}")
                    with col_del:
                        if st.button("🗑️", key=f"del_bom_new_{idx}"):
                            st.session_state.bom_items.pop(idx)
                            st.rerun()
                
                # Add new BOM item
                col_add_prod, col_add_qty, col_add_btn = st.columns([3, 1, 1])
                with col_add_prod:
                    new_product_id = st.selectbox(
                        "เลือกวัตถุดิบ",
                        options=[None] + [p.id for p in products],
                        format_func=lambda x: session.query(Product).filter(Product.id == x).first().name if x else "เลือกวัตถุดิบ",
                        key="new_bom_product"
                    )
                with col_add_qty:
                    new_bom_qty = st.number_input(
                        "จำนวน",
                        min_value=0.01,
                        value=1.0,
                        step=0.01,
                        key="new_bom_qty",
                        label_visibility="collapsed"
                    )
                with col_add_btn:
                    if st.form_submit_button("➕ เพิ่ม", key="add_bom_new"):
                        if new_product_id:
                            # Check if already in list
                            existing_idx = None
                            for idx, item in enumerate(st.session_state.bom_items):
                                if item['product_id'] == new_product_id:
                                    existing_idx = idx
                                    break
                            
                            if existing_idx is not None:
                                st.session_state.bom_items[existing_idx]['quantity'] += new_bom_qty
                            else:
                                st.session_state.bom_items.append({
                                    'product_id': new_product_id,
                                    'quantity': new_bom_qty
                                })
                            st.rerun()
                
                # Calculate estimated cost
                if st.session_state.bom_items:
                    estimated_cost = 0.0
                    for bom_item in st.session_state.bom_items:
                        product = session.query(Product).filter(Product.id == bom_item['product_id']).first()
                        if product:
                            estimated_cost += product.cost_price * bom_item['quantity']
                    
                    st.info(f"💰 ต้นทุนประมาณ: {format_currency(estimated_cost)}")
                    if price > 0:
                        estimated_profit = price - estimated_cost
                        profit_margin = (estimated_profit / price * 100) if price > 0 else 0
                        st.info(f"💵 กำไรประมาณ: {format_currency(estimated_profit)} ({profit_margin:.2f}%)")
                
                if st.form_submit_button("➕ เพิ่มเมนู", type="primary", use_container_width=True):
                    if name and price >= 0:
                        if not st.session_state.bom_items:
                            st.warning("⚠️ กรุณาเพิ่มวัตถุดิบอย่างน้อย 1 รายการ")
                        else:
                            try:
                                # Create menu
                                menu = Menu(
                                    name=name,
                                    description=description,
                                    price=price,
                                    is_active=is_active
                                )
                                session.add(menu)
                                session.flush()  # Get menu.id
                                
                                # Create menu items
                                for bom_item in st.session_state.bom_items:
                                    menu_item = MenuItem(
                                        menu_id=menu.id,
                                        product_id=bom_item['product_id'],
                                        quantity=bom_item['quantity']
                                    )
                                    session.add(menu_item)
                                
                                session.commit()
                                print(f"[DEBUG] เพิ่มเมนูสำเร็จ - Menu: {name}, Price: {price}, BOM Items: {len(st.session_state.bom_items)} - {datetime.now()}")
                                st.success(f"✅ เพิ่มเมนู {name} สำเร็จ")
                                st.session_state.bom_items = []
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                    else:
                        st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
        finally:
            session.close()

if __name__ == "__main__":
    main()

