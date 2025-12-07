"""
Online Order API Endpoints
สำหรับเชื่อมต่อกับแพลตฟอร์มออนไลน์ (LINE MAN, GrabFood, Foodpanda)
"""

from datetime import datetime
from typing import Dict, List, Optional
from database.db import get_session
from database.models import Sale, SaleItem, Product, Menu, Customer
from utils.helpers import format_currency

def create_online_order(order_data: Dict) -> Optional[Dict]:
    """Create order from online platform
    Args:
        order_data: {
            'platform': 'line_man' | 'grabfood' | 'foodpanda',
            'order_id': str,
            'customer_name': str,
            'customer_phone': str,
            'items': [{'type': 'product'|'menu', 'id': int, 'quantity': float, 'price': float}],
            'total': float,
            'payment_method': str
        }
    Returns:
        Dict with sale_id and status
    """
    session = get_session()
    try:
        # Get or create customer
        customer = None
        if order_data.get('customer_phone'):
            customer = session.query(Customer).filter(
                Customer.phone == order_data['customer_phone']
            ).first()
            
            if not customer:
                customer = Customer(
                    name=order_data.get('customer_name', 'ลูกค้าออนไลน์'),
                    phone=order_data['customer_phone'],
                    is_member=False
                )
                session.add(customer)
                session.commit()
                session.refresh(customer)
        
        # Create sale
        sale = Sale(
            sale_date=datetime.now(),
            total_amount=order_data['total'],
            discount_amount=0.0,
            final_amount=order_data['total'],
            payment_method='transfer',  # Online orders usually paid online
            payment_reference=order_data.get('order_id'),
            customer_id=customer.id if customer else None,
            created_by=None  # System order
        )
        session.add(sale)
        session.flush()
        
        # Create sale items
        for item_data in order_data.get('items', []):
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item_data['id'] if item_data['type'] == 'product' else None,
                menu_id=item_data['id'] if item_data['type'] == 'menu' else None,
                item_type=item_data['type'],
                quantity=item_data['quantity'],
                unit_price=item_data['price'],
                discount_amount=0.0,
                total_price=item_data['price'] * item_data['quantity']
            )
            session.add(sale_item)
        
        session.commit()
        
        print(f"[DEBUG] Created online order - Platform: {order_data.get('platform')}, Order ID: {order_data.get('order_id')}, Sale ID: {sale.id}")
        
        return {
            'sale_id': sale.id,
            'status': 'success',
            'message': 'Order created successfully'
        }
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error creating online order: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        session.close()

def get_online_orders(platform: str = None, status: str = None) -> List[Dict]:
    """Get online orders
    Args:
        platform: Filter by platform ('line_man', 'grabfood', 'foodpanda')
        status: Filter by status
    Returns:
        List of order dictionaries
    """
    session = get_session()
    try:
        query = session.query(Sale).filter(
            Sale.payment_reference.isnot(None),
            Sale.is_void == False
        )
        
        # Filter by platform (if payment_reference contains platform identifier)
        if platform:
            # This is simplified - in real implementation, need to store platform info
            pass
        
        sales = query.order_by(Sale.sale_date.desc()).limit(100).all()
        
        orders = []
        for sale in sales:
            orders.append({
                'sale_id': sale.id,
                'order_id': sale.payment_reference,
                'customer': sale.customer.name if sale.customer else 'Unknown',
                'total': sale.final_amount,
                'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            })
        
        return orders
    finally:
        session.close()

def generate_qr_code_for_online_ordering() -> str:
    """Generate QR Code data for online ordering
    Returns:
        QR Code data string
    """
    # In real implementation, this would generate a unique QR code
    # that links to the online ordering page
    return "https://your-pos-system.com/order"



