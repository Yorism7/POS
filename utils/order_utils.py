"""
Order Utilities - ฟังก์ชันช่วยเหลือสำหรับระบบสั่งอาหาร
"""

from datetime import datetime
from database.db import get_session
from database.models import Table, CustomerOrder, OrderItem, KitchenQueue, Menu, OrderStatus
import uuid
import qrcode
from io import BytesIO
import base64

def generate_order_number():
    """สร้างเลขที่ออเดอร์"""
    date_str = datetime.now().strftime("%Y%m%d")
    # สร้าง unique ID แบบสั้น
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"ORD-{date_str}-{unique_id}"

def create_order(table_id, items, customer_name=None, customer_phone=None, notes=None):
    """
    สร้างออเดอร์ใหม่
    
    Args:
        table_id: ID ของโต๊ะ
        items: List of dicts with 'menu_id', 'quantity', 'special_instructions'
        customer_name: ชื่อลูกค้า (optional)
        customer_phone: เบอร์โทรลูกค้า (optional)
        notes: หมายเหตุ (optional)
    
    Returns:
        CustomerOrder object
    """
    session = get_session()
    try:
        # สร้างออเดอร์
        order = CustomerOrder(
            order_number=generate_order_number(),
            table_id=table_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            status='pending',
            notes=notes
        )
        session.add(order)
        session.flush()  # เพื่อให้ได้ order.id
        
        total_amount = 0.0
        
        # เพิ่มรายการอาหาร
        for item_data in items:
            menu = session.query(Menu).filter(Menu.id == item_data['menu_id']).first()
            if not menu or not menu.is_active:
                continue
            
            quantity = item_data.get('quantity', 1)
            unit_price = menu.price
            subtotal = unit_price * quantity
            
            order_item = OrderItem(
                order_id=order.id,
                menu_id=menu.id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                special_instructions=item_data.get('special_instructions')
            )
            session.add(order_item)
            total_amount += subtotal
            
            # สร้างคิวทำอาหาร
            queue_item = KitchenQueue(
                order_id=order.id,
                menu_id=menu.id,
                quantity=quantity,
                status='pending',
                priority=0,
                notes=item_data.get('special_instructions')
            )
            session.add(queue_item)
        
        order.total_amount = total_amount
        session.commit()
        return order
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_table_by_qr(qr_data):
    """หาโต๊ะจาก QR Code data"""
    session = get_session()
    try:
        # QR Code อาจเป็น table_id หรือ URL ที่มี table_id
        table_id = None
        if qr_data.isdigit():
            table_id = int(qr_data)
        elif 'table_id=' in qr_data:
            # Extract table_id from URL
            import urllib.parse
            parsed = urllib.parse.urlparse(qr_data)
            params = urllib.parse.parse_qs(parsed.query)
            if 'table_id' in params:
                table_id = int(params['table_id'][0])
        
        if table_id:
            table = session.query(Table).filter(Table.id == table_id, Table.is_active == True).first()
            return table
        return None
    finally:
        session.close()

def get_order_by_id(order_id):
    """ดึงออเดอร์จาก ID"""
    session = get_session()
    try:
        return session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    finally:
        session.close()

def update_order_status(order_id, status, user_id=None):
    """อัพเดทสถานะออเดอร์"""
    session = get_session()
    try:
        order = session.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
        if not order:
            return False
        
        order.status = status
        order.updated_at = datetime.now()
        
        if status == 'confirmed':
            order.confirmed_at = datetime.now()
        elif status == 'completed':
            order.completed_at = datetime.now()
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def update_queue_status(queue_id, status, user_id=None):
    """อัพเดทสถานะคิว"""
    session = get_session()
    try:
        queue = session.query(KitchenQueue).filter(KitchenQueue.id == queue_id).first()
        if not queue:
            return False
        
        queue.status = status
        if status == 'preparing' and not queue.started_at:
            queue.started_at = datetime.now()
            queue.prepared_by = user_id
        elif status == 'completed':
            queue.completed_at = datetime.now()
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def generate_table_qr_code(table_id, base_url):
    """
    สร้าง QR Code สำหรับโต๊ะ
    
    Args:
        table_id: ID ของโต๊ะ
        base_url: Base URL ของแอป (เช่น https://pos-ez.streamlit.app)
    
    Returns:
        base64 encoded image string
    """
    # สร้าง URL สำหรับสั่งอาหาร
    order_url = f"{base_url}/?table_id={table_id}"
    
    # สร้าง QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(order_url)
    qr.make(fit=True)
    
    # สร้างภาพ
    img = qr.make_image(fill_color="black", back_color="white")
    
    # แปลงเป็น base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str, order_url

