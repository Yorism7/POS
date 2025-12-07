"""
Reports Page - รายงานต่างๆ
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from database.db import get_session
from database.models import Sale, SaleItem, Product, Menu, Customer, Expense
from utils.expense import get_expense_summary
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from utils.helpers import format_currency, calculate_menu_cost
from utils.tax import get_tax_report, generate_tax_invoice
import io

st.set_page_config(page_title="รายงาน", page_icon="📈", layout="wide")

def get_sales_report(start_date: datetime, end_date: datetime):
    """Get sales report data"""
    session = get_session()
    try:
        sales = session.query(Sale).options(
            joinedload(Sale.creator)
        ).filter(
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
    # Check authentication and redirect to login if not authenticated
    from utils.auth import require_auth
    require_auth()
    
    st.title("📈 รายงาน")
    
    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("วันที่เริ่มต้น", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", value=datetime.now().date())
    with col3:
        report_type = st.selectbox("ประเภทรายงาน", [
            "ยอดขาย", "กำไร-ขาดทุน", "สินค้าขายดี", "สรุปภาพรวม",
            "รายงานรายชั่วโมง", "เปรียบเทียบ", "พฤติกรรมลูกค้า", 
            "กำไร-ขาดทุน (รวมค่าใช้จ่าย)", "รายงานภาษี"
        ])
    
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
                st.plotly_chart(fig, width='stretch')
                
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
            st.dataframe(df_sales, width='stretch', hide_index=True)
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
                st.plotly_chart(fig, width='stretch')
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
            
            st.dataframe(df_products, width='stretch', hide_index=True)
            
            # Chart
            fig = px.bar(
                df_products.head(10),
                x='ชื่อสินค้า',
                y='จำนวนที่ขาย',
                title="สินค้าขายดี 10 อันดับ"
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, width='stretch')
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
            
            st.dataframe(df_menus, width='stretch', hide_index=True)
            
            # Chart
            fig = px.bar(
                df_menus.head(10),
                x='ชื่อเมนู',
                y='จำนวนที่ขาย',
                title="เมนูขายดี 10 อันดับ"
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, width='stretch')
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
    
    elif report_type == "รายงานรายชั่วโมง":
        st.subheader("⏰ รายงานรายชั่วโมง (Peak Hours Analysis)")
        
        session = get_session()
        try:
            hourly_sales = session.query(
                func.strftime('%H', Sale.sale_date).label('hour'),
                func.sum(Sale.final_amount).label('total'),
                func.count(Sale.id).label('count')
            ).filter(
                Sale.sale_date >= start_datetime,
                Sale.sale_date <= end_datetime,
                Sale.is_void == False
            ).group_by(
                func.strftime('%H', Sale.sale_date)
            ).order_by(
                func.strftime('%H', Sale.sale_date).asc()
            ).all()
            
            if hourly_sales:
                df_hourly = pd.DataFrame([
                    {'ชั่วโมง': f"{int(h.hour):02d}:00", 'ยอดขาย': h.total or 0.0, 'จำนวน': h.count or 0}
                    for h in hourly_sales
                ])
                
                # Chart
                fig = px.bar(
                    df_hourly,
                    x='ชั่วโมง',
                    y='ยอดขาย',
                    labels={'ชั่วโมง': 'เวลา', 'ยอดขาย': 'ยอดขาย (฿)'},
                    title="ยอดขายรายชั่วโมง"
                )
                fig.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig, width='stretch')
                
                # Table
                df_hourly['ยอดขาย'] = df_hourly['ยอดขาย'].apply(lambda x: format_currency(x))
                st.dataframe(df_hourly, width='stretch', hide_index=True)
                
                # Peak hours
                peak_hour = df_hourly.loc[df_hourly['ยอดขาย'].str.replace('฿', '').str.replace(',', '').astype(float).idxmax()]
                st.metric("⏰ ชั่วโมงที่ขายดีที่สุด", peak_hour['ชั่วโมง'])
            else:
                st.info("ไม่มีข้อมูลยอดขาย")
        finally:
            session.close()
    
    elif report_type == "เปรียบเทียบ":
        st.subheader("📊 รายงานเปรียบเทียบ")
        
        compare_type = st.radio("เปรียบเทียบ", ["วัน", "เดือน", "ปี"], horizontal=True, key="compare_type")
        
        session = get_session()
        try:
            if compare_type == "วัน":
                # Compare last 7 days
                days_data = []
                for i in range(7):
                    day = (datetime.now() - timedelta(days=i)).date()
                    day_start = datetime.combine(day, datetime.min.time())
                    day_end = datetime.combine(day, datetime.max.time())
                    day_report = get_sales_report(day_start, day_end)
                    days_data.append({
                        'วันที่': day.strftime('%d/%m/%Y'),
                        'ยอดขาย': day_report['total_sales'],
                        'กำไร': day_report['total_profit']
                    })
                
                df_compare = pd.DataFrame(days_data)
                df_compare = df_compare.sort_values('วันที่')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_compare['วันที่'],
                    y=df_compare['ยอดขาย'],
                    name='ยอดขาย',
                    line=dict(color='blue')
                ))
                fig.add_trace(go.Scatter(
                    x=df_compare['วันที่'],
                    y=df_compare['กำไร'],
                    name='กำไร',
                    line=dict(color='green')
                ))
                fig.update_layout(title="เปรียบเทียบยอดขาย 7 วันล่าสุด", height=400, hovermode='x unified')
                st.plotly_chart(fig, width='stretch')
                
                df_compare['ยอดขาย'] = df_compare['ยอดขาย'].apply(lambda x: format_currency(x))
                df_compare['กำไร'] = df_compare['กำไร'].apply(lambda x: format_currency(x))
                st.dataframe(df_compare, width='stretch', hide_index=True)
            
            elif compare_type == "เดือน":
                # Compare last 6 months
                months_data = []
                for i in range(6):
                    month_date = datetime.now() - timedelta(days=30*i)
                    month_start = datetime(month_date.year, month_date.month, 1)
                    if month_date.month == 12:
                        month_end = datetime(month_date.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        month_end = datetime(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
                    
                    month_report = get_sales_report(month_start, month_end)
                    months_data.append({
                        'เดือน': month_start.strftime('%m/%Y'),
                        'ยอดขาย': month_report['total_sales'],
                        'กำไร': month_report['total_profit']
                    })
                
                df_compare = pd.DataFrame(months_data)
                df_compare = df_compare.sort_values('เดือน')
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_compare['เดือน'], y=df_compare['ยอดขาย'], name='ยอดขาย'))
                fig.add_trace(go.Bar(x=df_compare['เดือน'], y=df_compare['กำไร'], name='กำไร'))
                fig.update_layout(title="เปรียบเทียบยอดขาย 6 เดือนล่าสุด", height=400, barmode='group')
                st.plotly_chart(fig, width='stretch')
                
                df_compare['ยอดขาย'] = df_compare['ยอดขาย'].apply(lambda x: format_currency(x))
                df_compare['กำไร'] = df_compare['กำไร'].apply(lambda x: format_currency(x))
                st.dataframe(df_compare, width='stretch', hide_index=True)
        finally:
            session.close()
    
    elif report_type == "พฤติกรรมลูกค้า":
        st.subheader("👥 รายงานพฤติกรรมลูกค้า")
        
        session = get_session()
        try:
            # Top customers
            top_customers = session.query(
                Customer.id,
                Customer.name,
                Customer.phone,
                func.count(Sale.id).label('visit_count'),
                func.sum(Sale.final_amount).label('total_spent'),
                func.avg(Sale.final_amount).label('avg_spent')
            ).join(
                Sale, Sale.customer_id == Customer.id
            ).filter(
                Sale.sale_date >= start_datetime,
                Sale.sale_date <= end_datetime,
                Sale.is_void == False
            ).group_by(
                Customer.id, Customer.name, Customer.phone
            ).order_by(
                func.sum(Sale.final_amount).desc()
            ).limit(20).all()
            
            if top_customers:
                st.write("**🏆 ลูกค้าที่ซื้อมากที่สุด**")
                customer_data = []
                for cust in top_customers:
                    customer_data.append({
                        'ชื่อ': cust.name,
                        'เบอร์โทร': cust.phone or '-',
                        'จำนวนครั้ง': cust.visit_count or 0,
                        'ยอดซื้อรวม': format_currency(cust.total_spent or 0.0),
                        'ยอดซื้อเฉลี่ย': format_currency(cust.avg_spent or 0.0)
                    })
                
                df_customers = pd.DataFrame(customer_data)
                st.dataframe(df_customers, width='stretch', hide_index=True)
                
                # Chart
                fig = px.bar(
                    df_customers.head(10),
                    x='ชื่อ',
                    y='ยอดซื้อรวม',
                    title="ลูกค้าที่ซื้อมากที่สุด 10 อันดับ"
                )
                fig.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("ไม่มีข้อมูลลูกค้า")
        finally:
            session.close()
    
    elif report_type == "กำไร-ขาดทุน (รวมค่าใช้จ่าย)":
        st.subheader("💵 รายงานกำไร-ขาดทุน (รวมค่าใช้จ่าย)")
        
        report_data = get_sales_report(start_datetime, end_datetime)
        expense_summary = get_expense_summary(start_datetime, end_datetime)
        
        # Calculate net profit
        total_expenses = expense_summary['total']
        net_profit = report_data['total_profit'] - total_expenses
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ยอดขายรวม", format_currency(report_data['total_sales']))
        with col2:
            st.metric("กำไรขั้นต้น", format_currency(report_data['total_profit']))
        with col3:
            st.metric("ค่าใช้จ่ายรวม", format_currency(total_expenses))
        with col4:
            st.metric("กำไรสุทธิ", format_currency(net_profit), 
                     delta=f"{(net_profit/report_data['total_sales']*100) if report_data['total_sales'] > 0 else 0:.2f}%")
        
        # Chart
        st.divider()
        fig = go.Figure()
        fig.add_trace(go.Bar(name='ยอดขาย', x=['สรุป'], y=[report_data['total_sales']]))
        fig.add_trace(go.Bar(name='กำไรขั้นต้น', x=['สรุป'], y=[report_data['total_profit']]))
        fig.add_trace(go.Bar(name='ค่าใช้จ่าย', x=['สรุป'], y=[total_expenses]))
        fig.add_trace(go.Bar(name='กำไรสุทธิ', x=['สรุป'], y=[net_profit]))
        fig.update_layout(title="สรุปกำไร-ขาดทุน", height=400, barmode='group')
        st.plotly_chart(fig, width='stretch')
        
        # Expenses by category
        if expense_summary['by_category']:
            st.divider()
            st.write("**💰 ค่าใช้จ่ายตามหมวดหมู่**")
            df_expense = pd.DataFrame(expense_summary['by_category'])
            df_expense['total'] = df_expense['total'].apply(lambda x: format_currency(x))
            df_expense.columns = ['ID', 'หมวดหมู่', 'จำนวนเงิน']
            st.dataframe(df_expense[['หมวดหมู่', 'จำนวนเงิน']], width='stretch', hide_index=True)
    
    elif report_type == "รายงานภาษี":
        st.subheader("📋 รายงานภาษีมูลค่าเพิ่ม")
        
        tax_report = get_tax_report(start_datetime, end_datetime)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ยอดขายรวม", format_currency(tax_report['total_sales']))
        with col2:
            st.metric("ยอดก่อนภาษี", format_currency(tax_report['total_subtotal']))
        with col3:
            st.metric("ภาษีรวม", format_currency(tax_report['total_tax']))
        with col4:
            st.metric("จำนวนใบกำกับ", f"{tax_report['sales_count']:,} ใบ")
        
        # Tax by rate
        if tax_report['by_rate']:
            st.divider()
            st.write("**📊 ภาษีตามอัตรา**")
            tax_data = []
            for rate, data in tax_report['by_rate'].items():
                tax_data.append({
                    'อัตราภาษี': f"{rate}%",
                    'ยอดก่อนภาษี': format_currency(data['subtotal']),
                    'ภาษี': format_currency(data['tax']),
                    'รวม': format_currency(data['total']),
                    'จำนวน': data['count']
                })
            
            df_tax = pd.DataFrame(tax_data)
            st.dataframe(df_tax, width='stretch', hide_index=True)
        
        # Generate tax invoice for specific sale
        st.divider()
        st.write("**🧾 สร้างใบกำกับภาษี**")
        sale_id_input = st.number_input("เลขที่การขาย", min_value=1, step=1, key="tax_invoice_sale_id")
        
        if st.button("📄 สร้างใบกำกับภาษี", key="generate_tax_invoice_btn"):
            invoice_text = generate_tax_invoice(int(sale_id_input))
            st.code(invoice_text, language=None)
            
            st.download_button(
                "📥 ดาวน์โหลดใบกำกับภาษี",
                invoice_text,
                file_name=f"tax_invoice_{sale_id_input:06d}.txt",
                mime="text/plain",
                width='stretch'
            )

if __name__ == "__main__":
    main()

