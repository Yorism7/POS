"""
Promotion Management Functions
จัดการโปรโมชั่นขั้นสูง
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from database.db import get_session
from database.models import Promotion, PromotionRule, Product, Menu, Category, Customer
from sqlalchemy import and_, or_
from utils.helpers import format_currency

def get_active_promotions(current_time: datetime = None) -> List[Promotion]:
    """Get all active promotions"""
    if current_time is None:
        current_time = datetime.now()
    
    session = get_session()
    try:
        return session.query(Promotion).filter(
            Promotion.is_active == True,
            Promotion.valid_from <= current_time,
            Promotion.valid_until >= current_time
        ).all()
    finally:
        session.close()

def check_promotion_conditions(promotion: Promotion, cart_items: List[Dict], 
                               customer: Optional[Customer] = None, 
                               current_time: datetime = None) -> Tuple[bool, str]:
    """Check if promotion conditions are met
    Returns: (is_valid, message)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Check time-based conditions
    if promotion.promotion_type == 'time_based':
        if promotion.time_start and promotion.time_end:
            current_time_str = current_time.strftime('%H:%M')
            if not (promotion.time_start <= current_time_str <= promotion.time_end):
                return False, "โปรโมชั่นยังไม่ถึงเวลา"
        
        if promotion.days_of_week:
            current_day = str(current_time.weekday())  # 0=Monday, 6=Sunday
            if current_day not in promotion.days_of_week.split(','):
                return False, "โปรโมชั่นไม่ใช้ในวันนี้"
    
    # Check member-only
    if promotion.promotion_type == 'member_only':
        if not customer or not customer.is_member:
            return False, "โปรโมชั่นสำหรับสมาชิกเท่านั้น"
    
    # Check rules
    session = get_session()
    try:
        rules = session.query(PromotionRule).filter(
            PromotionRule.promotion_id == promotion.id
        ).all()
        
        if rules:
            # Check if any rule matches
            rule_matched = False
            for rule in rules:
                if rule.rule_type == 'product':
                    # Check if product is in cart
                    for item in cart_items:
                        if item['type'] == 'product' and item['id'] == rule.target_id:
                            if item['quantity'] >= rule.min_quantity:
                                rule_matched = True
                                break
                elif rule.rule_type == 'menu':
                    # Check if menu is in cart
                    for item in cart_items:
                        if item['type'] == 'menu' and item['id'] == rule.target_id:
                            if item['quantity'] >= rule.min_quantity:
                                rule_matched = True
                                break
                elif rule.rule_type == 'category':
                    # Check if any product/menu from category is in cart
                    session = get_session()
                    try:
                        for item in cart_items:
                            if item['type'] == 'product':
                                product = session.query(Product).filter(Product.id == item['id']).first()
                                if product and product.category_id == rule.target_id:
                                    if item['quantity'] >= rule.min_quantity:
                                        rule_matched = True
                                        break
                    finally:
                        session.close()
            
            if not rule_matched:
                return False, "ไม่ตรงตามเงื่อนไขโปรโมชั่น"
        
        return True, "โปรโมชั่นสามารถใช้งานได้"
    finally:
        session.close()

def calculate_promotion_discount(promotion: Promotion, cart_items: List[Dict], 
                                 cart_total: float) -> float:
    """Calculate discount from promotion"""
    discount = 0.0
    
    if promotion.promotion_type == 'discount':
        if promotion.discount_type == 'percent':
            discount = cart_total * (promotion.discount_value / 100.0)
            if promotion.max_discount:
                discount = min(discount, promotion.max_discount)
        else:  # fixed
            discount = min(promotion.discount_value, cart_total)
    
    elif promotion.promotion_type == 'buy_x_get_y':
        # For buy X get Y, discount is calculated based on free items
        # This is simplified - in real implementation, need to check which items qualify
        if promotion.buy_quantity and promotion.get_quantity:
            # Calculate how many sets of buy X get Y
            total_quantity = sum(item['quantity'] for item in cart_items)
            sets = int(total_quantity / (promotion.buy_quantity + promotion.get_quantity))
            # Discount = value of free items (simplified)
            if cart_items:
                avg_price = cart_total / total_quantity
                discount = sets * promotion.get_quantity * avg_price
    
    # Check minimum purchase
    if cart_total < promotion.min_purchase:
        return 0.0
    
    return discount

def get_applicable_promotions(cart_items: List[Dict], cart_total: float,
                              customer: Optional[Customer] = None,
                              current_time: datetime = None) -> List[Tuple[Promotion, float]]:
    """Get all applicable promotions with their discount amounts
    Returns: List of (promotion, discount_amount) tuples
    """
    if current_time is None:
        current_time = datetime.now()
    
    active_promotions = get_active_promotions(current_time)
    applicable = []
    
    for promotion in active_promotions:
        is_valid, message = check_promotion_conditions(promotion, cart_items, customer, current_time)
        if is_valid:
            discount = calculate_promotion_discount(promotion, cart_items, cart_total)
            if discount > 0:
                applicable.append((promotion, discount))
    
    # Sort by discount amount (highest first)
    applicable.sort(key=lambda x: x[1], reverse=True)
    
    return applicable

def use_promotion(promotion_id: int, sale_id: int, customer_id: int = None, 
                  discount_amount: float = 0.0) -> bool:
    """Record promotion usage"""
    session = get_session()
    try:
        from database.models import PromotionUsage
        usage = PromotionUsage(
            promotion_id=promotion_id,
            sale_id=sale_id,
            customer_id=customer_id,
            discount_amount=discount_amount
        )
        session.add(usage)
        session.commit()
        
        print(f"[DEBUG] Used promotion {promotion_id} in sale {sale_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in use_promotion: {str(e)}")
        return False
    finally:
        session.close()

