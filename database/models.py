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
    sales = relationship("Sale", back_populates="creator", foreign_keys="Sale.created_by")
    voided_sales = relationship("Sale", back_populates="voider", foreign_keys="Sale.voided_by")
    shifts = relationship("EmployeeShift", back_populates="user")
    attendances = relationship("Attendance", back_populates="user")
    expenses = relationship("Expense", back_populates="creator")
    saved_logins = relationship("SavedLogin", back_populates="user", cascade="all, delete-orphan")

class SavedLogin(Base):
    """SavedLogin model - เก็บข้อมูลการล็อคอินที่ต้องการจดจำ"""
    __tablename__ = 'saved_logins'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    username = Column(String(50), nullable=False)  # เก็บ username เพื่อความสะดวก
    remember_token = Column(String(255), nullable=False, unique=True, index=True)  # Token สำหรับ auto-login
    created_at = Column(DateTime, default=datetime.now)
    last_used_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime, nullable=True)  # วันที่หมดอายุ (null = ไม่หมดอายุ)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saved_logins")

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
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)  # สาขา
    branch = relationship("Branch", back_populates="products")
    stock_transfers = relationship("StockTransfer", back_populates="product")
    batches = relationship("Batch", back_populates="product")
    reorder_point = Column(Float, nullable=False, default=0.0)  # จุดสั่งซื้ออัตโนมัติ

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
        Index('idx_sale_customer', 'customer_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime, default=datetime.now, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)  # ส่วนลดรวม
    final_amount = Column(Float, nullable=False, default=0.0)  # ยอดสุดท้ายหลังหักส่วนลด
    payment_method = Column(String(20), nullable=False, default='cash')  # 'cash', 'transfer', 'qr_code', 'credit_card'
    payment_reference = Column(String(200), nullable=True)  # เลขที่อ้างอิงการโอน/บัตร
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)  # ลูกค้า
    points_earned = Column(Float, nullable=False, default=0.0)  # แต้มที่ได้รับ
    points_used = Column(Float, nullable=False, default=0.0)  # แต้มที่ใช้
    tax_rate = Column(Float, nullable=False, default=0.0)  # อัตราภาษี (%)
    tax_amount = Column(Float, nullable=False, default=0.0)  # จำนวนภาษี
    subtotal = Column(Float, nullable=False, default=0.0)  # ยอดก่อนภาษี
    is_void = Column(Boolean, default=False, nullable=False)  # ยกเลิกการขาย
    void_reason = Column(Text, nullable=True)  # เหตุผลในการยกเลิก
    voided_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ผู้ยกเลิก
    voided_at = Column(DateTime, nullable=True)  # วันที่ยกเลิก
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    creator = relationship("User", back_populates="sales", foreign_keys=[created_by])
    voider = relationship("User", back_populates="voided_sales", foreign_keys=[voided_by])
    customer = relationship("Customer", back_populates="sales")
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="sale")
    coupon_usages = relationship("CouponUsage", back_populates="sale")
    promotion_usages = relationship("PromotionUsage", back_populates="sale")
    branch_id = Column(Integer, ForeignKey('branches.id'), nullable=True)  # สาขา
    branch = relationship("Branch", back_populates="sales")

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

class Customer(Base):
    """Customer model - ข้อมูลลูกค้า"""
    __tablename__ = 'customers'
    __table_args__ = (
        Index('idx_customer_phone', 'phone'),
        Index('idx_customer_email', 'email'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), nullable=True, unique=True, index=True)
    email = Column(String(200), nullable=True, index=True)
    address = Column(Text, nullable=True)
    is_member = Column(Boolean, default=False, nullable=False)  # เป็นสมาชิกหรือไม่
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    membership = relationship("Membership", back_populates="customer", uselist=False)
    loyalty_transactions = relationship("LoyaltyTransaction", back_populates="customer")

