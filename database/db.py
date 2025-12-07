"""
Database Connection and Initialization
Supports both SQLite (local) and PostgreSQL/MySQL (cloud) for persistent storage
"""

import os
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from database.models import (
    Base, User, Category, Product, Menu, MenuItem, StockTransaction, 
    Sale, SaleItem, Customer, Membership, LoyaltyTransaction, Coupon, CouponUsage,
    EmployeeShift, Attendance, Expense, ExpenseCategory, Promotion, PromotionRule, PromotionUsage,
    Branch, StockTransfer, Supplier, PurchaseOrder, PurchaseOrderItem, Batch, StoreSetting, SavedLogin,
    Table, CustomerOrder, OrderItem, KitchenQueue
)
import bcrypt

def get_database_url():
    """
    Get database URL from environment variables or Streamlit secrets
    Priority:
    1. Streamlit secrets (for Streamlit Cloud)
    2. Environment variables
    3. Default to SQLite (local development)
    """
    # Check if running on Streamlit Cloud
    is_streamlit_cloud = os.environ.get('STREAMLIT_CLOUD', '').lower() == 'true'
    if is_streamlit_cloud:
        print("[DEBUG] 🌐 Running on Streamlit Cloud - checking for database secrets...")
    
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        # Check if Streamlit secrets are available
        if not hasattr(st, 'secrets'):
            print(f"[DEBUG] ⚠️ st.secrets not available")
            if is_streamlit_cloud:
                print(f"[DEBUG] ❌ CRITICAL: On Streamlit Cloud but st.secrets is not available!")
                print(f"[DEBUG] 💡 Please check Streamlit Cloud Secrets configuration")
        elif 'database' not in st.secrets:
            print(f"[DEBUG] ⚠️ 'database' not found in st.secrets")
            print(f"[DEBUG] Available secrets keys: {list(st.secrets.keys()) if hasattr(st, 'secrets') else 'N/A'}")
            if is_streamlit_cloud:
                print(f"[DEBUG] ❌ CRITICAL: On Streamlit Cloud but '[database]' section not found in secrets!")
                print(f"[DEBUG] 💡 Please add '[database]' section to Streamlit Cloud Secrets")
                print(f"[DEBUG] 💡 See: คู่มือตั้งค่า_Streamlit_Cloud_Supabase.md")
        else:
            db_config = st.secrets['database']
            db_type = db_config.get('type', 'sqlite').lower()
            
            print(f"[DEBUG] ========================================")
            print(f"[DEBUG] Reading database config from Streamlit secrets:")
            print(f"[DEBUG] ========================================")
            print(f"[DEBUG]   type: {db_type}")
            print(f"[DEBUG]   host: {db_config.get('host', 'NOT SET')}")
            print(f"[DEBUG]   port: {db_config.get('port', 'NOT SET')}")
            print(f"[DEBUG]   user: {db_config.get('user', 'NOT SET')}")
            print(f"[DEBUG]   database: {db_config.get('database', 'NOT SET')}")
            print(f"[DEBUG]   password: {'***' if db_config.get('password') else 'MISSING'}")
            print(f"[DEBUG] ========================================")
            
            if db_type == 'postgresql':
                # PostgreSQL connection
                user = db_config.get('user')
                password = db_config.get('password')
                host = db_config.get('host')
                port = db_config.get('port', 5432)
                database = db_config.get('database')
                
                # Check if using Direct Connection (will fail on Streamlit Cloud)
                if host and 'db.' in host and '.supabase.co' in host and port == 5432:
                    print(f"[DEBUG] ⚠️ WARNING: Using Direct Connection (IPv6 only)")
                    print(f"[DEBUG] ⚠️ This will FAIL on Streamlit Cloud!")
                    print(f"[DEBUG] ⚠️ Please use Transaction Pooler instead:")
                    print(f"[DEBUG] ⚠️   host: aws-X-REGION.pooler.supabase.com")
                    print(f"[DEBUG] ⚠️   port: 6543")
                    print(f"[DEBUG] ⚠️   user: postgres.PROJECT_REF")
                
                if all([user, password, host, database]):
                    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                    print(f"[DEBUG] ✅ Using PostgreSQL connection: postgresql://{user}:***@{host}:{port}/{database}")
                    return database_url
                else:
                    missing = [k for k, v in {'user': user, 'password': password, 'host': host, 'database': database}.items() if not v]
                    print(f"[DEBUG] ❌ Missing required fields: {missing}")
            
            elif db_type == 'mysql':
                # MySQL connection
                user = db_config.get('user')
                password = db_config.get('password')
                host = db_config.get('host')
                port = db_config.get('port', 3306)
                database = db_config.get('database')
                
                if all([user, password, host, database]):
                    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            
            elif db_type == 'sqlite':
                # SQLite with custom path
                db_path = db_config.get('path', 'data/pos.db')
                return f"sqlite:///{db_path}"
    except Exception as e:
        print(f"[DEBUG] ❌ Error reading Streamlit secrets: {e}")
        import traceback
        traceback.print_exc()
    
    # Try environment variables
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Check if it's Direct Connection (will fail on Streamlit Cloud)
        if 'db.' in database_url and '.supabase.co:5432' in database_url:
            print(f"[DEBUG] ⚠️ WARNING: DATABASE_URL is Direct Connection (IPv6 only)")
            print(f"[DEBUG] ⚠️ This will fail on Streamlit Cloud! Use Transaction Pooler instead.")
            print(f"[DEBUG] ⚠️ DATABASE_URL: {database_url.split('@')[0]}@***")
        print(f"[DEBUG] ✅ Using DATABASE_URL from environment variable")
        return database_url
    
    # Default to SQLite (local development)
    # Check for persistent disk (Render.com) first
    if os.path.exists("/data"):
        # Render.com persistent disk - data will persist!
        DB_DIR = "/data"
        os.makedirs(DB_DIR, exist_ok=True)
        print("✅ Using persistent disk at /data (Render.com)")
    elif os.path.exists("/tmp"):
        # Streamlit Cloud or Linux - use /tmp (temporary, will be lost on restart)
        # ⚠️ WARNING: On Streamlit Cloud, SQLite in /tmp will be LOST on restart!
        DB_DIR = "/tmp"
        if is_streamlit_cloud:
            print("="*60)
            print("❌ CRITICAL WARNING: Using SQLite on Streamlit Cloud!")
            print("="*60)
            print("⚠️ ข้อมูลจะหายเมื่อ app restart!")
            print("⚠️ ข้อมูลจะหายเมื่อ redeploy!")
            print()
            print("💡 วิธีแก้ไข:")
            print("   1. ไปที่ Streamlit Cloud Dashboard")
            print("   2. เลือก App ของคุณ")
            print("   3. ไปที่ Settings > Secrets")
            print("   4. เพิ่ม '[database]' section:")
            print("      [database]")
            print("      type = 'postgresql'")
            print("      host = 'aws-1-ap-southeast-1.pooler.supabase.com'")
            print("      port = 6543")
            print("      user = 'postgres.thvvvsyujfzntvepmvzo'")
            print("      database = 'postgres'")
            print("      password = 'YOUR_PASSWORD'")
            print()
            print("💡 ดูคู่มือ: คู่มือตั้งค่า_Streamlit_Cloud_Supabase.md")
            print("="*60)
        else:
            print("⚠️ WARNING: Using SQLite in /tmp - data will be LOST on restart!")
            print("💡 For persistent storage:")
            print("   - Streamlit Cloud: Use external database (PostgreSQL/MySQL)")
            print("   - Render.com: Use persistent disk at /data")
            print("💡 See STREAMLIT_CLOUD_DATABASE.md or RENDER_DEPLOY.md for setup instructions")
    else:
        # Local development
        DB_DIR = "data"
        os.makedirs(DB_DIR, exist_ok=True)
    
    DB_PATH = os.path.join(DB_DIR, "pos.db")
    sqlite_url = f"sqlite:///{DB_PATH}"
    print(f"[DEBUG] ⚠️ No database config found, defaulting to SQLite: {sqlite_url}")
    if is_streamlit_cloud:
        print(f"[DEBUG] ❌ This is a problem! Please configure Streamlit Cloud Secrets!")
    return sqlite_url

