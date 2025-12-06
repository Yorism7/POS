"""
Reports Page - รายงานต่างๆ
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from database.db import get_session
from database.models import Sale, SaleItem, Product, Menu
from sqlalchemy import func
from utils.helpers import format_currency, calculate_menu_cost
import io

st.set_page_config(page_title="รายงาน", page_icon="📈", layout="wide")

def get_sales_report(start_date: datetime, end_date: datetime):
    """Get sales report data"""
    session = get_session()
    try:
        sales = session.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_void == False
        ).all()
        
        total_sales = sum(s.final_amount for s in sales)
        total_count = len(sales)
        
        # Calculate profit
        total_profit = 0.0
        for sale in sales:
            for item in sale.sale_items:
                if item.item_type == 'product':
                    if item.product:
                        cost = item.product.cost_price
                        # Profit after discount
                        item_profit = (item.unit_price - cost) * item.quantity - (item.discount_amount or 0)
                        total_profit += item_profit
                elif item.item_type == 'menu':
                    menu_cost = calculate_menu_cost(item.menu_id)
                    # Profit after discount
                    item_profit = (item.unit_price - menu_cost) * item.quantity - (item.discount_amount or 0)
                    total_profit += item_profit
        
        return {
            'total_sales': total_sales,
            'total_count': total_count,
            'total_profit': total_profit,
            'sales': sales
        }
    finally:
        session.close()

def get_top_selling_items(start_date: datetime, end_date: datetime, limit: int = 10):
    """Get top selling items"""
    session = get_session()
    try:
        # Products
        product_sales = session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('total_quantity'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(
            SaleItem, SaleItem.product_id == Product.id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            SaleItem.item_type == 'product'
        ).group_by(
            Product.id, Product.name
        ).order_by(
            func.sum(SaleItem.quantity).desc()
        ).limit(limit).all()
        
        # Menus
        menu_sales = session.query(
            Menu.id,
            Menu.name,
            func.sum(SaleItem.quantity).label('total_quantity'),
            func.sum(SaleItem.total_price).label('total_revenue')
        ).join(
            SaleItem, SaleItem.menu_id == Menu.id
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            SaleItem.item_type == 'menu'
        ).group_by(
            Menu.id, Menu.name
        ).order_by(
            func.sum(SaleItem.quantity).desc()
        ).limit(limit).all()
        
        return {
            'products': [
                {'id': p.id, 'name': p.name, 'quantity': p.total_quantity or 0, 'revenue': p.total_revenue or 0.0, 'type': 'product'}
                for p in product_sales
            ],
            'menus': [
                {'id': m.id, 'name': m.name, 'quantity': m.total_quantity or 0, 'revenue': m.total_revenue or 0.0, 'type': 'menu'}
                for m in menu_sales
            ]
        }
    finally:
        session.close()

def export_to_excel(df: pd.DataFrame, filename: str):
    """Export DataFrame to Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='รายงาน')
    return output.getvalue()

