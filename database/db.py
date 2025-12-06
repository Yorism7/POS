"""
Database Connection and Initialization
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, User, Category, Product, Menu, MenuItem, StockTransaction, Sale, SaleItem
import bcrypt

# Database path
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "pos.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create database directory if not exists
os.makedirs(DB_DIR, exist_ok=True)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Session:
    """Get database session"""
    return SessionLocal()

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    
    # Add missing columns for existing databases
    try:
        conn = engine.connect()
        # Check sales table columns
        result = conn.execute(text("PRAGMA table_info(sales)"))
        columns = [row[1] for row in result]
        
        if 'is_void' not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN is_void BOOLEAN DEFAULT 0"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN void_reason TEXT"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN voided_by INTEGER"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN voided_at DATETIME"))
        
        if 'discount_amount' not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN discount_amount FLOAT DEFAULT 0"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN final_amount FLOAT DEFAULT 0"))
            # Update existing records: final_amount = total_amount
            conn.execute(text("UPDATE sales SET final_amount = total_amount WHERE final_amount = 0"))
        
        # Check sale_items table columns
        result_items = conn.execute(text("PRAGMA table_info(sale_items)"))
        item_columns = [row[1] for row in result_items]
        
        if 'discount_amount' not in item_columns:
            conn.execute(text("ALTER TABLE sale_items ADD COLUMN discount_amount FLOAT DEFAULT 0"))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration note: {e}")
    
    # Create default data if needed
    session = get_session()
    try:
        # Create default categories if not exists
        categories_data = [
            {"name": "อาหารแห้ง", "description": "อาหารแห้งและของชำ"},
            {"name": "เครื่องดื่ม", "description": "เครื่องดื่มต่างๆ"},
            {"name": "วัตถุดิบ", "description": "วัตถุดิบสำหรับทำอาหาร"},
            {"name": "อื่นๆ", "description": "สินค้าอื่นๆ"},
        ]
        
        for cat_data in categories_data:
            existing = session.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                category = Category(**cat_data)
                session.add(category)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error initializing default data: {e}")
    finally:
        session.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

