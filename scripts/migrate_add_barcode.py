"""
Migration script to add barcode column to products table
"""

import sqlite3
import os
from database.db import DB_PATH

def migrate_add_barcode():
    """Add barcode column to products table"""
    if not os.path.exists(DB_PATH):
        print("❌ ไม่พบฐานข้อมูล")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'barcode' not in columns:
            print("🔄 กำลังเพิ่มคอลัมน์ barcode...")
            cursor.execute("ALTER TABLE products ADD COLUMN barcode VARCHAR(100)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_barcode ON products(barcode)")
            conn.commit()
            print("✅ เพิ่มคอลัมน์ barcode สำเร็จ")
        else:
            print("✅ คอลัมน์ barcode มีอยู่แล้ว")
        
        conn.close()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    migrate_add_barcode()



