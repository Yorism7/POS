"""
Helper Functions for POS System
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.db import get_session
from database.models import Product, Menu, Sale, SaleItem, StockTransaction, Category
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

