"""
Helper Functions for POS System
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.db import get_session
from database.models import (
    Product, Menu, Sale, SaleItem, StockTransaction, Category,
    Customer, Membership, LoyaltyTransaction, Coupon, CouponUsage
)
from sqlalchemy import func, and_
from functools import lru_cache
import time

def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"฿{amount:,.2f}"

def format_date(date: datetime) -> str:
    """Format datetime as Thai date"""
    return date.strftime("%d/%m/%Y %H:%M")

@lru_cache(maxsize=128)
def _get_today_sales_cached(date_str: str) -> float:
    """Cached version of get_today_sales"""
    session = get_session()
    try:
        today = datetime.strptime(date_str, "%Y-%m-%d").date()
        result = session.query(func.sum(Sale.final_amount)).filter(
            func.date(Sale.sale_date) == today,
            Sale.is_void == False
        ).scalar()
        return result or 0.0
    finally:
        session.close()

def get_today_sales() -> float:
    """Get today's total sales (with caching)"""
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    return _get_today_sales_cached(today_str)

@lru_cache(maxsize=128)
def _get_month_sales_cached(year_month: str) -> float:
    """Cached version of get_month_sales"""
    session = get_session()
    try:
        year, month = map(int, year_month.split("-"))
        first_day = datetime(year, month, 1)
        result = session.query(func.sum(Sale.final_amount)).filter(
            Sale.sale_date >= first_day,
            Sale.is_void == False
        ).scalar()
        return result or 0.0
    finally:
        session.close()

def get_month_sales() -> float:
    """Get this month's total sales (with caching)"""
    today = datetime.now()
    year_month = f"{today.year}-{today.month}"
    return _get_month_sales_cached(year_month)

@lru_cache(maxsize=128)
def _get_today_profit_cached(date_str: str) -> float:
    """Cached version of get_today_profit"""
    session = get_session()
    try:
        today = datetime.strptime(date_str, "%Y-%m-%d").date()
        sales = session.query(Sale).filter(
            func.date(Sale.sale_date) == today,
            Sale.is_void == False
        ).all()
        
        total_profit = 0.0
        for sale in sales:
            for item in sale.sale_items:
                if item.item_type == 'product':
                    # Profit = (selling_price - cost_price) * quantity
                    if item.product:
                        cost = item.product.cost_price
                        profit = (item.unit_price - cost) * item.quantity
                        total_profit += profit
                elif item.item_type == 'menu':
                    # Calculate menu cost from BOM
                    if item.menu:
                        menu_cost = calculate_menu_cost(item.menu_id)
                        profit = (item.unit_price - menu_cost) * item.quantity
                        total_profit += profit
        
        return total_profit
    finally:
        session.close()

def get_today_profit() -> float:
    """Get today's profit (with caching)"""
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    return _get_today_profit_cached(today_str)

def calculate_menu_cost(menu_id: int) -> float:
    """Calculate total cost of a menu from its BOM"""
    session = get_session()
    try:
        menu = session.query(Menu).filter(Menu.id == menu_id).first()
        if not menu:
            return 0.0
        
        total_cost = 0.0
        for menu_item in menu.menu_items:
            if menu_item.product:
                cost = menu_item.product.cost_price * menu_item.quantity
                total_cost += cost
        
        return total_cost
    finally:
        session.close()

def get_low_stock_products(limit: int = 10) -> List[Product]:
    """Get products with low stock"""
    session = get_session()
    try:
        products = session.query(Product).filter(
            Product.stock_quantity <= Product.min_stock
        ).order_by(Product.stock_quantity.asc()).limit(limit).all()
        return products
    finally:
        session.close()