# Export DB_PATH and DB_DIR for backward compatibility
# Note: These are only valid when using SQLite
# For PostgreSQL/MySQL, these variables are not used
try:
    # Try to get DB_DIR from the default SQLite path
    if os.path.exists("/data"):
        DB_DIR = "/data"
    elif os.path.exists("/tmp"):
        DB_DIR = "/tmp"
    else:
        DB_DIR = "data"
    DB_PATH = os.path.join(DB_DIR, "pos.db")
except:
    DB_DIR = "data"
    DB_PATH = os.path.join(DB_DIR, "pos.db")

# Get database URL
DATABASE_URL = get_database_url()

# Debug: Show final database URL (hide password)
if DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('mysql://'):
    # Hide password in debug output
    import re
    safe_url = re.sub(r':([^:@]+)@', ':***@', DATABASE_URL)
    print(f"[DEBUG] 🔗 Final DATABASE_URL: {safe_url}")
else:
    print(f"[DEBUG] 🔗 Final DATABASE_URL: {DATABASE_URL}")

# Determine database type
is_postgresql = DATABASE_URL.startswith('postgresql://')
is_mysql = DATABASE_URL.startswith('mysql://') or DATABASE_URL.startswith('mysql+pymysql://')
is_sqlite = DATABASE_URL.startswith('sqlite:///')

