"""
Script สำหรับลบข้อมูล Mockup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_session
from database.models import Product, Menu, MenuItem

def clear_mockup_data():
    """Clear mockup data from database"""
    session = get_session()
    
    try:
        print("🗑️ กำลังลบข้อมูล Mockup...")
        
        # ลบเมนูและ BOM
        menus = session.query(Menu).all()
        menu_count = len(menus)
        for menu in menus:
            session.delete(menu)
        
        # ลบสินค้า (ยกเว้นสินค้าที่มี sale_items หรือ stock_transactions)
        products = session.query(Product).all()
        product_count = 0
        for product in products:
            # ตรวจสอบว่ามีการใช้งานหรือไม่
            if len(product.sale_items) == 0 and len(product.stock_transactions) == 0:
                session.delete(product)
                product_count += 1
        
        session.commit()
        print(f"✅ ลบเมนู {menu_count} รายการ")
        print(f"✅ ลบสินค้า {product_count} รายการ")
        print("✅ ลบข้อมูล Mockup สำเร็จ")
        
    except Exception as e:
        session.rollback()
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    confirm = input("⚠️ คุณแน่ใจหรือไม่ที่จะลบข้อมูล Mockup? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_mockup_data()
    else:
        print("❌ ยกเลิกการลบข้อมูล")

