"""
Migration Script - เพิ่มคอลัมน์ใหม่ในตาราง products
รันสคริปต์นี้เพื่อเพิ่มคอลัมน์ branch_id และ reorder_point
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from database.db import DB_PATH, DATABASE_URL

def migrate():
    """Run migration to add new columns"""
    print("Starting migration...")
    
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    conn = engine.connect()
    
    try:
        # Check products table columns
        result = conn.execute(text("PRAGMA table_info(products)"))
        columns = [row[1] for row in result]
        
        print(f"Current columns in products table: {columns}")
        
        # Add branch_id if not exists
        if 'branch_id' not in columns:
            print("Adding branch_id column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN branch_id INTEGER"))
            print("✅ Added branch_id column")
        else:
            print("✓ branch_id column already exists")
        
        # Add reorder_point if not exists
        if 'reorder_point' not in columns:
            print("Adding reorder_point column...")
            conn.execute(text("ALTER TABLE products ADD COLUMN reorder_point FLOAT DEFAULT 0"))
            print("✅ Added reorder_point column")
        else:
            print("✓ reorder_point column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        conn.close()
        engine.dispose()

if __name__ == "__main__":
    migrate()

