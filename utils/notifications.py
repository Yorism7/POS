"""
Notification System
ระบบแจ้งเตือน
"""

from datetime import datetime, timedelta
from typing import List, Dict
from database.db import get_session
from database.models import Product, Sale, Expense
from sqlalchemy import func
from utils.helpers import format_currency, get_today_sales

class Notification:
    """Notification class"""
    def __init__(self, type: str, title: str, message: str, severity: str = "info"):
        self.type = type  # 'stock', 'sales', 'payment', 'expense'
        self.title = title
        self.message = message
        self.severity = severity  # 'info', 'warning', 'error', 'success'
        self.timestamp = datetime.now()

def get_stock_notifications() -> List[Notification]:
    """Get stock-related notifications"""
    notifications = []
    session = get_session()
    try:
        # Low stock products
        low_stock_products = session.query(Product).filter(
            Product.stock_quantity <= Product.min_stock,
            Product.stock_quantity > 0
        ).all()
        
        if low_stock_products:
            count = len(low_stock_products)
            notifications.append(Notification(
                type='stock',
                title='⚠️ สินค้าใกล้หมดสต็อค',
                message=f'มีสินค้า {count} รายการที่ใกล้หมดสต็อค',
                severity='warning'
            ))
        
        # Out of stock products
        out_of_stock = session.query(Product).filter(
            Product.stock_quantity <= 0
        ).count()
        
        if out_of_stock > 0:
            notifications.append(Notification(
                type='stock',
                title='❌ สินค้าหมดสต็อค',
                message=f'มีสินค้า {out_of_stock} รายการที่หมดสต็อค',
                severity='error'
            ))
    finally:
        session.close()
    
    return notifications

def get_sales_notifications(sales_target: float = None) -> List[Notification]:
    """Get sales-related notifications"""
    notifications = []
    
    today_sales = get_today_sales()
    
    # Sales target notification
    if sales_target and sales_target > 0:
        progress = (today_sales / sales_target) * 100
        if progress >= 100:
            notifications.append(Notification(
                type='sales',
                title='🎉 บรรลุเป้าหมายยอดขาย',
                message=f'ยอดขายวันนี้: {format_currency(today_sales)} (เป้าหมาย: {format_currency(sales_target)})',
                severity='success'
            ))
        elif progress >= 80:
            notifications.append(Notification(
                type='sales',
                title='📈 ใกล้เป้าหมายยอดขาย',
                message=f'ยอดขายวันนี้: {format_currency(today_sales)} ({progress:.1f}% ของเป้าหมาย)',
                severity='info'
            ))
    
    return notifications

def get_expense_notifications() -> List[Notification]:
    """Get expense-related notifications"""
    notifications = []
    session = get_session()
    try:
        # Today's expenses
        today = datetime.now().date()
        today_expenses = session.query(func.sum(Expense.amount)).filter(
            func.date(Expense.expense_date) == today
        ).scalar() or 0.0
        
        # Average daily expenses (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        # First get daily totals, then calculate average
        daily_totals = session.query(
            func.sum(Expense.amount).label('daily_total')
        ).filter(
            Expense.expense_date >= thirty_days_ago
        ).group_by(
            func.date(Expense.expense_date)
        ).all()
        
        # Calculate average of daily totals
        if daily_totals:
            total_sum = sum(row.daily_total or 0.0 for row in daily_totals)
            avg_expenses = total_sum / len(daily_totals) if len(daily_totals) > 0 else 0.0
        else:
            avg_expenses = 0.0
        
        if avg_expenses > 0 and today_expenses > avg_expenses * 1.5:
            notifications.append(Notification(
                type='expense',
                title='⚠️ ค่าใช้จ่ายสูงผิดปกติ',
                message=f'ค่าใช้จ่ายวันนี้: {format_currency(today_expenses)} (สูงกว่าค่าเฉลี่ย {((today_expenses/avg_expenses-1)*100):.1f}%)',
                severity='warning'
            ))
    finally:
        session.close()
    
    return notifications

def get_all_notifications(sales_target: float = None) -> List[Notification]:
    """Get all notifications"""
    notifications = []
    notifications.extend(get_stock_notifications())
    notifications.extend(get_sales_notifications(sales_target))
    notifications.extend(get_expense_notifications())
    return notifications