def main():
    st.title("📈 รายงาน")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date())
    with col3:
        report_type = st.selectbox("ประเภทรายงาน", ["ยอดขาย", "กำไร-ขาดทุน", "สินค้าขายดี", "สรุปภาพรวม"])
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    if report_type == "ยอดขาย":
        st.subheader("📊 รายงานยอดขาย")
        
        report_data = get_sales_report(start_datetime, end_datetime)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ยอดขายรวม", format_currency(report_data['total_sales']))
        with col2:
            st.metric("จำนวนการขาย", f"{report_data['total_count']:,} ครั้ง")
        with col3:
            avg_sale = report_data['total_sales'] / report_data['total_count'] if report_data['total_count'] > 0 else 0
            st.metric("ยอดขายเฉลี่ย", format_currency(avg_sale))
        
        # Daily sales chart
        st.divider()
        st.write("**กราฟยอดขายรายวัน**")
        
        session = get_session()
        try:
            daily_sales = session.query(
                func.date(Sale.sale_date).label('date'),
                func.sum(Sale.final_amount).label('total'),
                func.count(Sale.id).label('count')
            ).filter(
                Sale.sale_date >= start_datetime,
                Sale.sale_date <= end_datetime,
                Sale.is_void == False
            ).group_by(
                func.date(Sale.sale_date)
            ).order_by(
                func.date(Sale.sale_date).asc()
            ).all()
            
            if daily_sales:
                df_daily = pd.DataFrame([
                    {'date': d.date, 'ยอดขาย': d.total or 0.0, 'จำนวน': d.count or 0}
                    for d in daily_sales
                ])
                df_daily['date'] = pd.to_datetime(df_daily['date'])
                
                fig = px.line(
                    df_daily,
                    x='date',
                    y='ยอดขาย',
                    labels={'date': 'วันที่', 'ยอดขาย': 'ยอดขาย (฿)'},
                    title="ยอดขายรายวัน"
                )
                fig.update_layout(height=400, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
                
                # Export button
                if st.button("📥 Export เป็น Excel"):
                    excel_data = export_to_excel(df_daily, f"sales_report_{start_date}_{end_date}.xlsx")
                    st.download_button(
                        "ดาวน์โหลด",
                        excel_data,
                        file_name=f"sales_report_{start_date}_{end_date}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.info("ไม่มีข้อมูลยอดขายในช่วงเวลานี้")
        finally:
            session.close()
        
        # Sales table
        st.divider()
        st.write("**รายละเอียดการขาย**")
        
        if report_data['sales']:
            sales_data = []
            for sale in report_data['sales']:
                payment_text = "💰 เงินสด" if sale.payment_method == 'cash' else "💳 โอนเงิน"
                sales_data.append({
                    'เลขที่': f"#{sale.id:06d}",
                    'วันที่': sale.sale_date.strftime("%d/%m/%Y %H:%M"),
                    'ยอดรวม': format_currency(sale.final_amount),
                    'วิธีชำระ': payment_text,
                    'ผู้ขาย': sale.creator.username if sale.creator else '-'
                })
            
            df_sales = pd.DataFrame(sales_data)
            st.dataframe(df_sales, use_container_width=True, hide_index=True)
        else:
            st.info("ไม่มีข้อมูลการขาย")
    
    elif report_type == "กำไร-ขาดทุน":
        st.subheader("💵 รายงานกำไร-ขาดทุน")
        
        report_data = get_sales_report(start_datetime, end_datetime)
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ยอดขายรวม", format_currency(report_data['total_sales']))
        with col2:
            st.metric("กำไรรวม", format_currency(report_data['total_profit']))
        with col3:
            profit_margin = (report_data['total_profit'] / report_data['total_sales'] * 100) if report_data['total_sales'] > 0 else 0
            st.metric("อัตรากำไร", f"{profit_margin:.2f}%")
        
        # Profit chart
        st.divider()
        st.write("**กราฟกำไรรายวัน**")
        
        session = get_session()
        try:
            daily_profit = []
            daily_sales = session.query(
                func.date(Sale.sale_date).label('date')
            ).filter(
                Sale.sale_date >= start_datetime,
                Sale.sale_date <= end_datetime,
                Sale.is_void == False
            ).group_by(
                func.date(Sale.sale_date)
            ).all()
            
            for day in daily_sales:
                day_start = datetime.combine(day.date, datetime.min.time())
                day_end = datetime.combine(day.date, datetime.max.time())
                day_report = get_sales_report(day_start, day_end)
                daily_profit.append({
                    'date': day.date,
                    'ยอดขาย': day_report['total_sales'],
                    'กำไร': day_report['total_profit']
                })
            
            if daily_profit:
                df_profit = pd.DataFrame(daily_profit)
                df_profit['date'] = pd.to_datetime(df_profit['date'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_profit['date'],
                    y=df_profit['ยอดขาย'],
                    name='ยอดขาย',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=df_profit['date'],
                    y=df_profit['กำไร'],
                    name='กำไร',
                    line=dict(color='green')
                ))
                fig.update_layout(
                    title="ยอดขายและกำไรรายวัน",
                    xaxis_title="วันที่",
                    yaxis_title="จำนวนเงิน (฿)",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลกำไร")
        finally:
            session.close()
    
    elif report_type == "สินค้าขายดี":
        st.subheader("🏆 สินค้าขายดี")
        
        top_items = get_top_selling_items(start_datetime, end_datetime, limit=20)
        
        # Products
        st.write("**📦 สินค้าขายดี**")
        if top_items['products']:
            df_products = pd.DataFrame(top_items['products'])
            df_products['ลำดับ'] = range(1, len(df_products) + 1)
            df_products = df_products[['ลำดับ', 'name', 'quantity', 'revenue']]
            df_products.columns = ['ลำดับ', 'ชื่อสินค้า', 'จำนวนที่ขาย', 'ยอดขาย']
            df_products['ยอดขาย'] = df_products['ยอดขาย'].apply(lambda x: format_currency(x))
            
            st.dataframe(df_products, use_container_width=True, hide_index=True)
            
            # Chart
            fig = px.bar(
                df_products.head(10),
                x='ชื่อสินค้า',
                y='จำนวนที่ขาย',
                title="สินค้าขายดี 10 อันดับ"
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลสินค้าขายดี")
        
        st.divider()
        
        # Menus
        st.write("**🍜 เมนูขายดี**")
        if top_items['menus']:
            df_menus = pd.DataFrame(top_items['menus'])
            df_menus['ลำดับ'] = range(1, len(df_menus) + 1)
            df_menus = df_menus[['ลำดับ', 'name', 'quantity', 'revenue']]
            df_menus.columns = ['ลำดับ', 'ชื่อเมนู', 'จำนวนที่ขาย', 'ยอดขาย']
            df_menus['ยอดขาย'] = df_menus['revenue'].apply(lambda x: format_currency(x))
            
            st.dataframe(df_menus, use_container_width=True, hide_index=True)
            
            # Chart
            fig = px.bar(
                df_menus.head(10),
                x='ชื่อเมนู',
                y='จำนวนที่ขาย',
                title="เมนูขายดี 10 อันดับ"
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลเมนูขายดี")
    
    elif report_type == "สรุปภาพรวม":
        st.subheader("📊 สรุปภาพรวม")
        
        report_data = get_sales_report(start_datetime, end_datetime)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ยอดขายรวม", format_currency(report_data['total_sales']))
        with col2:
            st.metric("กำไรรวม", format_currency(report_data['total_profit']))
        with col3:
            st.metric("จำนวนการขาย", f"{report_data['total_count']:,} ครั้ง")
        with col4:
            profit_margin = (report_data['total_profit'] / report_data['total_sales'] * 100) if report_data['total_sales'] > 0 else 0
            st.metric("อัตรากำไร", f"{profit_margin:.2f}%")
        
        # Top items
        st.divider()
        top_items = get_top_selling_items(start_datetime, end_datetime, limit=5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**📦 สินค้าขายดี 5 อันดับ**")
            if top_items['products']:
                for idx, item in enumerate(top_items['products'][:5], 1):
                    st.write(f"{idx}. {item['name']} - {item['quantity']:.2f} หน่วย")
            else:
                st.info("ไม่มีข้อมูล")
        
        with col2:
            st.write("**🍜 เมนูขายดี 5 อันดับ**")
            if top_items['menus']:
                for idx, item in enumerate(top_items['menus'][:5], 1):
                    st.write(f"{idx}. {item['name']} - {item['quantity']:.0f} จาน")
            else:
                st.info("ไม่มีข้อมูล")

if __name__ == "__main__":
    main()

