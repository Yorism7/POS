"""
Barcode Utilities for POS System
"""

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from typing import Optional

def generate_barcode_image(barcode_value: str, barcode_type: str = 'code128') -> Optional[BytesIO]:
    """Generate barcode image"""
    try:
        if barcode_type == 'code128':
            code = barcode.get_barcode_class('code128')
        elif barcode_type == 'ean13':
            code = barcode.get_barcode_class('ean13')
        elif barcode_type == 'ean8':
            code = barcode.get_barcode_class('ean8')
        else:
            code = barcode.get_barcode_class('code128')
        
        barcode_instance = code(barcode_value, writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"[DEBUG] เกิดข้อผิดพลาดในการสร้างบาร์โค๊ด: {str(e)}")
        return None

def validate_barcode(barcode_value: str) -> bool:
    """Validate barcode format"""
    if not barcode_value:
        return False
    # Basic validation - only alphanumeric and some special characters
    if len(barcode_value) < 3 or len(barcode_value) > 100:
        return False
    return True

