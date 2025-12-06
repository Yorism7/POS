"""
Category Management Page - จัดการหมวดหมู่
"""

import streamlit as st
from datetime import datetime
from database.db import get_session
from database.models import Category, Product
from utils.pagination import paginate_items

st.set_page_config(page_title="จัดการหมวดหมู่", page_icon="📁", layout="wide")

def main():
    st.title("📁 จัดการหมวดหมู่")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Check if admin
    if st.session_state.role != 'admin':
        st.error("❌ เฉพาะผู้ดูแลระบบเท่านั้นที่สามารถเข้าถึงหน้านี้ได้")
        return
    
    # Tabs
    tab1, tab2 = st.tabs(["📋 รายการหมวดหมู่", "➕ เพิ่มหมวดหมู่"])
    
    with tab1:
        st.subheader("📋 รายการหมวดหมู่ทั้งหมด")
        
        session = get_session()
        try:
            all_categories = session.query(Category).order_by(Category.name).all()
            
            # Pagination
            if 'category_page' not in st.session_state:
                st.session_state.category_page = 1
            
            items_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 50], index=0, key="category_items_per_page")
            
            paginated_categories, total_items, total_pages, current_page = paginate_items(
                all_categories,
                st.session_state.category_page,
                items_per_page
            )
            
            st.info(f"📊 แสดง {len(paginated_categories)} จาก {total_items} รายการ (หน้า {current_page}/{total_pages})")
            
            # Pagination controls
            if total_pages > 1:
                col_prev, col_page, col_next = st.columns([1, 3, 1])
                with col_prev:
                    if st.button("◀️ ก่อนหน้า", disabled=(current_page == 1), use_container_width=True, key="cat_prev"):
                        st.session_state.category_page = max(1, current_page - 1)
                        st.rerun()
                with col_page:
                    st.write(f"หน้า {current_page} / {total_pages}")
                with col_next:
                    if st.button("ถัดไป ▶️", disabled=(current_page == total_pages), use_container_width=True, key="cat_next"):
                        st.session_state.category_page = min(total_pages, current_page + 1)
                        st.rerun()
            
            if paginated_categories:
                for category in paginated_categories:
                    # Count products in this category
                    product_count = session.query(Product).filter(Product.category_id == category.id).count()
                    
                    with st.expander(f"📁 {category.name} ({product_count} สินค้า)"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ชื่อหมวดหมู่:** {category.name}")
                            st.write(f"**คำอธิบาย:** {category.description or '-'}")
                            st.write(f"**จำนวนสินค้า:** {product_count} รายการ")
                        
                        with col2:
                            if st.button("✏️ แก้ไข", key=f"edit_cat_{category.id}", use_container_width=True):
                                st.session_state[f"editing_category_{category.id}"] = True
                                st.rerun()
                        
                        with col3:
                            if product_count > 0:
                                st.warning(f"⚠️ มีสินค้า {product_count} รายการในหมวดหมู่นี้")
                            else:
                                if st.button("🗑️ ลบ", key=f"delete_cat_{category.id}", use_container_width=True):
                                    st.session_state[f"confirm_delete_category_{category.id}"] = True
                                    st.rerun()
                            
                            # Confirmation dialog
                            if st.session_state.get(f"confirm_delete_category_{category.id}", False):
                                st.warning(f"⚠️ คุณแน่ใจหรือไม่ที่จะลบหมวดหมู่ {category.name}?")
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ ยืนยัน", key=f"yes_delete_cat_{category.id}", use_container_width=True):
                                        try:
                                            session.delete(category)
                                            session.commit()
                                            st.session_state[f"confirm_delete_category_{category.id}"] = False
                                            st.success(f"✅ ลบหมวดหมู่ {category.name} สำเร็จ")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                with col_no:
                                    if st.button("❌ ยกเลิก", key=f"no_delete_cat_{category.id}", use_container_width=True):
                                        st.session_state[f"confirm_delete_category_{category.id}"] = False
                                        st.rerun()
                        
                        # Edit form
                        if st.session_state.get(f"editing_category_{category.id}", False):
                            st.divider()
                            with st.form(f"edit_category_form_{category.id}"):
                                new_name = st.text_input("ชื่อหมวดหมู่", value=category.name, key=f"cat_name_{category.id}")
                                new_description = st.text_area("คำอธิบาย", value=category.description or "", key=f"cat_desc_{category.id}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("💾 บันทึก", use_container_width=True):
                                        if new_name:
                                            try:
                                                # Check if name already exists
                                                existing = session.query(Category).filter(
                                                    Category.name == new_name,
                                                    Category.id != category.id
                                                ).first()
                                                
                                                if existing:
                                                    st.error("❌ ชื่อหมวดหมู่นี้มีอยู่แล้ว")
                                                else:
                                                    category.name = new_name
                                                    category.description = new_description
                                                    session.commit()
                                                    st.session_state[f"editing_category_{category.id}"] = False
                                                    st.success("✅ บันทึกสำเร็จ")
                                                    st.rerun()
                                            except Exception as e:
                                                session.rollback()
                                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                                        else:
                                            st.warning("⚠️ กรุณากรอกชื่อหมวดหมู่")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                        st.session_state[f"editing_category_{category.id}"] = False
                                        st.rerun()
            else:
                st.info("ไม่มีหมวดหมู่")
        finally:
            session.close()
    
    with tab2:
        st.subheader("➕ เพิ่มหมวดหมู่ใหม่")
        
        session = get_session()
        try:
            with st.form("add_category_form"):
                name = st.text_input("ชื่อหมวดหมู่ *", placeholder="เช่น อาหารแห้ง")
                description = st.text_area("คำอธิบาย", placeholder="คำอธิบายหมวดหมู่...")
                
                if st.form_submit_button("➕ เพิ่มหมวดหมู่", type="primary", use_container_width=True):
                    if name:
                        # Check if category exists
                        existing = session.query(Category).filter(Category.name == name).first()
                        if existing:
                            st.error("❌ หมวดหมู่นี้มีอยู่แล้ว")
                        else:
                            try:
                                category = Category(
                                    name=name,
                                    description=description
                                )
                                session.add(category)
                                session.commit()
                                st.success(f"✅ เพิ่มหมวดหมู่ {name} สำเร็จ")
                                st.rerun()
                            except Exception as e:
                                session.rollback()
                                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                    else:
                        st.warning("⚠️ กรุณากรอกชื่อหมวดหมู่")
        finally:
            session.close()

if __name__ == "__main__":
    main()

