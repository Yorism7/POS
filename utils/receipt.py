"""
Receipt Printing Functions
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import Optional
from database.db import get_session
from database.models import Sale, SaleItem
from utils.store_settings import get_store_settings, get_receipt_settings
import os

def generate_receipt_pdf(sale_id: int, output_path: Optional[str] = None) -> str:
    """Generate PDF receipt for a sale"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError(f"Sale {sale_id} not found")
        
        # Create output directory if not exists
        receipt_dir = "data/receipts"
        os.makedirs(receipt_dir, exist_ok=True)
        
        if not output_path:
            output_path = os.path.join(receipt_dir, f"receipt_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=(80*mm, 200*mm))
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.alignment = TA_CENTER
        normal_style = styles['Normal']
        normal_style.alignment = TA_LEFT
        
        # Get store and receipt settings
        store_settings = get_store_settings()
        receipt_settings = get_receipt_settings()
        store_name = store_settings.get('store_name', 'ร้านขายของชำและอาหารตามสั่ง')
        
        # Header
        story.append(Paragraph(store_name, title_style))
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph(f"ใบเสร็จรับเงิน", normal_style))
        story.append(Paragraph(f"เลขที่: {sale.id:06d}", normal_style))
        story.append(Paragraph(f"วันที่: {sale.sale_date.strftime('%d/%m/%Y %H:%M')}", normal_style))
        story.append(Spacer(1, 5*mm))
        
        # Items table
        table_data = [['รายการ', 'จำนวน', 'ราคา', 'ส่วนลด', 'รวม']]
        for item in sale.sale_items:
            item_name = ""
            if item.item_type == 'product' and item.product:
                item_name = item.product.name
            elif item.item_type == 'menu' and item.menu:
                item_name = item.menu.name
            
            table_data.append([
                item_name,
                f"{item.quantity:.2f}",
                f"{item.unit_price:.2f}",
                f"{item.discount_amount:.2f}" if item.discount_amount > 0 else "-",
                f"{item.total_price:.2f}"
            ])
        
        # Total rows
        table_data.append(['', '', '', 'รวม', f"{sale.total_amount:.2f}"])
        if sale.discount_amount > 0:
            table_data.append(['', '', '', 'ส่วนลด', f"-{sale.discount_amount:.2f}"])
        
        # Calculate tax if enabled
        subtotal = sale.final_amount
        if receipt_settings.get('receipt_show_tax', False):
            tax_rate = receipt_settings.get('receipt_tax_rate', 7.0) / 100
            tax_amount = subtotal * tax_rate / (1 + tax_rate)
            subtotal_before_tax = subtotal - tax_amount
            table_data.append(['', '', '', 'รวมก่อนภาษี', f"{subtotal_before_tax:.2f}"])
            table_data.append(['', '', '', f'ภาษีมูลค่าเพิ่ม ({receipt_settings.get("receipt_tax_rate", 7.0):.1f}%)', f"{tax_amount:.2f}"])
        
        table_data.append(['', '', '', 'รวมทั้งสิ้น', f"{sale.final_amount:.2f}"])
        
        table = Table(table_data, colWidths=[50*mm, 15*mm, 15*mm, 15*mm, 20*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
            ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 5*mm))
        
        # Payment method
        payment_text = "เงินสด" if sale.payment_method == 'cash' else "โอนเงิน"
        story.append(Paragraph(f"วิธีชำระ: {payment_text}", normal_style))
        story.append(Spacer(1, 5*mm))
        
        # Footer
        receipt_footer = receipt_settings.get('receipt_footer', 'ขอบคุณที่ใช้บริการ')
        story.append(Paragraph(receipt_footer, normal_style))
        story.append(Paragraph("---", normal_style))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    finally:
        session.close()

def generate_receipt_text(sale_id: int) -> str:
    """Generate text receipt for a sale"""
    session = get_session()
    try:
        sale = session.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError(f"Sale {sale_id} not found")
        
        # Get store and receipt settings
        store_settings = get_store_settings()
        receipt_settings = get_receipt_settings()
        store_name = store_settings.get('store_name', 'ร้านขายของชำและอาหารตามสั่ง')
        
        receipt = []
        receipt.append("=" * 40)
        receipt.append(store_name)
        receipt.append("=" * 40)
        receipt.append(f"ใบเสร็จรับเงิน")
        receipt.append(f"เลขที่: {sale.id:06d}")
        receipt.append(f"วันที่: {sale.sale_date.strftime('%d/%m/%Y %H:%M')}")
        receipt.append("-" * 50)
        receipt.append(f"{'รายการ':<20} {'จำนวน':>8} {'ราคา':>10} {'ส่วนลด':>10} {'รวม':>10}")
        receipt.append("-" * 50)
        
        for item in sale.sale_items:
            item_name = ""
            if item.item_type == 'product' and item.product:
                item_name = item.product.name
            elif item.item_type == 'menu' and item.menu:
                item_name = item.menu.name
            
            discount_str = f"{item.discount_amount:>10.2f}" if item.discount_amount > 0 else f"{'-':>10}"
            receipt.append(
                f"{item_name[:18]:<20} {item.quantity:>8.2f} {item.unit_price:>10.2f} {discount_str} {item.total_price:>10.2f}"
            )
        
        receipt.append("-" * 50)
        receipt.append(f"{'รวม':<30} {sale.total_amount:>10.2f}")
        if sale.discount_amount > 0:
            receipt.append(f"{'ส่วนลด':<30} -{sale.discount_amount:>9.2f}")
        
        # Calculate tax if enabled
        subtotal = sale.final_amount
        if receipt_settings.get('receipt_show_tax', False):
            tax_rate = receipt_settings.get('receipt_tax_rate', 7.0) / 100
            tax_amount = subtotal * tax_rate / (1 + tax_rate)
            subtotal_before_tax = subtotal - tax_amount
            receipt.append(f"{'รวมก่อนภาษี':<30} {subtotal_before_tax:>10.2f}")
            receipt.append(f"{'ภาษีมูลค่าเพิ่ม (' + str(receipt_settings.get('receipt_tax_rate', 7.0)) + '%)':<30} {tax_amount:>10.2f}")
        
        receipt.append(f"{'รวมทั้งสิ้น':<30} {sale.final_amount:>10.2f}")
        receipt.append("-" * 50)
        payment_text = "เงินสด" if sale.payment_method == 'cash' else "โอนเงิน"
        receipt.append(f"วิธีชำระ: {payment_text}")
        receipt.append("=" * 40)
        receipt_footer = receipt_settings.get('receipt_footer', 'ขอบคุณที่ใช้บริการ')
        receipt.append(receipt_footer)
        receipt.append("=" * 40)
        
        return "\n".join(receipt)
    finally:
        session.close()

