"""
POS Page - ระบบขายสินค้าและเมนู
"""

import streamlit as st
from datetime import datetime
from database.db import get_session
from database.models import Product, Menu, Sale, SaleItem, Customer
from utils.helpers import (
    format_currency, reduce_stock_for_sale, get_or_create_customer,
    get_customer_membership, create_membership, calculate_points_earned,
    calculate_points_value, earn_points, redeem_points, update_membership_after_sale,
    validate_coupon, calculate_coupon_discount, use_coupon
)
from utils.receipt import generate_receipt_text, generate_receipt_pdf
from utils.validators import validate_stock_availability
from utils.sound import play_beep_sound
import json

st.set_page_config(page_title="POS - ขายของ", page_icon="💰", layout="wide")

def init_cart():
    """Initialize cart in session state"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []

def add_to_cart(item_type: str, item_id: int, name: str, price: float, quantity: float = 1.0):
    """Add item to cart"""
    init_cart()
    
    # Check if item already in cart
    for i, item in enumerate(st.session_state.cart):
        if item['type'] == item_type and item['id'] == item_id:
            st.session_state.cart[i]['quantity'] += quantity
            st.session_state.cart[i]['total'] = st.session_state.cart[i]['quantity'] * st.session_state.cart[i]['price']
            return
    
    # Add new item
    st.session_state.cart.append({
        'type': item_type,
        'id': item_id,
        'name': name,
        'price': price,
        'quantity': quantity,
        'total': price * quantity
    })

def remove_from_cart(index: int):
    """Remove item from cart"""
    if 'cart' in st.session_state and 0 <= index < len(st.session_state.cart):
        st.session_state.cart.pop(index)

def clear_cart():
    """Clear cart"""
    if 'cart' in st.session_state:
        st.session_state.cart = []

def get_cart_total() -> float:
    """Get cart total"""
    if 'cart' not in st.session_state:
        return 0.0
    return sum(item['total'] for item in st.session_state.cart)

def apply_discount_to_cart(discount_type: str, discount_value: float):
    """Apply discount to cart"""
    if 'cart' not in st.session_state or not st.session_state.cart:
        st.session_state.cart_discount = 0.0
        return
    
    total = get_cart_total()
    if discount_type == "percent":
        discount = total * (discount_value / 100.0)
    else:  # fixed
        discount = min(discount_value, total)
    
    st.session_state.cart_discount = discount

def get_cart_discount() -> float:
    """Get cart discount"""
    return st.session_state.get('cart_discount', 0.0)

def main():
    st.title("💰 POS - ระบบขายสินค้า")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    init_cart()
    
    # Initialize discount
    if 'cart_discount' not in st.session_state:
        st.session_state.cart_discount = 0.0
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🛍️ เลือกสินค้า/เมนู")
        
        # Barcode scanner options
        scanner_mode = st.radio(
            "วิธีสแกนบาร์โค๊ด",
            ["📷 ใช้กล้องมือถือ/เว็บแคม", "⌨️ ใช้เครื่องยิงบาร์โค๊ด"],
            horizontal=True,
            key="scanner_mode"
        )
        
        if scanner_mode == "📷 ใช้กล้องมือถือ/เว็บแคม":
            st.info("💡 เปิดกล้องและชี้ไปที่บาร์โค๊ด ระบบจะสแกนอัตโนมัติ")
            
            # Camera barcode scanner
            try:
                from components.barcode_scanner import barcode_scanner_component
                scanned_barcode = barcode_scanner_component(key="camera_scanner")
                
                if scanned_barcode:
                    st.session_state['barcode_search'] = scanned_barcode
                    st.session_state['last_barcode'] = scanned_barcode
                    st.rerun()
            except Exception as e:
                st.warning(f"⚠️ ไม่สามารถใช้กล้องได้: {str(e)}")
                st.info("💡 กรุณาใช้วิธีเครื่องยิงบาร์โค๊ดแทน หรืออนุญาตให้เข้าถึงกล้อง")
                # Fallback to manual input
                barcode_input = st.text_input(
                    "📷 พิมพ์บาร์โค๊ด",
                    key="barcode_manual",
                    placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                    help="พิมพ์บาร์โค๊ดแล้วกด Enter"
                )
                if barcode_input:
                    st.session_state['barcode_search'] = barcode_input.strip()
                    st.rerun()
        else:
            # Barcode scanner input (for physical scanner)
            col_barcode, col_barcode_btn = st.columns([3, 1])
            with col_barcode:
                barcode_input = st.text_input(
                    "📷 สแกนบาร์โค๊ด (หรือพิมพ์บาร์โค๊ด)",
                    key="barcode_scanner",
                    placeholder="สแกนบาร์โค๊ดที่นี่...",
                    help="ใช้เครื่องยิงบาร์โค๊ดสแกน หรือพิมพ์บาร์โค๊ดแล้วกด Enter"
                )
            with col_barcode_btn:
                if st.button("🔍 ค้นหา", key="search_barcode", use_container_width=True):
                    if barcode_input:
                        st.session_state['barcode_search'] = barcode_input.strip()
                        st.rerun()
        
        # Handle barcode search when button clicked or Enter pressed
        barcode_to_search = None
        if st.session_state.get('barcode_search'):
            barcode_to_search = st.session_state['barcode_search']
        elif scanner_mode == "⌨️ ใช้เครื่องยิงบาร์โค๊ด" and 'barcode_input' in locals() and barcode_input and barcode_input.strip() and len(barcode_input.strip()) >= 3:
            # Auto-search when barcode is entered (for scanner that auto-enters)
            if 'last_barcode' not in st.session_state or st.session_state['last_barcode'] != barcode_input.strip():
                barcode_to_search = barcode_input.strip()
                st.session_state['last_barcode'] = barcode_input.strip()
        
        if barcode_to_search:
            session = get_session()
            try:
                product = session.query(Product).filter(
                    Product.barcode == barcode_to_search
                ).first()
                
                if product:
                    # Validate stock
                    is_valid, error_msg, available_stock = validate_stock_availability(product.id, 1.0)
                    if is_valid:
                        # Auto-add to cart
                        add_to_cart('product', product.id, product.name, product.selling_price, 1.0)
                        # Play beep sound
                        play_beep_sound()
                        st.success(f"✅ พบสินค้า: {product.name} - เพิ่มลงตะกร้าแล้ว")
                        print(f"[DEBUG] สแกนบาร์โค๊ดสำเร็จ - Barcode: {barcode_to_search}, Product: {product.name} - {datetime.now()}")
                        # Clear barcode search state
                        st.session_state['barcode_search'] = None
                        st.session_state['last_barcode'] = None
                        # Clear input by rerunning
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")
                else:
                    st.warning(f"⚠️ ไม่พบสินค้าที่มีบาร์โค๊ด: {barcode_to_search}")
            finally:
                session.close()
        
        # Tabs for Products and Menus
        tab1, tab2 = st.tabs(["📦 สินค้า", "🍜 เมนู"])
        
        with tab1:
            session = get_session()
            try:
                products = session.query(Product).filter(
                    Product.stock_quantity > 0
                ).order_by(Product.name).all()
                
                if products:
                    # Display products in grid
                    cols = st.columns(3)
                    for idx, product in enumerate(products):
                        with cols[idx % 3]:
                            with st.container():
                                st.write(f"**{product.name}**")
                                st.caption(f"สต็อค: {product.stock_quantity:.2f} {product.unit}")
                                st.write(f"ราคา: {format_currency(product.selling_price)}")
                                
                                col_qty, col_add = st.columns([1, 1])
                                with col_qty:
                                    qty = st.number_input(
                                        "จำนวน",
                                        min_value=0.01,
                                        value=1.0,
                                        step=0.01,
                                        key=f"qty_product_{product.id}",
                                        label_visibility="collapsed"
                                    )
                                with col_add:
                                    if st.button("➕ เพิ่ม", key=f"add_product_{product.id}", use_container_width=True):
                                        # Validate stock availability
                                        is_valid, error_msg, available_stock = validate_stock_availability(product.id, qty)
                                        if is_valid:
                                            add_to_cart('product', product.id, product.name, product.selling_price, qty)
                                            st.success(f"✅ เพิ่ม {product.name} จำนวน {qty:.2f} ลงตะกร้า")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {error_msg}")
                                st.divider()
                else:
                    st.info("ไม่มีสินค้าที่พร้อมขาย")
            finally:
                session.close()
        
        with tab2:
            session = get_session()
            try:
                menus = session.query(Menu).filter(Menu.is_active == True).order_by(Menu.name).all()
                
                if menus:
                    # Display menus in grid
                    cols = st.columns(3)
                    for idx, menu in enumerate(menus):
                        with cols[idx % 3]:
                            with st.container():
                                st.write(f"**{menu.name}**")
                                if menu.description:
                                    st.caption(menu.description)
                                st.write(f"ราคา: {format_currency(menu.price)}")
                                
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
                                    if st.button("➕ เพิ่ม", key=f"add_menu_{menu.id}", use_container_width=True):
                                        add_to_cart('menu', menu.id, menu.name, menu.price, float(qty))
                                        st.success(f"✅ เพิ่ม {menu.name} จำนวน {qty} ลงตะกร้า")
                                        st.rerun()
                                st.divider()
                else:
                    st.info("ไม่มีเมนูที่พร้อมขาย")
            finally:
                session.close()
    
    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        
        if st.session_state.cart:
            total = 0.0
            for idx, item in enumerate(st.session_state.cart):
                col_name, col_del = st.columns([4, 1])
                with col_name:
                    st.write(f"**{item['name']}**")
                    st.caption(f"{item['quantity']:.2f} x {format_currency(item['price'])} = {format_currency(item['total'])}")
                with col_del:
                    if st.button("🗑️", key=f"del_{idx}", help="ลบ"):
                        remove_from_cart(idx)
                        st.rerun()
                total += item['total']
                st.divider()
            
            # Customer selection section
            st.divider()
            st.subheader("👤 ลูกค้า")
            
            customer_search = st.text_input("🔍 ค้นหาลูกค้า (เบอร์โทรหรือชื่อ)", placeholder="พิมพ์เบอร์โทรหรือชื่อ...", key="customer_search")
            selected_customer = None
            membership = None
            points_available = 0.0
            
            if customer_search:
                session = get_session()
                try:
                    # Search by phone first
                    customer = session.query(Customer).filter(Customer.phone.contains(customer_search)).first()
                    if not customer:
                        # Search by name
                        customer = session.query(Customer).filter(Customer.name.contains(customer_search)).first()
                    
                    if customer:
                        selected_customer = customer
                        st.success(f"✅ พบลุกค้า: {customer.name}")
                        if customer.is_member:
                            membership = get_customer_membership(customer.id)
                            if membership:
                                points_available = membership.points
                                st.info(f"⭐ สมาชิก - แต้มสะสม: {points_available:.2f} แต้ม")
                    else:
                        # Option to create new customer
                        if st.button("➕ สร้างลูกค้าใหม่", key="create_customer_btn"):
                            st.session_state['create_customer'] = True
                            st.rerun()
                finally:
                    session.close()
            
            # Create new customer form
            if st.session_state.get('create_customer', False):
                with st.expander("➕ สร้างลูกค้าใหม่", expanded=True):
                    with st.form("quick_create_customer"):
                        new_customer_name = st.text_input("ชื่อ *", key="new_customer_name")
                        new_customer_phone = st.text_input("เบอร์โทร", key="new_customer_phone")
                        make_member = st.checkbox("สมัครสมาชิก", key="make_member_check")
                        
                        col_create, col_cancel = st.columns(2)
                        with col_create:
                            if st.form_submit_button("✅ สร้าง", use_container_width=True):
                                if new_customer_name:
                                    customer = get_or_create_customer(
                                        phone=new_customer_phone if new_customer_phone else None,
                                        name=new_customer_name
                                    )
                                    if customer:
                                        if make_member:
                                            create_membership(customer.id)
                                            customer.is_member = True
                                        selected_customer = customer
                                        st.session_state['create_customer'] = False
                                        st.success(f"✅ สร้างลูกค้า {customer.name} สำเร็จ")
                                        st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ ยกเลิก", use_container_width=True):
                                st.session_state['create_customer'] = False
                                st.rerun()
            
            # Points usage section (if member)
            points_to_use = 0.0
            if selected_customer and membership and points_available > 0:
                st.divider()
                use_points = st.checkbox("ใช้แต้ม", key="use_points_check")
                if use_points:
                    points_value = calculate_points_value(points_available)  # Convert points to baht
                    max_points_to_use = min(points_available, points_value * 10)  # Max points that can be used
                    points_to_use = st.number_input(
                        "จำนวนแต้มที่ใช้",
                        min_value=0.0,
                        max_value=max_points_to_use,
                        value=0.0,
                        step=1.0,
                        key="points_to_use_input"
                    )
                    if points_to_use > 0:
                        points_discount = calculate_points_value(points_to_use)
                        st.info(f"ส่วนลดจากแต้ม: {format_currency(points_discount)}")
            
            # Coupon section
            st.divider()
            st.subheader("🎫 คูปองส่วนลด")
            
            coupon_code = st.text_input("รหัสคูปอง", placeholder="พิมพ์รหัสคูปอง...", key="coupon_code_input").upper()
            coupon_discount = 0.0
            selected_coupon = None
            
            if coupon_code:
                is_valid, coupon, message = validate_coupon(coupon_code, total)
                if is_valid:
                    selected_coupon = coupon
                    coupon_discount = calculate_coupon_discount(coupon, total)
                    st.success(f"✅ {message} - ส่วนลด: {format_currency(coupon_discount)}")
                else:
                    st.warning(f"⚠️ {message}")
            
            # Discount section
            st.divider()
            st.subheader("🎫 ส่วนลดเพิ่มเติม")
            
            discount_type = st.radio(
                "ประเภทส่วนลด",
                ["ไม่มีส่วนลด", "เปอร์เซ็นต์ (%)", "จำนวนเงิน (฿)"],
                horizontal=True,
                key="discount_type"
            )
            
            discount_value = 0.0
            if discount_type == "เปอร์เซ็นต์ (%)":
                discount_value = st.number_input("ส่วนลด (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="discount_percent")
                apply_discount_to_cart("percent", discount_value)
            elif discount_type == "จำนวนเงิน (฿)":
                discount_value = st.number_input("ส่วนลด (฿)", min_value=0.0, max_value=float(total), value=0.0, step=5.0, key="discount_fixed")
                apply_discount_to_cart("fixed", discount_value)
            else:
                st.session_state.cart_discount = 0.0
            
            discount = get_cart_discount()
            # Calculate points discount
            points_discount_amount = 0.0
            if points_to_use > 0:
                points_discount_amount = calculate_points_value(points_to_use)
            
            # Total discount = manual discount + coupon discount + points discount
            total_discount = discount + coupon_discount + points_discount_amount
            final_total = total - total_discount
            if final_total < 0:
                final_total = 0.0
            
            st.markdown(f"### รวม: {format_currency(total)}")
            if total_discount > 0:
                discount_details = []
                if discount > 0:
                    discount_details.append(f"ส่วนลดเพิ่มเติม: {format_currency(discount)}")
                if coupon_discount > 0:
                    discount_details.append(f"คูปอง: {format_currency(coupon_discount)}")
                if points_discount_amount > 0:
                    discount_details.append(f"แต้ม: {format_currency(points_discount_amount)}")
                
                for detail in discount_details:
                    st.caption(f"- {detail}")
                st.markdown(f"### ส่วนลดรวม: -{format_currency(total_discount)}")
            st.markdown(f"### **รวมทั้งสิ้น: {format_currency(final_total)}**")
            
            # Show points to be earned
            if selected_customer and membership:
                points_to_earn = calculate_points_earned(final_total)
                if points_to_earn > 0:
                    st.info(f"⭐ จะได้รับแต้ม: {points_to_earn:.2f} แต้ม")
            
            # Payment section
            st.divider()
            st.subheader("💳 ชำระเงิน")
            
            payment_method = st.radio(
                "วิธีชำระ",
                ["💰 เงินสด", "💳 โอนเงิน", "📱 QR Code (PromptPay)", "💳 บัตรเครดิต/เดบิต"],
                horizontal=True
            )
            
            payment_reference = None
            
            if payment_method == "💰 เงินสด":
                received = st.number_input("รับเงิน", min_value=0.0, value=float(final_total), step=10.0)
                change = received - final_total
                if change >= 0:
                    st.success(f"💰 เงินทอน: {format_currency(change)}")
                else:
                    st.error(f"❌ เงินไม่พอ (ขาด {format_currency(abs(change))})")
            
            elif payment_method == "📱 QR Code (PromptPay)":
                # Generate QR Code for payment
                try:
                    import qrcode
                    from io import BytesIO
                    import base64
                    
                    # Get store phone from settings (default to empty)
                    store_phone = st.session_state.get('store_phone', '')
                    
                    # Create QR Code data (PromptPay format - simplified)
                    # In real implementation, this should follow PromptPay standard
                    qr_data = f"00020101021153037645802TH2937{store_phone}54{final_total:.2f}5802TH6304"
                    
                    # Generate QR Code
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    
                    # Display QR Code
                    st.image(buf, caption=f"สแกนเพื่อชำระเงิน {format_currency(final_total)}", width=300)
                    st.info("💡 ลูกค้าสามารถสแกน QR Code นี้เพื่อชำระเงินผ่านแอปธนาคาร")
                    
                    # Payment reference input
                    payment_reference = st.text_input("เลขที่อ้างอิงการโอน (ถ้ามี)", placeholder="เลขที่อ้างอิง...", key="qr_payment_ref")
                    
                except ImportError:
                    st.warning("⚠️ ต้องการ library qrcode สำหรับสร้าง QR Code")
                    st.info("💡 ติดตั้งด้วย: pip install qrcode[pil]")
                    payment_reference = st.text_input("เลขที่อ้างอิงการโอน", placeholder="เลขที่อ้างอิง...", key="qr_payment_ref")
                except Exception as e:
                    st.warning(f"⚠️ ไม่สามารถสร้าง QR Code: {str(e)}")
                    payment_reference = st.text_input("เลขที่อ้างอิงการโอน", placeholder="เลขที่อ้างอิง...", key="qr_payment_ref")
            
            elif payment_method == "💳 บัตรเครดิต/เดบิต":
                payment_reference = st.text_input("เลขที่บัตร/เลขที่อ้างอิง", placeholder="เลขที่บัตรหรือเลขที่อ้างอิง...", key="card_payment_ref")
                st.info("💡 กรุณาบันทึกเลขที่อ้างอิงการชำระเงิน")
            
            elif payment_method == "💳 โอนเงิน":
                payment_reference = st.text_input("เลขที่อ้างอิงการโอน", placeholder="เลขที่อ้างอิง...", key="transfer_payment_ref")
            
            col_pay, col_clear = st.columns(2)
            with col_pay:
                if st.button("✅ ชำระเงิน", type="primary", use_container_width=True, disabled=(payment_method == "💰 เงินสด" and change < 0)):
                    # Process payment with loading state
                    with st.spinner("⏳ กำลังประมวลผลการชำระเงิน..."):
                        session = get_session()
                        try:
                            # Create sale
                            sale = Sale(
                                sale_date=datetime.now(),
                                total_amount=total,
                                discount_amount=total_discount,
                                final_amount=final_total,
                                payment_method=('cash' if payment_method == "💰 เงินสด" else 
                                              'qr_code' if payment_method == "📱 QR Code (PromptPay)" else
                                              'credit_card' if payment_method == "💳 บัตรเครดิต/เดบิต" else 'transfer'),
                                payment_reference=payment_reference if payment_reference else None,
                                customer_id=selected_customer.id if selected_customer else None,
                                points_earned=calculate_points_earned(final_total) if selected_customer and membership else 0.0,
                                points_used=points_to_use if points_to_use > 0 else 0.0,
                                created_by=st.session_state.user_id
                            )
                            session.add(sale)
                            session.flush()  # Get sale.id
                            
                            # Calculate item discount (proportional)
                            item_discount_ratio = discount / total if total > 0 else 0
                            
                            # Create sale items
                            for item in st.session_state.cart:
                                item_discount = item['total'] * item_discount_ratio
                                sale_item = SaleItem(
                                    sale_id=sale.id,
                                    product_id=item['id'] if item['type'] == 'product' else None,
                                    menu_id=item['id'] if item['type'] == 'menu' else None,
                                    item_type=item['type'],
                                    quantity=item['quantity'],
                                    unit_price=item['price'],
                                    discount_amount=item_discount,
                                    total_price=item['total'] - item_discount
                                )
                                session.add(sale_item)
                            
                            session.commit()
                            print(f"[DEBUG] สร้างการขายสำเร็จ - Sale ID: {sale.id}, Total: {total}, User: {st.session_state.user_id} - {datetime.now()}")
                            
                            # Handle customer and membership
                            if selected_customer:
                                # Update membership stats
                                update_membership_after_sale(selected_customer.id, sale.id, final_total)
                                
                                # Earn points
                                if sale.points_earned > 0:
                                    earn_points(
                                        selected_customer.id,
                                        sale.id,
                                        sale.points_earned,
                                        f"ได้รับแต้มจากการซื้อ #{sale.id:06d}"
                                    )
                                
                                # Redeem points
                                if points_to_use > 0:
                                    redeem_points(
                                        selected_customer.id,
                                        sale.id,
                                        points_to_use,
                                        f"ใช้แต้มในการซื้อ #{sale.id:06d}"
                                    )
                            
                            # Use coupon
                            if selected_coupon:
                                use_coupon(
                                    selected_coupon.id,
                                    sale.id,
                                    selected_customer.id if selected_customer else None,
                                    coupon_discount
                                )
                            
                            # Reduce stock
                            try:
                                with st.spinner("⏳ กำลังลดสต็อค..."):
                                    reduce_stock_for_sale(sale.id, st.session_state.user_id)
                                    print(f"[DEBUG] ลดสต็อคสำเร็จ - Sale ID: {sale.id} - {datetime.now()}")
                            except Exception as e:
                                print(f"[DEBUG] เกิดข้อผิดพลาดในการลดสต็อค: {str(e)} - {datetime.now()}")
                                st.error(f"❌ เกิดข้อผิดพลาดในการลดสต็อค: {str(e)}")
                            
                            st.success(f"✅ ชำระเงินสำเร็จ! เลขที่: {sale.id:06d}")
                            
                            # Show receipt
                            st.subheader("🧾 ใบเสร็จ")
                            receipt_text = generate_receipt_text(sale.id)
                            st.code(receipt_text, language=None)
                            
                            # Download receipt
                            col_dl_pdf, col_dl_txt = st.columns(2)
                            with col_dl_pdf:
                                try:
                                    pdf_path = generate_receipt_pdf(sale.id)
                                    with open(pdf_path, 'rb') as f:
                                        st.download_button(
                                            "📄 ดาวน์โหลด PDF",
                                            f.read(),
                                            file_name=f"receipt_{sale.id:06d}.pdf",
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                                except Exception as e:
                                    st.error(f"❌ ไม่สามารถสร้าง PDF: {str(e)}")
                            
                            with col_dl_txt:
                                st.download_button(
                                    "📝 ดาวน์โหลด Text",
                                    receipt_text,
                                    file_name=f"receipt_{sale.id:06d}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            
                            # Clear cart and discount
                            clear_cart()
                            st.session_state.cart_discount = 0.0
                            if 'customer_search' in st.session_state:
                                del st.session_state['customer_search']
                            if 'create_customer' in st.session_state:
                                del st.session_state['create_customer']
                            st.rerun()
                            
                        except Exception as e:
                            session.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                        finally:
                            session.close()
            
            with col_clear:
                if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                    clear_cart()
                    st.rerun()
        else:
            st.info("🛒 ตะกร้าว่างเปล่า")

if __name__ == "__main__":
    main()

