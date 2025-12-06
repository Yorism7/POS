"""
Database Models for POS System
SQLAlchemy ORM Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(enum.Enum):
    """Transaction type enum"""
    IN = "in"
    OUT = "out"

class ItemType(enum.Enum):
    """Item type enum"""
    PRODUCT = "product"
    MENU = "menu"

class PaymentMethod(enum.Enum):
    """Payment method enum"""
    CASH = "cash"
    TRANSFER = "transfer"

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='staff')  # admin, staff
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    stock_transactions = relationship("StockTransaction", back_populates="creator")
    sales = relationship("Sale", back_populates="creator")

class Category(Base):
    """Category model"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="category")

class Product(Base):
    """Product model - สินค้า/วัตถุดิบ"""
    __tablename__ = 'products'
    __table_args__ = (
        Index('idx_product_name', 'name'),
        Index('idx_product_stock', 'stock_quantity'),
        Index('idx_product_category', 'category_id'),
        Index('idx_product_barcode', 'barcode'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    unit = Column(String(50), nullable=False, default='ชิ้น')  # หน่วย เช่น ชิ้น, กิโลกรัม, ลิตร
    cost_price = Column(Float, nullable=False, default=0.0)  # ราคาต้นทุน
    selling_price = Column(Float, nullable=False, default=0.0)  # ราคาขาย
    stock_quantity = Column(Float, nullable=False, default=0.0)  # จำนวนสต็อค
    min_stock = Column(Float, nullable=False, default=0.0)  # จำนวนขั้นต่ำ
    barcode = Column(String(100), nullable=True, unique=True, index=True)  # บาร์โค๊ด
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    menu_items = relationship("MenuItem", back_populates="product")
    stock_transactions = relationship("StockTransaction", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")

class Menu(Base):
    """Menu model - เมนูอาหาร"""
    __tablename__ = 'menus'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    image_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    menu_items = relationship("MenuItem", back_populates="menu", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", back_populates="menu")

class MenuItem(Base):
    """MenuItem model - วัตถุดิบในเมนู (Bill of Materials)"""
    __tablename__ = 'menu_items'
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)  # จำนวนวัตถุดิบที่ใช้
    
    # Relationships
    menu = relationship("Menu", back_populates="menu_items")
    product = relationship("Product", back_populates="menu_items")

class StockTransaction(Base):
    """StockTransaction model - บันทึกสต็อคเข้าออก"""
    __tablename__ = 'stock_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    transaction_type = Column(String(10), nullable=False)  # 'in' or 'out'
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    reason = Column(Text, nullable=True)  # เหตุผล เช่น 'ซื้อเข้า', 'ขาย', 'เสียหาย'
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    product = relationship("Product", back_populates="stock_transactions")
    creator = relationship("User", back_populates="stock_transactions")

class Sale(Base):
    """Sale model - การขาย"""
    __tablename__ = 'sales'
    __table_args__ = (
        Index('idx_sale_date', 'sale_date'),
        Index('idx_sale_created_by', 'created_by'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime, default=datetime.now, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)  # ส่วนลดรวม
    final_amount = Column(Float, nullable=False, default=0.0)  # ยอดสุดท้ายหลังหักส่วนลด
    payment_method = Column(String(20), nullable=False, default='cash')  # 'cash', 'transfer'
    is_void = Column(Boolean, default=False, nullable=False)  # ยกเลิกการขาย
    void_reason = Column(Text, nullable=True)  # เหตุผลในการยกเลิก
    voided_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ผู้ยกเลิก
    voided_at = Column(DateTime, nullable=True)  # วันที่ยกเลิก
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    creator = relationship("User", back_populates="sales", foreign_keys=[created_by])
    voider = relationship("User", back_populates="voided_sales", foreign_keys=[voided_by])
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    """SaleItem model - รายการขาย"""
    __tablename__ = 'sale_items'
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)  # null if menu
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=True)  # null if product
    item_type = Column(String(20), nullable=False)  # 'product' or 'menu'
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)  # ส่วนลดต่อรายการ
    total_price = Column(Float, nullable=False)
    
    # Relationships
    sale = relationship("Sale", back_populates="sale_items")
    product = relationship("Product", back_populates="sale_items")
    menu = relationship("Menu", back_populates="sale_items")