# Create engine with appropriate settings
if is_sqlite:
    # SQLite specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
elif is_postgresql:
    # PostgreSQL specific settings
    # For Connection Pooler (Transaction Mode), disable prepared statements
    # Transaction mode does not support prepared statements
    pooler_mode = os.environ.get('SUPABASE_POOLER_MODE', '')
    if '6543' in DATABASE_URL or pooler_mode == 'transaction':
        # Transaction mode pooler - disable prepared statements
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            connect_args={"options": "-c statement_timeout=30000"},  # 30 second timeout
            echo=False
        )
    else:
        # Direct connection or Session mode - can use prepared statements
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            echo=False
        )
elif is_mysql:
    # MySQL specific settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )
else:
    # Default
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_barcode_image_path_column():
    """Ensure barcode_image_path column exists in products table (called on-demand)"""
    try:
        if is_postgresql:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'products' AND column_name = 'barcode_image_path'
                """))
                columns = [row[0] for row in result]
                if 'barcode_image_path' not in columns:
                    print("[INFO] ⚠️ barcode_image_path column missing - adding now...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path VARCHAR(500)"))
                    print("[INFO] ✅ barcode_image_path column added successfully")
                    # Invalidate SQLAlchemy metadata cache
                    from sqlalchemy import inspect
                    try:
                        inspect(engine).clear_cache()
                    except:
                        pass
                else:
                    print("[DEBUG] ✅ barcode_image_path column already exists")
        elif is_mysql:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 'products' 
                    AND column_name = 'barcode_image_path'
                """))
                columns = [row[0] for row in result]
                if 'barcode_image_path' not in columns:
                    print("[INFO] ⚠️ barcode_image_path column missing - adding now...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path VARCHAR(500)"))
                    print("[INFO] ✅ barcode_image_path column added successfully")
                else:
                    print("[DEBUG] ✅ barcode_image_path column already exists")
        else:  # SQLite
            conn = engine.connect()
            result = conn.execute(text("PRAGMA table_info(products)"))
            columns = [row[1] for row in result]
            if 'barcode_image_path' not in columns:
                print("[INFO] ⚠️ barcode_image_path column missing - adding now...")
                conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path TEXT"))
                conn.commit()
                print("[INFO] ✅ barcode_image_path column added successfully")
            else:
                print("[DEBUG] ✅ barcode_image_path column already exists")
            conn.close()
    except Exception as e:
        print(f"[ERROR] ❌ Error ensuring barcode_image_path column: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - let the app continue, but log the error clearly

def get_session() -> Session:
    """Get database session"""
    # Ensure barcode_image_path column exists before creating session
    ensure_barcode_image_path_column()
    return SessionLocal()

def init_db():
    """Initialize database - create all tables"""
    # Import models to ensure they're registered with Base
    from database.models import StoreSetting, SavedLogin, Table, CustomerOrder, OrderItem, KitchenQueue
    
    # Create all tables including new ones
    print("[INFO] Creating all database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[INFO] ✅ All tables created via Base.metadata.create_all()")
    except Exception as e:
        print(f"[WARNING] Base.metadata.create_all() failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Force create new tables if they don't exist (for existing databases)
    # Use connection with explicit transaction for PostgreSQL
    try:
        print("[INFO] Verifying new tables exist...")
        # For PostgreSQL, we need to commit DDL statements explicitly
        if is_postgresql:
            with engine.begin() as conn:  # Use begin() for auto-commit/rollback
                try:
                    StoreSetting.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ store_settings table verified")
                    SavedLogin.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ saved_logins table verified")
                    Table.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ tables table verified")
                    CustomerOrder.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ customer_orders table verified")
                    OrderItem.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ order_items table verified")
                    KitchenQueue.__table__.create(bind=conn, checkfirst=True)
                    print("[INFO] ✅ kitchen_queue table verified")
                    print("[INFO] ✅ All new tables committed successfully")
                except Exception as e:
                    print(f"[ERROR] Failed to create tables: {e}")
                    import traceback
                    traceback.print_exc()
                    raise e
        else:
            # For SQLite/MySQL, use checkfirst=True directly
            StoreSetting.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ store_settings table verified")
            SavedLogin.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ saved_logins table verified")
            Table.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ tables table verified")
            CustomerOrder.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ customer_orders table verified")
            OrderItem.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ order_items table verified")
            KitchenQueue.__table__.create(bind=engine, checkfirst=True)
            print("[INFO] ✅ kitchen_queue table verified")
        
        # Verify tables actually exist by querying them
        print("[INFO] Verifying tables can be queried...")
        session = get_session()
        try:
            # Try to query each table to verify they exist
            if is_postgresql:
                result = session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('tables', 'customer_orders', 'order_items', 'kitchen_queue', 'store_settings', 'saved_logins')"))
                count = result.scalar()
                print(f"[INFO] ✅ Found {count} new tables in database")
            else:
                # For SQLite, just try to query
                session.query(Table).limit(1).all()
                session.query(CustomerOrder).limit(1).all()
                session.query(OrderItem).limit(1).all()
                session.query(KitchenQueue).limit(1).all()
                print("[INFO] ✅ All new tables are queryable")
        except Exception as e:
            print(f"[WARNING] Could not verify tables: {e}")
        finally:
            session.close()
    except Exception as e:
        print(f"[WARNING] Error verifying tables: {e}")
        import traceback
        traceback.print_exc()
    
    # Initialize default settings
    try:
        from utils.store_settings import init_default_settings
        init_default_settings()
    except Exception as e:
        print(f"[WARNING] Failed to initialize default settings: {e}")
        import traceback
        traceback.print_exc()
    
    # Add missing columns for existing databases
    # Note: PostgreSQL and MySQL use different syntax
    try:
        conn = engine.connect()
        
        # Get table columns based on database type
        if is_sqlite:
            # SQLite: Use PRAGMA
            result = conn.execute(text("PRAGMA table_info(sales)"))
            columns = [row[1] for row in result]
        elif is_postgresql:
            # PostgreSQL: Query information_schema
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sales'
            """))
            columns = [row[0] for row in result]
        elif is_mysql:
            # MySQL: Query information_schema
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND table_name = 'sales'
            """))
            columns = [row[0] for row in result]
        else:
            columns = []
        
        # Define default values based on database type
        if is_sqlite:
            bool_default = "0"
            float_default = "0"
        else:
            bool_default = "FALSE"
            float_default = "0.0"
        
        # Add columns with appropriate syntax
        if 'is_void' not in columns:
            if is_sqlite:
                conn.execute(text("ALTER TABLE sales ADD COLUMN is_void BOOLEAN DEFAULT 0"))
            else:
                conn.execute(text("ALTER TABLE sales ADD COLUMN is_void BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN void_reason TEXT"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN voided_by INTEGER"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN voided_at TIMESTAMP"))
        
        if 'discount_amount' not in columns:
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN discount_amount FLOAT DEFAULT {float_default}"))
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN final_amount FLOAT DEFAULT {float_default}"))
            # Update existing records: final_amount = total_amount
            conn.execute(text("UPDATE sales SET final_amount = total_amount WHERE final_amount = 0 OR final_amount IS NULL"))
        
        # Add new columns for CRM and cashless payment
        if 'customer_id' not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN customer_id INTEGER"))
            conn.execute(text("ALTER TABLE sales ADD COLUMN payment_reference TEXT"))
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN points_earned FLOAT DEFAULT {float_default}"))
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN points_used FLOAT DEFAULT {float_default}"))
        
        # Add tax columns
        if 'tax_rate' not in columns:
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN tax_rate FLOAT DEFAULT {float_default}"))
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN tax_amount FLOAT DEFAULT {float_default}"))
            conn.execute(text(f"ALTER TABLE sales ADD COLUMN subtotal FLOAT DEFAULT {float_default}"))
        
        # Add branch_id column for multi-branch support
        if 'branch_id' not in columns:
            conn.execute(text("ALTER TABLE sales ADD COLUMN branch_id INTEGER"))
        
        # Update payment_method to support new payment types
        # Note: SQLite doesn't support ALTER COLUMN, so we'll handle this in application code
        
        # Check sale_items table columns
        if is_sqlite:
            result_items = conn.execute(text("PRAGMA table_info(sale_items)"))
            item_columns = [row[1] for row in result_items]
        elif is_postgresql:
            result_items = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sale_items'
            """))
            item_columns = [row[0] for row in result_items]
        elif is_mysql:
            result_items = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND table_name = 'sale_items'
            """))
            item_columns = [row[0] for row in result_items]
        else:
            item_columns = []
        
        if 'discount_amount' not in item_columns:
            float_default = "0" if is_sqlite else "0.0"
            conn.execute(text(f"ALTER TABLE sale_items ADD COLUMN discount_amount FLOAT DEFAULT {float_default}"))
        
        # Check products table columns
        if is_sqlite:
            result_products = conn.execute(text("PRAGMA table_info(products)"))
            product_columns = [row[1] for row in result_products]
        elif is_postgresql:
            result_products = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products'
            """))
            product_columns = [row[0] for row in result_products]
        elif is_mysql:
            result_products = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND table_name = 'products'
            """))
            product_columns = [row[0] for row in result_products]
        else:
            product_columns = []
        
        if 'branch_id' not in product_columns:
            conn.execute(text("ALTER TABLE products ADD COLUMN branch_id INTEGER"))
        
        if 'reorder_point' not in product_columns:
            float_default = "0" if is_sqlite else "0.0"
            conn.execute(text(f"ALTER TABLE products ADD COLUMN reorder_point FLOAT DEFAULT {float_default}"))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration note: {e}")
    
    # Migrate qr_code column from VARCHAR(500) to TEXT for tables table
    try:
        if is_postgresql:
            with engine.connect() as conn:
                # Check if qr_code column exists and is VARCHAR(500)
                result = conn.execute(text("""
                    SELECT data_type, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = 'tables' AND column_name = 'qr_code'
                """))
                row = result.fetchone()
                if row and row[0] == 'character varying' and row[1] == 500:
                    print("[INFO] Migrating qr_code column from VARCHAR(500) to TEXT...")
                    with conn.begin():
                        conn.execute(text("ALTER TABLE tables ALTER COLUMN qr_code TYPE TEXT"))
                    print("[INFO] ✅ qr_code column migrated to TEXT")
        elif is_sqlite:
            # SQLite doesn't need migration - TEXT is already flexible
            pass
        elif is_mysql:
            with engine.connect() as conn:
                # Check if qr_code column exists and is VARCHAR(500)
                result = conn.execute(text("""
                    SELECT DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                    FROM information_schema.columns 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 'tables' 
                    AND column_name = 'qr_code'
                """))
                row = result.fetchone()
                if row and row[0] == 'varchar' and row[1] == 500:
                    print("[INFO] Migrating qr_code column from VARCHAR(500) to TEXT...")
                    with conn.begin():
                        conn.execute(text("ALTER TABLE tables MODIFY COLUMN qr_code TEXT"))
                    print("[INFO] ✅ qr_code column migrated to TEXT")
    except Exception as e:
        print(f"[WARNING] Error migrating qr_code column: {e}")
        import traceback
        traceback.print_exc()
    
    # Add barcode_image_path column to products table if it doesn't exist
    try:
        print("[INFO] Checking for barcode_image_path column in products table...")
        if is_postgresql:
            with engine.begin() as conn:  # Use begin() for auto-commit
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'products' AND column_name = 'barcode_image_path'
                """))
                columns = [row[0] for row in result]
                if 'barcode_image_path' not in columns:
                    print("[INFO] Adding barcode_image_path column to products table...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path VARCHAR(500)"))
                    print("[INFO] ✅ barcode_image_path column added")
                else:
                    print("[INFO] ✅ barcode_image_path column already exists")
        elif is_mysql:
            with engine.begin() as conn:  # Use begin() for auto-commit
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 'products' 
                    AND column_name = 'barcode_image_path'
                """))
                columns = [row[0] for row in result]
                if 'barcode_image_path' not in columns:
                    print("[INFO] Adding barcode_image_path column to products table...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path VARCHAR(500)"))
                    print("[INFO] ✅ barcode_image_path column added")
                else:
                    print("[INFO] ✅ barcode_image_path column already exists")
        else:  # SQLite
            conn = engine.connect()
            result = conn.execute(text("PRAGMA table_info(products)"))
            columns = [row[1] for row in result]
            if 'barcode_image_path' not in columns:
                print("[INFO] Adding barcode_image_path column to products table...")
                conn.execute(text("ALTER TABLE products ADD COLUMN barcode_image_path TEXT"))
                conn.commit()
                print("[INFO] ✅ barcode_image_path column added")
            else:
                print("[INFO] ✅ barcode_image_path column already exists")
            conn.close()
    except Exception as e:
        print(f"[ERROR] Error adding barcode_image_path column: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - let the app continue, but log the error
    
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