def get_top_selling_menus(limit: int = 10, days: int = 30) -> List[Dict]:
    """Get top selling menus"""
    session = get_session()
    try:
        start_date = datetime.now() - timedelta(days=days)
        results = session.query(
            Menu.id,
            Menu.name,
            func.sum(SaleItem.quantity).label('total_quantity'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(
            SaleItem, SaleItem.menu_id == Menu.id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= start_date
        ).group_by(
            Menu.id, Menu.name
        ).order_by(
            func.sum(SaleItem.quantity).desc()
        ).limit(limit).all()
        
        return [
            {
                'id': r.id,
                'name': r.name,
                'quantity': r.total_quantity or 0,
                'revenue': r.total_revenue or 0.0
            }
            for r in results
        ]
    finally:
        session.close()

def get_sales_by_date(days: int = 30) -> List[Dict]:
    """Get sales grouped by date"""
    session = get_session()
    try:
        start_date = datetime.now() - timedelta(days=days)
        results = session.query(
            func.date(Sale.sale_date).label('date'),
            func.sum(Sale.total_amount).label('total'),
            func.count(Sale.id).label('count')
        ).filter(
            Sale.sale_date >= start_date
        ).group_by(
            func.date(Sale.sale_date)
        ).order_by(
            func.date(Sale.sale_date).asc()
        ).all()
        
        return [
            {
                'date': r.date,
                'total': r.total or 0.0,
                'count': r.count or 0
            }
            for r in results
        ]
    finally:
        session.close()

def reduce_stock_for_sale(sale_id: int, user_id: int):
    """Reduce stock when sale is completed"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return
        
        for item in sale.sale_items:
            if item.item_type == 'product' and item.product_id:
                # Reduce product stock
                product = session.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    new_stock = product.stock_quantity - item.quantity
                    if new_stock < 0:
                        new_stock = 0
                    
                    # Create stock transaction
                    transaction = StockTransaction(
                        product_id=product.id,
                        transaction_type='out',
                        quantity=item.quantity,
                        unit_price=product.cost_price,
                        total_cost=product.cost_price * item.quantity,
                        reason=f'ขาย - Sale #{sale_id}',
                        created_by=user_id
                    )
                    session.add(transaction)
                    
                    # Update stock
                    product.stock_quantity = new_stock
                    
            elif item.item_type == 'menu' and item.menu_id:
                # Reduce stock for menu ingredients
                menu = session.query(Menu).filter(Menu.id == item.menu_id).first()
                if menu:
                    for menu_item in menu.menu_items:
                        if menu_item.product:
                            product = session.query(Product).filter(
                                Product.id == menu_item.product.id
                            ).first()
                            if product:
                                quantity_needed = menu_item.quantity * item.quantity
                                new_stock = product.stock_quantity - quantity_needed
                                if new_stock < 0:
                                    new_stock = 0
                                
                                # Create stock transaction
                                transaction = StockTransaction(
                                    product_id=product.id,
                                    transaction_type='out',
                                    quantity=quantity_needed,
                                    unit_price=product.cost_price,
                                    total_cost=product.cost_price * quantity_needed,
                                    reason=f'ขายเมนู {menu.name} - Sale #{sale_id}',
                                    created_by=user_id
                                )
                                session.add(transaction)
                                
                                # Update stock
                                product.stock_quantity = new_stock
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# ========== CRM and Membership Functions ==========

def calculate_points_earned(amount: float, points_per_baht: float = 0.01) -> float:
    """Calculate points earned from purchase amount
    Default: 1 point per 100 baht (0.01 points per baht)
    """
    return amount * points_per_baht

def calculate_points_value(points: float, points_per_baht: float = 10.0) -> float:
    """Calculate baht value from points
    Default: 10 points = 1 baht
    """
    return points / points_per_baht

def get_or_create_customer(phone: str = None, name: str = None, email: str = None) -> Optional[Customer]:
    """Get existing customer by phone or create new one"""
    session = get_session()
    try:
        customer = None
        if phone:
            customer = session.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer and name:
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                is_member=False
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
        
        return customer
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in get_or_create_customer: {str(e)}")
        return None
    finally:
        session.close()

def create_membership(customer_id: int, member_code: str = None) -> Optional[Membership]:
    """Create membership for customer"""
    session = get_session()
    try:
        # Check if membership already exists
        existing = session.query(Membership).filter(Membership.customer_id == customer_id).first()
        if existing:
            return existing
        
        # Generate member code if not provided
        if not member_code:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                # Generate code from customer ID
                member_code = f"M{customer_id:06d}"
        
        membership = Membership(
            customer_id=customer_id,
            member_code=member_code,
            points=0.0,
            total_spent=0.0,
            total_visits=0,
            is_active=True
        )
        session.add(membership)
        
        # Update customer
        customer = session.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.is_member = True
        
        session.commit()
        session.refresh(membership)
        return membership
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in create_membership: {str(e)}")
        return None
    finally:
        session.close()

def earn_points(customer_id: int, sale_id: int, points: float, description: str = None) -> bool:
    """Add points to customer membership"""
    session = get_session()
    try:
        membership = session.query(Membership).filter(
            Membership.customer_id == customer_id,
            Membership.is_active == True
        ).first()
        
        if not membership:
            return False
        
        # Add points
        membership.points += points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_id=customer_id,
            transaction_type='earn',
            points=points,
            sale_id=sale_id,
            description=description or f"ได้รับแต้มจากการซื้อ #{sale_id}"
        )
        session.add(transaction)
        session.commit()
        
        print(f"[DEBUG] Earned {points} points for customer {customer_id} from sale {sale_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in earn_points: {str(e)}")
        return False
    finally:
        session.close()

def redeem_points(customer_id: int, sale_id: int, points: float, description: str = None) -> bool:
    """Redeem points from customer membership"""
    session = get_session()
    try:
        membership = session.query(Membership).filter(
            Membership.customer_id == customer_id,
            Membership.is_active == True
        ).first()
        
        if not membership or membership.points < points:
            return False
        
        # Deduct points
        membership.points -= points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_id=customer_id,
            transaction_type='redeem',
            points=-points,
            sale_id=sale_id,
            description=description or f"ใช้แต้มในการซื้อ #{sale_id}"
        )
        session.add(transaction)
        session.commit()
        
        print(f"[DEBUG] Redeemed {points} points for customer {customer_id} in sale {sale_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in redeem_points: {str(e)}")
        return False
    finally:
        session.close()

def update_membership_after_sale(customer_id: int, sale_id: int, amount: float):
    """Update membership statistics after sale"""
    session = get_session()
    try:
        membership = session.query(Membership).filter(
            Membership.customer_id == customer_id,
            Membership.is_active == True
        ).first()
        
        if membership:
            membership.total_spent += amount
            membership.total_visits += 1
            membership.last_visit = datetime.now()
            session.commit()
            print(f"[DEBUG] Updated membership stats for customer {customer_id}")
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in update_membership_after_sale: {str(e)}")
    finally:
        session.close()

def get_customer_by_phone(phone: str) -> Optional[Customer]:
    """Get customer by phone number"""
    session = get_session()
    try:
        return session.query(Customer).filter(Customer.phone == phone).first()
    finally:
        session.close()

def get_customer_membership(customer_id: int) -> Optional[Membership]:
    """Get customer membership"""
    session = get_session()
    try:
        return session.query(Membership).filter(
            Membership.customer_id == customer_id,
            Membership.is_active == True
        ).first()
    finally:
        session.close()

def validate_coupon(code: str, amount: float = 0.0) -> tuple[bool, Optional[Coupon], str]:
    """Validate coupon code
    Returns: (is_valid, coupon, message)
    """
    session = get_session()
    try:
        coupon = session.query(Coupon).filter(
            Coupon.code == code.upper(),
            Coupon.is_active == True
        ).first()
        
        if not coupon:
            return False, None, "ไม่พบคูปองนี้"
        
        # Check validity period
        now = datetime.now()
        if now < coupon.valid_from:
            return False, coupon, "คูปองยังไม่สามารถใช้งานได้"
        
        if now > coupon.valid_until:
            return False, coupon, "คูปองหมดอายุแล้ว"
        
        # Check usage limit
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return False, coupon, "คูปองถูกใช้ครบจำนวนแล้ว"
        
        # Check minimum purchase
        if amount < coupon.min_purchase:
            return False, coupon, f"ยอดซื้อขั้นต่ำ {format_currency(coupon.min_purchase)}"
        
        return True, coupon, "คูปองสามารถใช้งานได้"
    finally:
        session.close()

def calculate_coupon_discount(coupon: Coupon, amount: float) -> float:
    """Calculate discount amount from coupon"""
    if coupon.discount_type == 'percent':
        discount = amount * (coupon.discount_value / 100.0)
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
        return discount
    else:  # fixed
        return min(coupon.discount_value, amount)

def use_coupon(coupon_id: int, sale_id: int, customer_id: int = None, discount_amount: float = 0.0) -> bool:
    """Record coupon usage"""
    session = get_session()
    try:
        coupon = session.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return False
        
        # Increment usage count
        coupon.used_count += 1
        
        # Create usage record
        usage = CouponUsage(
            coupon_id=coupon_id,
            sale_id=sale_id,
            customer_id=customer_id,
            discount_amount=discount_amount
        )
        session.add(usage)
        session.commit()
        
        print(f"[DEBUG] Used coupon {coupon.code} in sale {sale_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in use_coupon: {str(e)}")
        return False
    finally:
        session.close()

