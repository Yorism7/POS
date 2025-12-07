"""
Validation Functions for POS System
"""

import re
from typing import Optional, Tuple

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validate username"""
    if not username:
        return False, "กรุณากรอกชื่อผู้ใช้"
    if len(username) < 3:
        return False, "ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร"
    if len(username) > 50:
        return False, "ชื่อผู้ใช้ต้องไม่เกิน 50 ตัวอักษร"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "ชื่อผู้ใช้สามารถใช้ได้เฉพาะตัวอักษร ตัวเลข และ _ เท่านั้น"
    return True, None

def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """Validate password"""
    if not password:
        return False, "กรุณากรอกรหัสผ่าน"
    if len(password) < 4:
        return False, "รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร"
    if len(password) > 100:
        return False, "รหัสผ่านต้องไม่เกิน 100 ตัวอักษร"
    return True, None

def validate_price(price: float, min_value: float = 0.0) -> Tuple[bool, Optional[str]]:
    """Validate price"""
    if price < min_value:
        return False, f"ราคาต้องไม่ต่ำกว่า {min_value:.2f}"
    if price > 999999.99:
        return False, "ราคาต้องไม่เกิน 999,999.99"
    return True, None

def validate_quantity(quantity: float, min_value: float = 0.01) -> Tuple[bool, Optional[str]]:
    """Validate quantity"""
    if quantity < min_value:
        return False, f"จำนวนต้องไม่ต่ำกว่า {min_value:.2f}"
    if quantity > 999999.99:
        return False, "จำนวนต้องไม่เกิน 999,999.99"
    return True, None

def validate_product_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate product name"""
    if not name or not name.strip():
        return False, "กรุณากรอกชื่อสินค้า"
    if len(name.strip()) < 1:
        return False, "ชื่อสินค้าต้องมีอย่างน้อย 1 ตัวอักษร"
    if len(name.strip()) > 200:
        return False, "ชื่อสินค้าต้องไม่เกิน 200 ตัวอักษร"
    return True, None

def validate_stock_availability(product_id: int, requested_quantity: float) -> Tuple[bool, Optional[str], Optional[float]]:
    """Validate stock availability"""
    from database.db import get_session
    from database.models import Product
    
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False, "ไม่พบสินค้า", None
        if product.stock_quantity < requested_quantity:
            return False, f"สต็อคไม่พอ (มี {product.stock_quantity:.2f} {product.unit})", product.stock_quantity
        return True, None, product.stock_quantity
    finally:
        session.close()