class Membership(Base):
    """Membership model - ข้อมูลสมาชิก"""
    __tablename__ = 'memberships'
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, unique=True)
    member_code = Column(String(50), nullable=True, unique=True, index=True)  # รหัสสมาชิก
    points = Column(Float, nullable=False, default=0.0)  # แต้มสะสม
    total_spent = Column(Float, nullable=False, default=0.0)  # ยอดซื้อสะสม
    total_visits = Column(Integer, nullable=False, default=0)  # จำนวนครั้งที่ซื้อ
    joined_date = Column(DateTime, default=datetime.now)
    last_visit = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="membership")

class LoyaltyTransaction(Base):
    """LoyaltyTransaction model - บันทึกการสะสม/ใช้แต้ม"""
    __tablename__ = 'loyalty_transactions'
    __table_args__ = (
        Index('idx_loyalty_date', 'transaction_date'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'earn' or 'redeem'
    points = Column(Float, nullable=False)  # จำนวนแต้ม (บวกสำหรับ earn, ลบสำหรับ redeem)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)  # อ้างอิงการขาย (ถ้ามี)
    description = Column(Text, nullable=True)  # คำอธิบาย
    transaction_date = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="loyalty_transactions")
    sale = relationship("Sale", back_populates="loyalty_transactions")

class Coupon(Base):
    """Coupon model - คูปองส่วนลด"""
    __tablename__ = 'coupons'
    __table_args__ = (
        Index('idx_coupon_code', 'code'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # รหัสคูปอง
    name = Column(String(200), nullable=False)  # ชื่อคูปอง
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), nullable=False)  # 'percent' or 'fixed'
    discount_value = Column(Float, nullable=False)  # ค่าส่วนลด (% หรือ ฿)
    min_purchase = Column(Float, nullable=False, default=0.0)  # ยอดซื้อขั้นต่ำ
    max_discount = Column(Float, nullable=True)  # ส่วนลดสูงสุด (สำหรับ percent)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    usage_limit = Column(Integer, nullable=True)  # จำนวนครั้งที่ใช้ได้ (null = ไม่จำกัด)
    used_count = Column(Integer, nullable=False, default=0)  # จำนวนครั้งที่ใช้แล้ว
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    coupon_usages = relationship("CouponUsage", back_populates="coupon")

class CouponUsage(Base):
    """CouponUsage model - บันทึกการใช้งานคูปอง"""
    __tablename__ = 'coupon_usages'
    
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey('coupons.id'), nullable=False)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    discount_amount = Column(Float, nullable=False)  # จำนวนส่วนลดที่ใช้
    used_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    coupon = relationship("Coupon", back_populates="coupon_usages")
    sale = relationship("Sale", back_populates="coupon_usages")
    customer = relationship("Customer")

