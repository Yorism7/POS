"""
Expense Management Functions
จัดการค่าใช้จ่าย
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.db import get_session
from database.models import Expense, ExpenseCategory
from sqlalchemy import func
from utils.helpers import format_currency

def get_expenses_by_date_range(start_date: datetime, end_date: datetime, category_id: int = None) -> List[Expense]:
    """Get expenses by date range"""
    session = get_session()
    try:
        query = session.query(Expense).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
        
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        
        return query.order_by(Expense.expense_date.desc()).all()
    finally:
        session.close()

def get_expense_summary(start_date: datetime, end_date: datetime) -> Dict:
    """Get expense summary by category"""
    session = get_session()
    try:
        # Total expenses
        total = session.query(func.sum(Expense.amount)).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).scalar() or 0.0
        
        # Expenses by category
        category_expenses = session.query(
            ExpenseCategory.id,
            ExpenseCategory.name,
            func.sum(Expense.amount).label('total')
        ).join(
            Expense, Expense.category_id == ExpenseCategory.id
        ).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).group_by(
            ExpenseCategory.id, ExpenseCategory.name
        ).all()
        
        return {
            'total': total,
            'by_category': [
                {'id': c.id, 'name': c.name, 'total': c.total or 0.0}
                for c in category_expenses
            ]
        }
    finally:
        session.close()

def get_daily_expenses(start_date: datetime, end_date: datetime) -> List[Dict]:
    """Get daily expenses"""
    session = get_session()
    try:
        results = session.query(
            func.date(Expense.expense_date).label('date'),
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        ).group_by(
            func.date(Expense.expense_date)
        ).order_by(
            func.date(Expense.expense_date).asc()
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

def create_expense_category(name: str, description: str = None) -> Optional[ExpenseCategory]:
    """Create expense category"""
    session = get_session()
    try:
        # Check if exists
        existing = session.query(ExpenseCategory).filter(ExpenseCategory.name == name).first()
        if existing:
            return existing
        
        category = ExpenseCategory(
            name=name,
            description=description,
            is_active=True
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return category
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in create_expense_category: {str(e)}")
        return None
    finally:
        session.close()

def get_all_expense_categories() -> List[ExpenseCategory]:
    """Get all expense categories"""
    session = get_session()
    try:
        return session.query(ExpenseCategory).filter(
            ExpenseCategory.is_active == True
        ).order_by(ExpenseCategory.name).all()
    finally:
        session.close()



