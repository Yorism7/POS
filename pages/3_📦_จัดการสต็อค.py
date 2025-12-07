"""
Inventory Management Page - จัดการสต็อค
"""

import streamlit as st
import os
from datetime import datetime
from database.db import get_session
from database.models import Product, Category, StockTransaction
from utils.helpers import format_currency, format_date
from utils.pagination import paginate_items
from utils.image_upload import image_uploader_widget, delete_image
import pandas as pd

st.set_page_config(page_title="จัดการสต็อค", page_icon="📦", layout="wide")

def main():
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth
    require_auth()
    
    st.title("📦 จัดการสต็อค")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 รายการสินค้า", "➕ เพิ่มสินค้า", "📥 สต็อคเข้า", "📤 สต็อคออก"])
    
    with tab1:
        st.subheader("📋 รายการสินค้าทั้งหมด")
        
        session = get_session()
        try:
            # Search and filter
            col_search, col_barcode, col_category = st.columns([2, 1.5, 1])
            with col_search:
                search_term = st.text_input("🔍 ค้นหาสินค้า", placeholder="ชื่อสินค้า...")
            with col_barcode:
                barcode_search = st.text_input("📷 ค้นหาด้วยบาร์โค๊ด", placeholder="สแกนหรือพิมพ์บาร์โค๊ด...", help="ใช้เครื่องยิงบาร์โค๊ดหรือกล้องมือถือสแกนได้")
            with col_category:
                categories = session.query(Category).all()
                category_options = ["ทั้งหมด"] + [cat.name for cat in categories]
                selected_category = st.selectbox("หมวดหมู่", category_options)
            
            # Query products
            query = session.query(Product)
            
            if barcode_search and barcode_search.strip():
                query = query.filter(Product.barcode == barcode_search.strip())
            elif search_term:
                query = query.filter(Product.name.contains(search_term))
            
            if selected_category != "ทั้งหมด":
                category = session.query(Category).filter(Category.name == selected_category).first()
                if category:
                    query = query.filter(Product.category_id == category.id)
            
            all_products = query.order_by(Product.name).all()
            
            # Pagination
            if 'product_page' not in st.session_state:
                st.session_state.product_page = 1
            
            items_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 50, 100], index=0, key="product_items_per_page")
            
            paginated_products, total_items, total_pages, current_page = paginate_items(
                all_products, 
                st.session_state.product_page, 
                items_per_page
            )
            
            st.info(f"📊 แสดง {len(paginated_products)} จาก {total_items} รายการ (หน้า {current_page}/{total_pages})")
            
            # Pagination controls
            if total_pages > 1:
                col_prev, col_page, col_next = st.columns([1, 3, 1])
                with col_prev:
                    if st.button("◀️ ก่อนหน้า", disabled=(current_page == 1), width='stretch'):
                        st.session_state.product_page = max(1, current_page - 1)
                        st.rerun()
                with col_page:
                    st.write(f"หน้า {current_page} / {total_pages}")
                with col_next:
                    if st.button("ถัดไป ▶️", disabled=(current_page == total_pages), width='stretch'):
                        st.session_state.product_page = min(total_pages, current_page + 1)
                        st.rerun()
            
            if paginated_products:
                # Display products
                for product in paginated_products:
                    with st.expander(f"📦 {product.name} - สต็อค: {product.stock_quantity:.2f} {product.unit}"):
                        # Display product image if available
                        if product.image_path:
                            try:
                                # Check if it's a URL or file path
                                if product.image_path.startswith(('http://', 'https://')):
                                    st.image(product.image_path, caption=product.name, width=200, use_container_width=False)
                                else:
                                    # Try to load as file path
                                    if os.path.exists(product.image_path):
                                        st.image(product.image_path, caption=product.name, width=200, use_container_width=False)
                            except Exception as e:
                                st.caption("🖼️ ไม่สามารถแสดงรูปภาพได้")
                                print(f"[DEBUG] Error loading product image: {e}")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**หมวดหมู่:** {product.category.name if product.category else '-'}")
                            st.write(f"**หน่วย:** {product.unit}")
                            st.write(f"**บาร์โค๊ด:** {product.barcode or 'ไม่มี'}")
                            st.write(f"**ราคาต้นทุน:** {format_currency(product.cost_price)}")
                            st.write(f"**ราคาขาย:** {format_currency(product.selling_price)}")
                        
                        with col2:
                            stock_status = "🟢 ปกติ" if product.stock_quantity > product.min_stock else "🔴 ใกล้หมด"
                            st.write(f"**สถานะสต็อค:** {stock_status}")
                            st.write(f"**สต็อคคงเหลือ:** {product.stock_quantity:.2f} {product.unit}")
                            st.write(f"**ขั้นต่ำ:** {product.min_stock:.2f} {product.unit}")
                        
                        with col3:
                            if st.button("✏️ แก้ไข", key=f"edit_{product.id}", width='stretch'):
                                st.session_state[f"editing_product_{product.id}"] = True
                                st.rerun()
                            
                            if st.button("🗑️ ลบ", key=f"delete_{product.id}", width='stretch'):
                                st.session_state[f"confirm_delete_{product.id}"] = True
                                st.rerun()
                            
                            # Confirmation dialog
                            if st.session_state.get(f"confirm_delete_{product.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบ {product.name}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_{product.id}", width='stretch'):
                                        try:
                                            session.delete(product)
                                            session.commit()
                                            st.session_state[f"confirm_delete_{product.id}"] = False
                                            st.success(f"✅ ลบ {product.name} สำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_{product.id}", width='stretch'):
                                        st.session_state[f"confirm_delete_{product.id}"] = False
                                        st.rerun()
                        
                        # Edit form
                        if st.session_state.get(f"editing_product_{product.id}", False):
                            st.divider()
                            with st.form(f"edit_form_{product.id}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    new_name = st.text_input("ชื่อสินค้า", value=product.name, key=f"name_{product.id}")
                                    new_category_id = st.selectbox(
                                        "หมวดหมู่",
                                        options=[None] + [cat.id for cat in categories],
                                        format_func=lambda x: session.query(Category).filter(Category.id == x).first().name if x else "ไม่มี",
                                        index=0 if not product.category_id else [cat.id for cat in categories].index(product.category_id) + 1,
                                        key=f"cat_{product.id}"
                                    )
                                    new_unit = st.text_input("หน่วย", value=product.unit, key=f"unit_{product.id}")
                                    new_barcode = st.text_input("บาร์โค๊ด", value=product.barcode or "", key=f"barcode_{product.id}", placeholder="สแกนหรือพิมพ์บาร์โค๊ด", help="ใช้เครื่องยิงบาร์โค๊ดหรือกล้องมือถือสแกนได้")
                                
                                # ภาพบาร์โค๊ด
                                st.divider()
                                st.write("**📷 ภาพบาร์โค๊ด**")
                                
                                # แสดงภาพบาร์โค๊ดปัจจุบัน
                                if product.barcode_image_path:
                                    col_barcode_curr, col_barcode_new = st.columns([1, 1])
                                    with col_barcode_curr:
                                        st.write("**ภาพบาร์โค๊ดปัจจุบัน:**")
                                        try:
                                            if product.barcode_image_path.startswith(('http://', 'https://')):
                                                st.image(product.barcode_image_path, width=200)
                                            elif os.path.exists(product.barcode_image_path):
                                                st.image(product.barcode_image_path, width=200)
                                        except:
                                            st.caption("ไม่สามารถแสดงภาพได้")
                                
                                uploaded_barcode_image_path = image_uploader_widget(
                                    "อัพโหลดภาพบาร์โค๊ด",
                                    key=f"barcode_image_upload_{product.id}",
                                    image_type="barcode",
                                    help_text="รองรับไฟล์: JPG, PNG, WebP (ขนาดแนะนำ: ไม่เกิน 1200x400px)"
                                )
                                
                                barcode_image_url = st.text_input(
                                    "หรือใส่ URL ภาพบาร์โค๊ด",
                                    value=product.barcode_image_path if product.barcode_image_path and product.barcode_image_path.startswith(('http://', 'https://')) else "",
                                    placeholder="https://example.com/barcode.jpg",
                                    key=f"barcode_image_url_{product.id}"
                                )
                                
                                # กำหนด barcode_image_path
                                new_barcode_image_path = product.barcode_image_path  # ค่าเดิม
                                if uploaded_barcode_image_path:
                                    # ลบภาพเก่าถ้ามี (ถ้าเป็นไฟล์ในเครื่อง)
                                    if product.barcode_image_path and not product.barcode_image_path.startswith(('http://', 'https://')):
                                        delete_image(product.barcode_image_path)
                                    new_barcode_image_path = uploaded_barcode_image_path
                                elif barcode_image_url and barcode_image_url.strip():
                                    # ลบภาพเก่าถ้ามี (ถ้าเป็นไฟล์ในเครื่อง)
                                    if product.barcode_image_path and not product.barcode_image_path.startswith(('http://', 'https://')):
                                        delete_image(product.barcode_image_path)
                                    new_barcode_image_path = barcode_image_url.strip()
                                
                                with col2:
                                    new_cost = st.number_input("ราคาต้นทุน", min_value=0.0, value=float(product.cost_price), key=f"cost_{product.id}")
                                    new_selling = st.number_input("ราคาขาย", min_value=0.0, value=float(product.selling_price), key=f"selling_{product.id}")
                                    new_stock = st.number_input("สต็อค", min_value=0.0, value=float(product.stock_quantity), key=f"stock_{product.id}")
                                    new_min_stock = st.number_input("ขั้นต่ำ", min_value=0.0, value=float(product.min_stock), key=f"min_{product.id}")
                                
                                # รูปภาพสินค้า
                                st.divider()
                                st.write("**🖼️ รูปภาพสินค้า**")
                                
                                # แสดงรูปภาพปัจจุบัน
                                if product.image_path:
                                    col_img_curr, col_img_new = st.columns([1, 1])
                                    with col_img_curr:
                                        st.write("**รูปภาพปัจจุบัน:**")
                                        try:
                                            if product.image_path.startswith(('http://', 'https://')):
                                                st.image(product.image_path, width=150)
                                            elif os.path.exists(product.image_path):
                                                st.image(product.image_path, width=150)
                                        except:
                                            st.caption("ไม่สามารถแสดงรูปภาพได้")
                                
                                col_img1, col_img2 = st.columns([2, 1])
                                with col_img1:
                                    uploaded_image_path = image_uploader_widget(
                                        "อัพโหลดรูปภาพใหม่",
                                        key=f"product_image_upload_{product.id}",
                                        image_type="product",
                                        help_text="รองรับไฟล์: JPG, PNG, WebP"
                                    )
                                with col_img2:
                                    image_url = st.text_input(
                                        "หรือใส่ URL รูปภาพ",
                                        value=product.image_path if product.image_path and product.image_path.startswith(('http://', 'https://')) else "",
                                        placeholder="https://example.com/image.jpg",
                                        key=f"product_image_url_{product.id}"
                                    )
                                
                                # กำหนด image_path
                                new_image_path = product.image_path  # ค่าเดิม
                                if uploaded_image_path:
                                    # ลบรูปภาพเก่าถ้ามี (ถ้าเป็นไฟล์ในเครื่อง)
                                    if product.image_path and not product.image_path.startswith(('http://', 'https://')):
                                        from utils.image_upload import delete_image
                                        delete_image(product.image_path)
                                    new_image_path = uploaded_image_path
                                elif image_url and image_url.strip():
                                    # ลบรูปภาพเก่าถ้ามี (ถ้าเป็นไฟล์ในเครื่อง)
                                    if product.image_path and not product.image_path.startswith(('http://', 'https://')):
                                        delete_image(product.image_path)
                                    new_image_path = image_url.strip()
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 บันทึก", width='stretch'):
                                        try:
                                            # Check barcode uniqueness if changed
                                            if new_barcode and new_barcode.strip() and new_barcode.strip() != (product.barcode or ""):
                                                existing = session.query(Product).filter(
                                                    Product.barcode == new_barcode.strip(),
                                                    Product.id != product.id
                                                ).first()
                                                if existing:
                                                    st.error(f"❌ บาร์โค๊ด {new_barcode.strip()} มีอยู่แล้วในสินค้า: {existing.name}")
                                                else:
                                                    product.barcode = new_barcode.strip() if new_barcode.strip() else None
                                            elif not new_barcode or not new_barcode.strip():
                                                product.barcode = None
                                            
                                            product.name = new_name
                                            product.category_id = new_category_id
                                            product.unit = new_unit
                                            product.cost_price = new_cost
                                            product.selling_price = new_selling
                                            product.stock_quantity = new_stock
                                            product.min_stock = new_min_stock
                                            product.barcode_image_path = new_barcode_image_path
                                            product.updated_at = datetime.now()
                                            session.commit()
                                            st.session_state[f"editing_product_{product.id}"] = False
                                            st.success("✅ บันทึกสำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", width='stretch'):
                                        st.session_state[f"editing_product_{product.id}"] = False
                                        st.rerun()
            else:
                st.info("ไม่พบสินค้า")
        finally:
            session.close()
    
    with tab2:
        st.subheader("➕ เพิ่มสินค้าใหม่")
        
        session = get_session()
        try:
            categories = session.query(Category).all()
            
            # Initialize barcode in session state
            if 'add_product_barcode' not in st.session_state:
                st.session_state.add_product_barcode = ""
            
            # Barcode Scanner Section
            st.markdown("#### 📷 สแกนบาร์โค๊ด")
            with st.expander("📷 ใช้กล้องสแกนบาร์โค๊ด", expanded=False):
                try:
                    from components.barcode_scanner_realtime import barcode_scanner_realtime
                    scanned_barcode = barcode_scanner_realtime()
                    
                    if scanned_barcode:
                        st.session_state.add_product_barcode = scanned_barcode
                        st.success(f"✅ สแกนบาร์โค๊ดได้: {scanned_barcode}")
                        st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ ไม่สามารถใช้กล้องได้: {str(e)}")
                    st.info("💡 กรุณาใช้เครื่องยิงบาร์โค๊ดหรือพิมพ์บาร์โค๊ดในช่องด้านล่าง")
            
            with st.form("add_product_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("ชื่อสินค้า *", placeholder="ชื่อสินค้า")
                    category_id = st.selectbox(
                        "หมวดหมู่",
                        options=[None] + [cat.id for cat in categories],
                        format_func=lambda x: session.query(Category).filter(Category.id == x).first().name if x else "ไม่มี",
                        index=0
                    )
                    unit = st.text_input("หน่วย *", value="ชิ้น", placeholder="เช่น ชิ้น, กิโลกรัม, ลิตร")
                    
                    # Barcode input with scanner support
                    barcode = st.text_input(
                        "บาร์โค๊ด", 
                        value=st.session_state.add_product_barcode,
                        placeholder="สแกนหรือพิมพ์บาร์โค๊ด", 
                        help="ใช้เครื่องยิงบาร์โค๊ด, กล้องมือถือ, หรือพิมพ์บาร์โค๊ดได้",
                        key="barcode_input_add_product"
                    )
                    # Update session state when user types
                    if barcode != st.session_state.add_product_barcode:
                        st.session_state.add_product_barcode = barcode
                    
                    # ภาพบาร์โค๊ด
                    st.divider()
                    st.write("**📷 ภาพบาร์โค๊ด**")
                    col_barcode_img1, col_barcode_img2 = st.columns([2, 1])
                    with col_barcode_img1:
                        uploaded_barcode_image_path = image_uploader_widget(
                            "อัพโหลดภาพบาร์โค๊ด",
                            key="barcode_image_upload",
                            image_type="barcode",
                            help_text="รองรับไฟล์: JPG, PNG, WebP (ขนาดแนะนำ: ไม่เกิน 1200x400px)"
                        )
                    with col_barcode_img2:
                        barcode_image_url = st.text_input(
                            "หรือใส่ URL ภาพบาร์โค๊ด",
                            placeholder="https://example.com/barcode.jpg",
                            key="barcode_image_url"
                        )
                        if barcode_image_url:
                            st.caption("💡 ใช้ URL แทนการอัพโหลด")
                    
                    # กำหนด barcode_image_path
                    barcode_image_path = None
                    if uploaded_barcode_image_path:
                        barcode_image_path = uploaded_barcode_image_path
                    elif barcode_image_url and barcode_image_url.strip():
                        barcode_image_path = barcode_image_url.strip()
                    
                    cost_price = st.number_input("ราคาต้นทุน *", min_value=0.0, value=0.0)
                
                with col2:
                    selling_price = st.number_input("ราคาขาย *", min_value=0.0, value=0.0)
                    stock_quantity = st.number_input("จำนวนสต็อค *", min_value=0.0, value=0.0)
                    min_stock = st.number_input("จำนวนขั้นต่ำ *", min_value=0.0, value=0.0)
                
                # รูปภาพสินค้า
                st.divider()
                st.write("**🖼️ รูปภาพสินค้า**")
                col_img1, col_img2 = st.columns([2, 1])
                with col_img1:
                    uploaded_image_path = image_uploader_widget(
                        "อัพโหลดรูปภาพสินค้า",
                        key="product_image_upload",
                        image_type="product",
                        help_text="รองรับไฟล์: JPG, PNG, WebP (ขนาดแนะนำ: ไม่เกิน 800x800px)"
                    )
                with col_img2:
                    image_url = st.text_input(
                        "หรือใส่ URL รูปภาพ",
                        placeholder="https://example.com/image.jpg",
                        key="product_image_url"
                    )
                    if image_url:
                        st.caption("💡 ใช้ URL แทนการอัพโหลด")
                
                # กำหนด image_path
                image_path = None
                if uploaded_image_path:
                    image_path = uploaded_image_path
                elif image_url and image_url.strip():
                    image_path = image_url.strip()
                
                if st.form_submit_button("➕ เพิ่มสินค้า", type="primary", width='stretch'):
                    if name and unit:
                        with st.spinner("⏳ กำลังเพิ่มสินค้า..."):
                            try:
                                # Check if barcode already exists
                                if barcode and barcode.strip():
                                    existing = session.query(Product).filter(Product.barcode == barcode.strip()).first()
                                    if existing:
                                        st.error(f"❌ บาร์โค๊ด {barcode.strip()} มีอยู่แล้วในสินค้า: {existing.name}")
                                    else:
                                        product = Product(
                                            name=name,
                                            category_id=category_id,
                                            unit=unit,
                                            barcode=barcode.strip(),
                                            cost_price=cost_price,
                                            selling_price=selling_price,
                                            stock_quantity=stock_quantity,
                                            min_stock=min_stock,
                                            image_path=image_path,
                                            barcode_image_path=barcode_image_path
                                        )
                                        session.add(product)
                                        session.commit()
                                        print(f"[DEBUG] เพิ่มสินค้าพร้อมบาร์โค๊ด - Product: {name}, Barcode: {barcode.strip()} - {datetime.now()}")
                                        st.success(f"✅ เพิ่มสินค้า {name} สำเร็จ")
                                        # Clear barcode from session state
                                        st.session_state.add_product_barcode = ""
                                        st.rerun()
                                else:
                                    product = Product(
                                        name=name,
                                        category_id=category_id,
                                        unit=unit,
                                        barcode=None,
                                        cost_price=cost_price,
                                        selling_price=selling_price,
                                        stock_quantity=stock_quantity,
                                        min_stock=min_stock,
                                        image_path=image_path,
                                        barcode_image_path=barcode_image_path
                                    )
                                    session.add(product)
                                    session.commit()
                                    st.success(f"✅ เพิ่มสินค้า {name} สำเร็จ")
                                    # Clear barcode from session state
                                    st.session_state.add_product_barcode = ""
                                    st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                    else:
                        st.warning("⚠️ กรุณากรอกข้อมูลที่จำเป็น")
        finally:
            session.close()
    
    with tab3:
        st.subheader("📥 บันทึกสต็อคเข้า")
        
        session = get_session()
        try:
            products = session.query(Product).order_by(Product.name).all()
            
            with st.form("stock_in_form"):
                product_id = st.selectbox(
                    "เลือกสินค้า *",
                    options=[p.id for p in products],
                    format_func=lambda x: session.query(Product).filter(Product.id == x).first().name
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    quantity = st.number_input("จำนวน *", min_value=0.01, value=1.0, step=0.01)
                    unit_price = st.number_input("ราคาต่อหน่วย *", min_value=0.0, value=0.0)
                
                with col2:
                    total_cost = quantity * unit_price
                    st.metric("รวมต้นทุน", format_currency(total_cost))
                    reason = st.text_input("เหตุผล", placeholder="เช่น ซื้อเข้า, รับของ")
                
                if st.form_submit_button("📥 บันทึกสต็อคเข้า", type="primary", width='stretch'):
                    with st.spinner("⏳ กำลังบันทึกสต็อคเข้า..."):
                        try:
                            product = session.query(Product).filter(Product.id == product_id).first()
                            if product:
                                # Create transaction
                                transaction = StockTransaction(
                                    product_id=product_id,
                                    transaction_type='in',
                                    quantity=quantity,
                                    unit_price=unit_price,
                                    total_cost=total_cost,
                                    reason=reason or 'สต็อคเข้า',
                                    created_by=st.session_state.user_id
                                )
                                session.add(transaction)
                                
                                # Update product stock
                                product.stock_quantity += quantity
                                # Update cost price if needed
                                if unit_price > 0:
                                    # Weighted average cost
                                    old_total = product.stock_quantity * product.cost_price
                                    new_total = old_total + total_cost
                                    new_stock = product.stock_quantity
                                    if new_stock > 0:
                                        product.cost_price = new_total / new_stock
                                
                                session.commit()
                                print(f"[DEBUG] บันทึกสต็อคเข้า - Product: {product.name}, Qty: {quantity}, User: {st.session_state.user_id} - {datetime.now()}")
                                st.success("✅ บันทึกสต็อคเข้าสำเร็จ")
                                st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        finally:
            session.close()
    
    with tab4:
        st.subheader("📤 บันทึกสต็อคออก")
        
        session = get_session()
        try:
            products = session.query(Product).order_by(Product.name).all()
            
            with st.form("stock_out_form"):
                product_id = st.selectbox(
                    "เลือกสินค้า *",
                    options=[p.id for p in products],
                    format_func=lambda x: session.query(Product).filter(Product.id == x).first().name
                )
                
                product = session.query(Product).filter(Product.id == product_id).first()
                if product:
                    st.info(f"สต็อคคงเหลือ: {product.stock_quantity:.2f} {product.unit}")
                
                col1, col2 = st.columns(2)
                with col1:
                    quantity = st.number_input("จำนวน *", min_value=0.01, value=1.0, step=0.01, max_value=float(product.stock_quantity) if product else None)
                    unit_price = st.number_input("ราคาต่อหน่วย", min_value=0.0, value=float(product.cost_price) if product else 0.0)
                
                with col2:
                    total_cost = quantity * unit_price
                    st.metric("รวมต้นทุน", format_currency(total_cost))
                    reason = st.text_input("เหตุผล *", placeholder="เช่น เสียหาย, ขาย, ใช้")
                
                if st.form_submit_button("📤 บันทึกสต็อคออก", type="primary", width='stretch'):
                    if not reason:
                        st.warning("⚠️ กรุณากรอกเหตุผล")
                    elif product and quantity > product.stock_quantity:
                        st.error(f"❌ สต็อคไม่พอ (มี {product.stock_quantity:.2f} {product.unit})")
                    else:
                        try:
                            # Create transaction
                            transaction = StockTransaction(
                                product_id=product_id,
                                transaction_type='out',
                                quantity=quantity,
                                unit_price=unit_price,
                                total_cost=total_cost,
                                reason=reason,
                                created_by=st.session_state.user_id
                            )
                            session.add(transaction)
                            
                            # Update product stock
                            if product:
                                product.stock_quantity -= quantity
                                if product.stock_quantity < 0:
                                    product.stock_quantity = 0
                            
                            session.commit()
                            print(f"[DEBUG] บันทึกสต็อคออก - Product: {product.name if product else 'N/A'}, Qty: {quantity}, Reason: {reason}, User: {st.session_state.user_id} - {datetime.now()}")
                            st.success("✅ บันทึกสต็อคออกสำเร็จ")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        finally:
            session.close()
    
    # Stock transaction history
    st.divider()
    st.subheader("📜 ประวัติสต็อค")
    
    session = get_session()
    try:
        col1, col2 = st.columns(2)
        with col1:
            days = st.number_input("แสดงย้อนหลัง (วัน)", min_value=1, value=7, step=1)
        with col2:
            transaction_type = st.selectbox("ประเภท", ["ทั้งหมด", "เข้า", "ออก"])
        
        query = session.query(StockTransaction)
        
        if transaction_type == "เข้า":
            query = query.filter(StockTransaction.transaction_type == 'in')
        elif transaction_type == "ออก":
            query = query.filter(StockTransaction.transaction_type == 'out')
        
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(StockTransaction.created_at >= start_date)
        
        transactions = query.order_by(StockTransaction.created_at.desc()).limit(100).all()
        
        if transactions:
            trans_data = []
            for trans in transactions:
                trans_data.append({
                    'วันที่': format_date(trans.created_at),
                    'สินค้า': trans.product.name,
                    'ประเภท': '📥 เข้า' if trans.transaction_type == 'in' else '📤 ออก',
                    'จำนวน': f"{trans.quantity:.2f} {trans.product.unit}",
                    'ราคาต่อหน่วย': format_currency(trans.unit_price),
                    'รวม': format_currency(trans.total_cost),
                    'เหตุผล': trans.reason or '-',
                    'ผู้ทำ': trans.creator.username if trans.creator else '-'
                })
            
            df = pd.DataFrame(trans_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("ไม่มีประวัติสต็อค")
    finally:
        session.close()

if __name__ == "__main__":
    main()