class EmployeeShift(Base):
    """EmployeeShift model - กะการทำงาน"""
    __tablename__ = 'employee_shifts'
    __table_args__ = (
        Index('idx_shift_date', 'shift_date'),
        Index('idx_shift_user', 'user_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    shift_date = Column(DateTime, nullable=False, index=True)  # วันที่ทำงาน
    shift_start = Column(DateTime, nullable=True)  # เวลาเริ่มกะ
    shift_end = Column(DateTime, nullable=True)  # เวลาสิ้นสุดกะ
    break_duration = Column(Integer, nullable=False, default=0)  # เวลาพัก (นาที)
    notes = Column(Text, nullable=True)  # หมายเหตุ
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="shifts")
    attendances = relationship("Attendance", back_populates="shift")

class Attendance(Base):
    """Attendance model - บันทึกเวลาเข้า-ออกงาน"""
    __tablename__ = 'attendances'
    __table_args__ = (
        Index('idx_attendance_date', 'attendance_date'),
        Index('idx_attendance_user', 'user_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    shift_id = Column(Integer, ForeignKey('employee_shifts.id'), nullable=True)
    attendance_date = Column(DateTime, nullable=False, index=True)  # วันที่
    clock_in = Column(DateTime, nullable=True)  # เวลาเข้า
    clock_out = Column(DateTime, nullable=True)  # เวลาออก
    total_hours = Column(Float, nullable=False, default=0.0)  # จำนวนชั่วโมงทำงาน
    is_late = Column(Boolean, default=False, nullable=False)  # สายหรือไม่
    is_absent = Column(Boolean, default=False, nullable=False)  # ขาดงานหรือไม่
    notes = Column(Text, nullable=True)  # หมายเหตุ
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="attendances")
    shift = relationship("EmployeeShift", back_populates="attendances")

class ExpenseCategory(Base):
    """ExpenseCategory model - หมวดหมู่ค่าใช้จ่าย"""
    __tablename__ = 'expense_categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    expenses = relationship("Expense", back_populates="category")

class Expense(Base):
    """Expense model - ค่าใช้จ่าย"""
    __tablename__ = 'expenses'
    __table_args__ = (
        Index('idx_expense_date', 'expense_date'),
        Index('idx_expense_category', 'category_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=False)
    amount = Column(Float, nullable=False)  # จำนวนเงิน
    description = Column(Text, nullable=True)  # คำอธิบาย
    expense_date = Column(DateTime, nullable=False, index=True)  # วันที่ใช้จ่าย
    receipt_path = Column(String(500), nullable=True)  # ไฟล์ใบเสร็จ
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses")
    creator = relationship("User", back_populates="expenses")

class Branch(Base):
    """Branch model - สาขา"""
    __tablename__ = 'branches'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)  # ชื่อสาขา
    address = Column(Text, nullable=True)  # ที่อยู่
    phone = Column(String(20), nullable=True)  # เบอร์โทร
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    stock_transfers_from = relationship("StockTransfer", back_populates="from_branch", foreign_keys="StockTransfer.from_branch_id")
    stock_transfers_to = relationship("StockTransfer", back_populates="to_branch", foreign_keys="StockTransfer.to_branch_id")
    products = relationship("Product", back_populates="branch")
    sales = relationship("Sale", back_populates="branch")

class StockTransfer(Base):
    """StockTransfer model - การโอนย้ายสินค้าระหว่างสาขา"""
    __tablename__ = 'stock_transfers'
    __table_args__ = (
        Index('idx_transfer_date', 'transfer_date'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    from_branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    to_branch_id = Column(Integer, ForeignKey('branches.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False)  # จำนวนที่โอน
    transfer_date = Column(DateTime, default=datetime.now, index=True)  # วันที่โอน
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'completed', 'cancelled'
    notes = Column(Text, nullable=True)  # หมายเหตุ
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    from_branch = relationship("Branch", back_populates="stock_transfers_from", foreign_keys=[from_branch_id])
    to_branch = relationship("Branch", back_populates="stock_transfers_to", foreign_keys=[to_branch_id])
    product = relationship("Product", back_populates="stock_transfers")
    creator = relationship("User")

class Supplier(Base):
    """Supplier model - ผู้จำหน่าย"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # ชื่อผู้จำหน่าย
    contact_person = Column(String(200), nullable=True)  # ชื่อผู้ติดต่อ
    phone = Column(String(20), nullable=True)  # เบอร์โทร
    email = Column(String(200), nullable=True)  # อีเมล
    address = Column(Text, nullable=True)  # ที่อยู่
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class PurchaseOrder(Base):
    """PurchaseOrder model - ใบสั่งซื้อ"""
    __tablename__ = 'purchase_orders'
    __table_args__ = (
        Index('idx_po_date', 'order_date'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    order_date = Column(DateTime, default=datetime.now, index=True)  # วันที่สั่งซื้อ
    expected_date = Column(DateTime, nullable=True)  # วันที่คาดว่าจะได้รับ
    received_date = Column(DateTime, nullable=True)  # วันที่ได้รับจริง
    total_amount = Column(Float, nullable=False, default=0.0)  # ยอดรวม
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'received', 'cancelled'
    notes = Column(Text, nullable=True)  # หมายเหตุ
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    creator = relationship("User")

class PurchaseOrderItem(Base):
    """PurchaseOrderItem model - รายการในใบสั่งซื้อ"""
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False)  # จำนวนที่สั่ง
    unit_price = Column(Float, nullable=False)  # ราคาต่อหน่วย
    total_price = Column(Float, nullable=False)  # ราคารวม
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")

class Batch(Base):
    """Batch model - Lot/Batch สำหรับติดตามวันหมดอายุ"""
    __tablename__ = 'batches'
    __table_args__ = (
        Index('idx_batch_expiry', 'expiry_date'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    batch_number = Column(String(100), nullable=False)  # เลขที่ Lot/Batch
    quantity = Column(Float, nullable=False)  # จำนวนใน Lot
    remaining_quantity = Column(Float, nullable=False)  # จำนวนคงเหลือ
    production_date = Column(DateTime, nullable=True)  # วันที่ผลิต
    expiry_date = Column(DateTime, nullable=True, index=True)  # วันหมดอายุ
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True)  # อ้างอิงใบสั่งซื้อ
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    product = relationship("Product", back_populates="batches")
    purchase_order = relationship("PurchaseOrder")

class Promotion(Base):
    """Promotion model - โปรโมชั่น"""
    __tablename__ = 'promotions'
    __table_args__ = (
        Index('idx_promotion_date', 'valid_from', 'valid_until'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # ชื่อโปรโมชั่น
    description = Column(Text, nullable=True)  # คำอธิบาย
    promotion_type = Column(String(50), nullable=False)  # 'buy_x_get_y', 'discount', 'time_based', 'member_only'
    discount_type = Column(String(20), nullable=True)  # 'percent' or 'fixed' (for discount type)
    discount_value = Column(Float, nullable=True)  # ค่าส่วนลด
    min_purchase = Column(Float, nullable=False, default=0.0)  # ยอดซื้อขั้นต่ำ
    max_discount = Column(Float, nullable=True)  # ส่วนลดสูงสุด
    buy_quantity = Column(Integer, nullable=True)  # ซื้อ X (for buy_x_get_y)
    get_quantity = Column(Integer, nullable=True)  # แถม Y (for buy_x_get_y)
    time_start = Column(String(10), nullable=True)  # เวลาเริ่ม (HH:MM) for time_based
    time_end = Column(String(10), nullable=True)  # เวลาสิ้นสุด (HH:MM) for time_based
    days_of_week = Column(String(20), nullable=True)  # วันในสัปดาห์ (0=Monday, 6=Sunday) comma-separated
    valid_from = Column(DateTime, nullable=False)  # วันที่เริ่มต้น
    valid_until = Column(DateTime, nullable=False)  # วันที่สิ้นสุด
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    rules = relationship("PromotionRule", back_populates="promotion", cascade="all, delete-orphan")
    usages = relationship("PromotionUsage", back_populates="promotion")

class StoreSetting(Base):
    """StoreSetting model - ตั้งค่าร้านและระบบ"""
    __tablename__ = 'store_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # เช่น 'store_name', 'promptpay_phone'
    value = Column(Text, nullable=True)  # ค่าของการตั้งค่า (JSON string สำหรับข้อมูลซับซ้อน)
    description = Column(Text, nullable=True)  # คำอธิบาย
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ผู้ที่อัพเดทล่าสุด
    
    # Relationships
    updater = relationship("User", foreign_keys=[updated_by])

class PromotionRule(Base):
    """PromotionRule model - เงื่อนไขโปรโมชั่น"""
    __tablename__ = 'promotion_rules'
    
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, ForeignKey('promotions.id'), nullable=False)
    rule_type = Column(String(50), nullable=False)  # 'product', 'menu', 'category', 'member'
    target_id = Column(Integer, nullable=True)  # ID of product/menu/category
    min_quantity = Column(Float, nullable=False, default=1.0)  # จำนวนขั้นต่ำ
    
    # Relationships
    promotion = relationship("Promotion", back_populates="rules")

class PromotionUsage(Base):
    """PromotionUsage model - บันทึกการใช้งานโปรโมชั่น"""
    __tablename__ = 'promotion_usages'
    
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, ForeignKey('promotions.id'), nullable=False)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    discount_amount = Column(Float, nullable=False)  # จำนวนส่วนลดที่ใช้
    used_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    promotion = relationship("Promotion", back_populates="usages")
    sale = relationship("Sale", back_populates="promotion_usages")

class Table(Base):
    """Table model - โต๊ะในร้าน"""
    __tablename__ = 'tables'
    
    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String(20), nullable=False, unique=True, index=True)  # หมายเลขโต๊ะ เช่น "T1", "T2"
    name = Column(String(100), nullable=True)  # ชื่อโต๊ะ (ถ้ามี)
    capacity = Column(Integer, nullable=False, default=4)  # จำนวนที่นั่ง
    qr_code = Column(String(500), nullable=True)  # QR Code URL สำหรับโต๊ะนี้
    is_active = Column(Boolean, default=True, nullable=False)  # เปิดใช้งานหรือไม่
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    orders = relationship("CustomerOrder", back_populates="table")

class OrderStatus(enum.Enum):
    """Order status enum"""
    PENDING = "pending"  # รอการยืนยัน
    CONFIRMED = "confirmed"  # ยืนยันแล้ว
    PREPARING = "preparing"  # กำลังทำ
    READY = "ready"  # พร้อมเสิร์ฟ
    SERVED = "served"  # เสิร์ฟแล้ว
    COMPLETED = "completed"  # เสร็จสิ้น
    CANCELLED = "cancelled"  # ยกเลิก

class CustomerOrder(Base):
    """CustomerOrder model - ออเดอร์จากลูกค้า"""
    __tablename__ = 'customer_orders'
    __table_args__ = (
        Index('idx_order_table', 'table_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_created', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), nullable=False, unique=True, index=True)  # เลขที่ออเดอร์ เช่น "ORD-20250107-001"
    table_id = Column(Integer, ForeignKey('tables.id'), nullable=True)  # โต๊ะ
    customer_name = Column(String(200), nullable=True)  # ชื่อลูกค้า (ถ้าไม่ระบุ = ลูกค้าทั่วไป)
    customer_phone = Column(String(20), nullable=True)  # เบอร์โทรลูกค้า
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, confirmed, preparing, ready, served, completed, cancelled
    total_amount = Column(Float, nullable=False, default=0.0)  # ยอดรวม
    notes = Column(Text, nullable=True)  # หมายเหตุพิเศษ
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    confirmed_at = Column(DateTime, nullable=True)  # วันที่ยืนยันออเดอร์
    completed_at = Column(DateTime, nullable=True)  # วันที่เสร็จสิ้น
    
    # Relationships
    table = relationship("Table", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    queue_items = relationship("KitchenQueue", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    """OrderItem model - รายการในออเดอร์"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('customer_orders.id'), nullable=False, index=True)
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)  # ราคาต่อหน่วย (เก็บไว้เพื่อป้องกันการเปลี่ยนแปลงราคา)
    subtotal = Column(Float, nullable=False)  # ราคารวม (quantity * unit_price)
    special_instructions = Column(Text, nullable=True)  # หมายเหตุพิเศษ เช่น "ไม่เผ็ด", "ไม่ใส่ผัก"
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    order = relationship("CustomerOrder", back_populates="items")
    menu = relationship("Menu")

class KitchenQueue(Base):
    """KitchenQueue model - คิวทำอาหาร"""
    __tablename__ = 'kitchen_queue'
    __table_args__ = (
        Index('idx_queue_status', 'status'),
        Index('idx_queue_priority', 'priority'),
        Index('idx_queue_created', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('customer_orders.id'), nullable=False, index=True)
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, preparing, ready, completed
    priority = Column(Integer, nullable=False, default=0)  # ความสำคัญ (สูงกว่า = สำคัญกว่า)
    started_at = Column(DateTime, nullable=True)  # เริ่มทำเมื่อไหร่
    completed_at = Column(DateTime, nullable=True)  # เสร็จเมื่อไหร่
    prepared_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ใครเป็นคนทำ
    notes = Column(Text, nullable=True)  # หมายเหตุ
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    order = relationship("CustomerOrder", back_populates="queue_items")
    menu = relationship("Menu")
    preparer = relationship("User")
    customer = relationship("Customer")


