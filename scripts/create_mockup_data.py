"""
Script สำหรับสร้างข้อมูล Mockup สำหรับระบบ POS
รวมสินค้า, เมนูอาหาร, และข้อมูลอื่นๆ

รองรับทั้ง SQLite (local) และ PostgreSQL/MySQL (Supabase)
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_session, init_db, hash_password, DB_PATH
from database.models import Category, Product, Menu, MenuItem, User
import toml

def get_database_url_for_script():
    """
    Get database URL for script (outside Streamlit context)
    Priority:
    1. Environment variables (DATABASE_URL)
    2. Streamlit secrets file (.streamlit/secrets.toml)
    3. Default to SQLite (local development)
    """
    # Try environment variables first
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"[DEBUG] ✅ ใช้ DATABASE_URL จาก environment variable")
        return database_url
    
    # Try reading from .streamlit/secrets.toml
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.streamlit', 'secrets.toml')
    if os.path.exists(secrets_path):
        try:
            secrets = toml.load(secrets_path)
            if 'database' in secrets:
                db_config = secrets['database']
                db_type = db_config.get('type', 'sqlite').lower()
                
                if db_type == 'postgresql':
                    user = db_config.get('user')
                    password = db_config.get('password')
                    host = db_config.get('host')
                    port = db_config.get('port', 5432)
                    database = db_config.get('database')
                    
                    if all([user, password, host, database]):
                        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                        print(f"[DEBUG] ✅ อ่าน database config จาก .streamlit/secrets.toml (PostgreSQL)")
                        return database_url
                elif db_type == 'mysql':
                    user = db_config.get('user')
                    password = db_config.get('password')
                    host = db_config.get('host')
                    port = db_config.get('port', 3306)
                    database = db_config.get('database')
                    
                    if all([user, password, host, database]):
                        database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
                        print(f"[DEBUG] ✅ อ่าน database config จาก .streamlit/secrets.toml (MySQL)")
                        return database_url
                elif db_type == 'sqlite':
                    db_path = db_config.get('path', 'data/pos.db')
                    database_url = f"sqlite:///{db_path}"
                    print(f"[DEBUG] ✅ อ่าน database config จาก .streamlit/secrets.toml (SQLite)")
                    return database_url
        except Exception as e:
            print(f"[DEBUG] ⚠️ ไม่สามารถอ่าน secrets.toml: {e}")
    
    # Default to SQLite (local development)
    if os.path.exists("/data"):
        DB_DIR = "/data"
        os.makedirs(DB_DIR, exist_ok=True)
    elif os.path.exists("/tmp"):
        DB_DIR = "/tmp"
    else:
        DB_DIR = "data"
        os.makedirs(DB_DIR, exist_ok=True)
    
    DB_PATH = os.path.join(DB_DIR, "pos.db")
    database_url = f"sqlite:///{DB_PATH}"
    print(f"[DEBUG] ⚠️ ไม่พบ database config, ใช้ SQLite: {database_url}")
    return database_url

def check_database_type():
    """ตรวจสอบประเภท database ที่ใช้"""
    database_url = get_database_url_for_script()
    if database_url.startswith('postgresql://'):
        return 'postgresql'
    elif database_url.startswith('mysql://') or database_url.startswith('mysql+pymysql://'):
        return 'mysql'
    else:
        return 'sqlite'

def check_database_type():
    """ตรวจสอบประเภท database ที่ใช้"""
    database_url = get_database_url_for_script()
    if database_url.startswith('postgresql://'):
        return 'postgresql'
    elif database_url.startswith('mysql://') or database_url.startswith('mysql+pymysql://'):
        return 'mysql'
    else:
        return 'sqlite'

def create_mockup_data():
    """
    Create mockup data for POS system
    Returns: dict with counts of created items
    """
    session = get_session()
    
    try:
        result = {
            'categories': 0,
            'products': 0,
            'menus': 0,
            'menu_items': 0,
            'success': False,
            'error': None
        }
        
        print("🚀 เริ่มสร้างข้อมูล Mockup...")
        
        # Get or create categories
        categories = {}
        category_names = ["อาหารแห้ง", "เครื่องดื่ม", "วัตถุดิบ", "อื่นๆ"]
        
        for cat_name in category_names:
            category = session.query(Category).filter(Category.name == cat_name).first()
            if not category:
                category = Category(name=cat_name, description=f"หมวดหมู่{cat_name}")
                session.add(category)
                session.flush()
                result['categories'] += 1
            categories[cat_name] = category
        
        session.commit()
        print("✅ สร้างหมวดหมู่สำเร็จ")
        
        # สินค้าและวัตถุดิบ (30 รายการ)
        products_data = [
            # อาหารแห้ง
            {"name": "บะหมี่กึ่งสำเร็จรูป", "category": "อาหารแห้ง", "unit": "ห่อ", "cost": 8.0, "selling": 12.0, "stock": 100, "min_stock": 20, "barcode": "8850123456789"},
            {"name": "ข้าวสาร", "category": "อาหารแห้ง", "unit": "ถุง", "cost": 45.0, "selling": 55.0, "stock": 50, "min_stock": 10, "barcode": "8850123456790"},
            {"name": "น้ำตาลทราย", "category": "อาหารแห้ง", "unit": "กก.", "cost": 35.0, "selling": 42.0, "stock": 30, "min_stock": 5, "barcode": "8850123456791"},
            {"name": "เกลือ", "category": "อาหารแห้ง", "unit": "กก.", "cost": 12.0, "selling": 18.0, "stock": 25, "min_stock": 5, "barcode": "8850123456792"},
            {"name": "น้ำมันพืช", "category": "อาหารแห้ง", "unit": "ขวด", "cost": 65.0, "selling": 75.0, "stock": 40, "min_stock": 10, "barcode": "8850123456793"},
            {"name": "ซอสหอยนางรม", "category": "อาหารแห้ง", "unit": "ขวด", "cost": 28.0, "selling": 35.0, "stock": 35, "min_stock": 10, "barcode": "8850123456794"},
            {"name": "น้ำปลา", "category": "อาหารแห้ง", "unit": "ขวด", "cost": 32.0, "selling": 40.0, "stock": 30, "min_stock": 10, "barcode": "8850123456795"},
            {"name": "พริกแกง", "category": "อาหารแห้ง", "unit": "ถุง", "cost": 15.0, "selling": 22.0, "stock": 20, "min_stock": 5, "barcode": "8850123456796"},
            {"name": "กะทิ", "category": "อาหารแห้ง", "unit": "กระป๋อง", "cost": 18.0, "selling": 25.0, "stock": 45, "min_stock": 10, "barcode": "8850123456797"},
            {"name": "ถั่วลิสง", "category": "อาหารแห้ง", "unit": "กก.", "cost": 85.0, "selling": 100.0, "stock": 15, "min_stock": 5, "barcode": "8850123456798"},
            
            # เครื่องดื่ม
            {"name": "น้ำดื่ม", "category": "เครื่องดื่ม", "unit": "ขวด", "cost": 4.0, "selling": 7.0, "stock": 200, "min_stock": 50, "barcode": "8850123456799"},
            {"name": "โค้ก", "category": "เครื่องดื่ม", "unit": "กระป๋อง", "cost": 12.0, "selling": 18.0, "stock": 150, "min_stock": 30, "barcode": "8850123456800"},
            {"name": "เป๊ปซี่", "category": "เครื่องดื่ม", "unit": "กระป๋อง", "cost": 12.0, "selling": 18.0, "stock": 120, "min_stock": 30, "barcode": "8850123456801"},
            {"name": "น้ำส้ม", "category": "เครื่องดื่ม", "unit": "กล่อง", "cost": 15.0, "selling": 22.0, "stock": 80, "min_stock": 20, "barcode": "8850123456802"},
            {"name": "ชาเขียว", "category": "เครื่องดื่ม", "unit": "ขวด", "cost": 10.0, "selling": 15.0, "stock": 100, "min_stock": 25, "barcode": "8850123456803"},
            {"name": "กาแฟสำเร็จรูป", "category": "เครื่องดื่ม", "unit": "ซอง", "cost": 3.0, "selling": 5.0, "stock": 300, "min_stock": 50, "barcode": "8850123456804"},
            {"name": "นม", "category": "เครื่องดื่ม", "unit": "กล่อง", "cost": 18.0, "selling": 25.0, "stock": 60, "min_stock": 15, "barcode": "8850123456805"},
            {"name": "น้ำแข็ง", "category": "เครื่องดื่ม", "unit": "ถุง", "cost": 8.0, "selling": 12.0, "stock": 40, "min_stock": 10, "barcode": "8850123456806"},
            
            # วัตถุดิบ
            {"name": "เส้นก๋วยเตี๋ยว", "category": "วัตถุดิบ", "unit": "กก.", "cost": 35.0, "selling": 0, "stock": 20, "min_stock": 5, "barcode": "8850123456807"},
            {"name": "หมูสับ", "category": "วัตถุดิบ", "unit": "กก.", "cost": 180.0, "selling": 0, "stock": 10, "min_stock": 3, "barcode": "8850123456808"},
            {"name": "ไก่สับ", "category": "วัตถุดิบ", "unit": "กก.", "cost": 120.0, "selling": 0, "stock": 8, "min_stock": 3, "barcode": "8850123456809"},
            {"name": "กุ้ง", "category": "วัตถุดิบ", "unit": "กก.", "cost": 250.0, "selling": 0, "stock": 5, "min_stock": 2, "barcode": "8850123456810"},
            {"name": "ไข่ไก่", "category": "วัตถุดิบ", "unit": "ฟอง", "cost": 4.5, "selling": 0, "stock": 100, "min_stock": 30, "barcode": "8850123456811"},
            {"name": "ผักบุ้ง", "category": "วัตถุดิบ", "unit": "กก.", "cost": 25.0, "selling": 0, "stock": 12, "min_stock": 3, "barcode": "8850123456812"},
            {"name": "ถั่วงอก", "category": "วัตถุดิบ", "unit": "กก.", "cost": 20.0, "selling": 0, "stock": 15, "min_stock": 5, "barcode": "8850123456813"},
            {"name": "ต้นหอม", "category": "วัตถุดิบ", "unit": "กก.", "cost": 40.0, "selling": 0, "stock": 8, "min_stock": 2, "barcode": "8850123456814"},
            {"name": "ผักชี", "category": "วัตถุดิบ", "unit": "กก.", "cost": 50.0, "selling": 0, "stock": 6, "min_stock": 2, "barcode": "8850123456815"},
            {"name": "พริกขี้หนู", "category": "วัตถุดิบ", "unit": "กก.", "cost": 80.0, "selling": 0, "stock": 4, "min_stock": 1, "barcode": "8850123456816"},
            {"name": "กระเทียม", "category": "วัตถุดิบ", "unit": "กก.", "cost": 60.0, "selling": 0, "stock": 10, "min_stock": 3, "barcode": "8850123456817"},
            {"name": "หอมแดง", "category": "วัตถุดิบ", "unit": "กก.", "cost": 45.0, "selling": 0, "stock": 8, "min_stock": 2, "barcode": "8850123456818"},
        ]
        
        # สร้างสินค้า
        created_products = {}
        for prod_data in products_data:
            # ตรวจสอบว่ามีสินค้านี้อยู่แล้วหรือไม่
            existing = session.query(Product).filter(Product.name == prod_data["name"]).first()
            if not existing:
                product = Product(
                    name=prod_data["name"],
                    category_id=categories[prod_data["category"]].id,
                    unit=prod_data["unit"],
                    cost_price=prod_data["cost"],
                    selling_price=prod_data["selling"],
                    stock_quantity=prod_data["stock"],
                    min_stock=prod_data["min_stock"],
                    barcode=prod_data.get("barcode"),
                    image_path=f"https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=400&fit=crop"
                )
                session.add(product)
                session.flush()
                created_products[prod_data["name"]] = product
            else:
                created_products[prod_data["name"]] = existing
        
        session.commit()
        result['products'] = len(created_products)
        print(f"✅ สร้างสินค้า {len(created_products)} รายการสำเร็จ")
        
        # เมนูอาหาร (20 เมนู)
        menus_data = [
            {
                "name": "ก๋วยเตี๋ยวน้ำใส",
                "description": "ก๋วยเตี๋ยวน้ำใส หมูสับ",
                "price": 50.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                    {"product": "ผักชี", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำ",
                "description": "ก๋วยเตี๋ยวต้มยำ หมูสับ",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสไก่",
                "description": "ก๋วยเตี๋ยวน้ำใส ไก่สับ",
                "price": 50.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "ไก่สับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำกุ้ง",
                "description": "ก๋วยเตี๋ยวต้มยำ กุ้ง",
                "price": 70.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "กุ้ง", "quantity": 0.08},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวผัดซีอิ๊ว",
                "description": "ก๋วยเตี๋ยวผัดซีอิ๊ว หมูสับ",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ผักบุ้ง", "quantity": 0.1},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวแห้ง",
                "description": "ก๋วยเตี๋ยวแห้ง หมูสับ",
                "price": 50.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสพิเศษ",
                "description": "ก๋วยเตี๋ยวน้ำใส หมู+ไข่+กุ้ง",
                "price": 75.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.08},
                    {"product": "กุ้ง", "quantity": 0.05},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวเย็นตาโฟ",
                "description": "เย็นตาโฟ หมูสับ",
                "price": 60.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสไข่ลวก",
                "description": "ก๋วยเตี๋ยวน้ำใส หมู+ไข่ลวก",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 2},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำหมู",
                "description": "ก๋วยเตี๋ยวต้มยำ หมูสับ",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสไก่พิเศษ",
                "description": "ก๋วยเตี๋ยวน้ำใส ไก่+ไข่",
                "price": 60.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "ไก่สับ", "quantity": 0.12},
                    {"product": "ไข่ไก่", "quantity": 2},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำกุ้งพิเศษ",
                "description": "ก๋วยเตี๋ยวต้มยำ กุ้ง+ไข่",
                "price": 80.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "กุ้ง", "quantity": 0.12},
                    {"product": "ไข่ไก่", "quantity": 2},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวผัดซีอิ๊วไก่",
                "description": "ก๋วยเตี๋ยวผัดซีอิ๊ว ไก่สับ",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "ไก่สับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ผักบุ้ง", "quantity": 0.1},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสไข่ดิบ",
                "description": "ก๋วยเตี๋ยวน้ำใส หมู+ไข่ดิบ",
                "price": 55.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำไข่ลวก",
                "description": "ก๋วยเตี๋ยวต้มยำ หมู+ไข่ลวก",
                "price": 60.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 2},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสกุ้ง",
                "description": "ก๋วยเตี๋ยวน้ำใส กุ้ง",
                "price": 65.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "กุ้ง", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวแห้งไก่",
                "description": "ก๋วยเตี๋ยวแห้ง ไก่สับ",
                "price": 50.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "ไก่สับ", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวน้ำใสหมูพิเศษ",
                "description": "ก๋วยเตี๋ยวน้ำใส หมู+ไข่+กุ้ง",
                "price": 75.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "หมูสับ", "quantity": 0.08},
                    {"product": "กุ้ง", "quantity": 0.05},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวต้มยำกุ้งไข่ลวก",
                "description": "ก๋วยเตี๋ยวต้มยำ กุ้ง+ไข่ลวก",
                "price": 85.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "กุ้ง", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 2},
                    {"product": "ถั่วงอก", "quantity": 0.05},
                    {"product": "พริกขี้หนู", "quantity": 0.01},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
            {
                "name": "ก๋วยเตี๋ยวผัดซีอิ๊วกุ้ง",
                "description": "ก๋วยเตี๋ยวผัดซีอิ๊ว กุ้ง",
                "price": 70.0,
                "bom": [
                    {"product": "เส้นก๋วยเตี๋ยว", "quantity": 0.15},
                    {"product": "กุ้ง", "quantity": 0.1},
                    {"product": "ไข่ไก่", "quantity": 1},
                    {"product": "ผักบุ้ง", "quantity": 0.1},
                    {"product": "ต้นหอม", "quantity": 0.02},
                ],
                "image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=400&fit=crop"
            },
        ]
        
        # สร้างเมนู
        created_menus = {}
        for menu_data in menus_data:
            # ตรวจสอบว่ามีเมนูนี้อยู่แล้วหรือไม่
            existing = session.query(Menu).filter(Menu.name == menu_data["name"]).first()
            if not existing:
                menu = Menu(
                    name=menu_data["name"],
                    description=menu_data["description"],
                    price=menu_data["price"],
                    is_active=True,
                    image_path=menu_data["image"]
                )
                session.add(menu)
                session.flush()
                
                # สร้าง BOM (Bill of Materials)
                menu_items_count = 0
                for bom_item in menu_data["bom"]:
                    product = created_products.get(bom_item["product"])
                    if product:
                        menu_item = MenuItem(
                            menu_id=menu.id,
                            product_id=product.id,
                            quantity=bom_item["quantity"]
                        )
                        session.add(menu_item)
                        menu_items_count += 1
                
                result['menu_items'] += menu_items_count
                created_menus[menu_data["name"]] = menu
            else:
                created_menus[menu_data["name"]] = existing
        
        session.commit()
        result['menus'] = len(created_menus)
        print(f"✅ สร้างเมนู {len(created_menus)} รายการสำเร็จ")
        
        print("\n" + "="*50)
        print("✅ สร้างข้อมูล Mockup สำเร็จ!")
        print("="*50)
        print(f"📦 สินค้า: {len(created_products)} รายการ")
        print(f"🍜 เมนู: {len(created_menus)} รายการ")
        print(f"📊 รวมทั้งหมด: {len(created_products) + len(created_menus)} รายการ")
        print("="*50)
        
        result['success'] = True
        return result
        
    except Exception as e:
        session.rollback()
        error_msg = f"❌ เกิดข้อผิดพลาด: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        result['error'] = str(e)
        result['success'] = False
        return result
    finally:
        session.close()

if __name__ == "__main__":
    print("="*60)
    print("🚀 สร้างข้อมูล Mockup สำหรับระบบ POS")
    print("="*60)
    
    # ตรวจสอบประเภท database
    db_type = check_database_type()
    print(f"📊 ตรวจพบ Database: {db_type.upper()}")
    if db_type == 'postgresql':
        print("✅ กำลังเชื่อมต่อ Supabase PostgreSQL...")
    elif db_type == 'mysql':
        print("✅ กำลังเชื่อมต่อ MySQL...")
    else:
        print(f"✅ กำลังใช้ SQLite: {DB_PATH}")
    print()
    
    # Initialize database
    print("🔄 กำลังสร้างตาราง...")
    init_db()
    print("✅ สร้างตารางสำเร็จ")
    print()
    
    # Create mockup data
    create_mockup_data()
    
    print()
    print("="*60)
    print("🎉 เสร็จสิ้น! ข้อมูล Mockup ถูกสร้างเรียบร้อยแล้ว")
    print("="*60)
    print()
    print("📝 ข้อมูลที่สร้าง:")
    print("   - หมวดหมู่: 4 หมวด")
    print("   - สินค้า: 30 รายการ (อาหารแห้ง, เครื่องดื่ม, วัตถุดิบ)")
    print("   - เมนูก๋วยเตี๋ยว: 20 เมนู พร้อม BOM")
    print()
    print("💡 ตรวจสอบข้อมูลได้ที่:")
    if db_type == 'postgresql':
        print("   - Supabase Dashboard > Table Editor")
    else:
        print(f"   - Database file: {DB_PATH}")
    print("="*60)

