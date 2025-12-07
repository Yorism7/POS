"""
Tax Management Functions
จัดการภาษีมูลค่าเพิ่ม (VAT)
"""

from datetime import datetime, timedelta
from typing import List, Dict
from database.db import get_session
from database.models import Sale
from sqlalchemy import func
from utils.helpers import format_currency

def calculate_vat(amount: float, tax_rate: float = 7.0, include_tax: bool = False) -> Dict:
    """Calculate VAT
    Args:
        amount: Amount to calculate tax
        tax_rate: Tax rate in percentage (default 7%)
        include_tax: If True, amount includes tax. If False, amount excludes tax.
    Returns:
        Dict with 'subtotal', 'tax_amount', 'total'
    """
    if include_tax:
        # Amount includes tax
        total = amount
        subtotal = total / (1 + tax_rate / 100.0)
        tax_amount = total - subtotal
    else:
        # Amount excludes tax
        subtotal = amount
        tax_amount = subtotal * (tax_rate / 100.0)
        total = subtotal + tax_amount
    
    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': total,
        'tax_rate': tax_rate
    }

def get_tax_report(start_date: datetime, end_date: datetime) -> Dict:
    """Get tax report"""
    session = get_session()
    try:
        sales = session.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_void == False
        ).all()
        
        total_sales = sum(s.final_amount for s in sales)
        total_tax = sum(s.tax_amount for s in sales)
        total_subtotal = sum(s.subtotal for s in sales if s.subtotal > 0) or total_sales - total_tax
        
        # Group by tax rate
        tax_by_rate = {}
        for sale in sales:
            rate = sale.tax_rate or 0.0
            if rate not in tax_by_rate:
                tax_by_rate[rate] = {'subtotal': 0.0, 'tax': 0.0, 'total': 0.0, 'count': 0}
            tax_by_rate[rate]['subtotal'] += sale.subtotal if sale.subtotal > 0 else sale.final_amount - sale.tax_amount
            tax_by_rate[rate]['tax'] += sale.tax_amount
            tax_by_rate[rate]['total'] += sale.final_amount
            tax_by_rate[rate]['count'] += 1
        
        return {
            'total_sales': total_sales,
            'total_subtotal': total_subtotal,
            'total_tax': total_tax,
            'by_rate': tax_by_rate,
            'sales_count': len(sales)
        }
    finally:
        session.close()

def generate_tax_invoice(sale_id: int) -> str:
    """Generate tax invoice text"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            return "ไม่พบข้อมูลการขาย"
        
        lines = []
        lines.append("=" * 50)
        lines.append("ใบกำกับภาษี / TAX INVOICE")
        lines.append("=" * 50)
        lines.append(f"เลขที่: {sale.id:06d}")
        lines.append(f"วันที่: {sale.sale_date.strftime('%d/%m/%Y %H:%M')}")
        lines.append("-" * 50)
        
        if sale.customer:
            lines.append(f"ลูกค้า: {sale.customer.name}")
            if sale.customer.tax_id:
                lines.append(f"เลขประจำตัวผู้เสียภาษี: {sale.customer.tax_id}")
        
        lines.append("-" * 50)
        lines.append("รายการสินค้า:")
        
        for item in sale.sale_items:
            item_name = item.product.name if item.product else item.menu.name if item.menu else "Unknown"
            lines.append(f"  {item_name} x {item.quantity:.2f} = {format_currency(item.total_price)}")
        
        lines.append("-" * 50)
        if sale.subtotal > 0:
            lines.append(f"ยอดก่อนภาษี: {format_currency(sale.subtotal)}")
            lines.append(f"ภาษีมูลค่าเพิ่ม ({sale.tax_rate}%): {format_currency(sale.tax_amount)}")
        lines.append(f"รวมทั้งสิ้น: {format_currency(sale.final_amount)}")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    finally:
        session.close()



