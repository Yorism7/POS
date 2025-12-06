"""
Dashboard Page - ภาพรวมระบบ
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from database.db import get_session
from database.models import Sale, Product, Menu
from sqlalchemy import func
from utils.helpers import (
    get_today_sales, get_month_sales, get_today_profit,
    get_low_stock_products, get_top_selling_menus,
    get_sales_by_date, format_currency
)
from utils.notifications import get_all_notifications, Notification
from functools import lru_cache
import time

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

def main():
    st.title("📊 Dashboard - ภาพรวมระบบ")
    
    # Check authentication
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ กรุณาเข้าสู่ระบบก่อน")
        return
    
    # Notifications
    notifications = get_all_notifications()
    if notifications:
        st.subheader("🔔 การแจ้งเตือน")
        for notif in notifications:
            if notif.severity == 'error':
                st.error(f"**{notif.title}** - {notif.message}")
            elif notif.severity == 'warning':
                st.warning(f"**{notif.title}** - {notif.message}")
            elif notif.severity == 'success':
                st.success(f"**{notif.title}** - {notif.message}")
            else:
                st.info(f"**{notif.title}** - {notif.message}")
        st.divider()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        today_sales = get_today_sales()
        st.metric("💰 ยอดขายวันนี้", format_currency(today_sales))
    
    with col2:
        month_sales = get_month_sales()
        st.metric("📅 ยอดขายเดือนนี้", format_currency(month_sales))
    
    with col3:
        today_profit = get_today_profit()
        st.metric("💵 กำไรวันนี้", format_currency(today_profit))
    
    with col4:
        session = get_session()
        try:
            total_products = session.query(Product).count()
            st.metric("📦 จำนวนสินค้า", f"{total_products:,} รายการ")
        finally:
            session.close()
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 กราฟยอดขาย 30 วันล่าสุด")
        sales_data = get_sales_by_date(days=30)
        if sales_data:
            df_sales = pd.DataFrame(sales_data)
            df_sales['date'] = pd.to_datetime(df_sales['date'])
            fig = px.line(
                df_sales,
                x='date',
                y='total',
                labels={'date': 'วันที่', 'total': 'ยอดขาย (฿)'},
                title="ยอดขายรายวัน"
            )
            fig.update_layout(
                height=400,
                xaxis_title="วันที่",
                yaxis_title="ยอดขาย (฿)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลยอดขาย")
    
    with col2:
        st.subheader("🍜 เมนูขายดี 10 อันดับ")
        top_menus = get_top_selling_menus(limit=10, days=30)
        if top_menus:
            df_menus = pd.DataFrame(top_menus)
            fig = px.bar(
                df_menus,
                x='name',
                y='quantity',
                labels={'name': 'เมนู', 'quantity': 'จำนวนที่ขาย'},
                title="เมนูขายดี"
            )
            fig.update_layout(
                height=400,
                xaxis_title="เมนู",
                yaxis_title="จำนวนที่ขาย",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลเมนูขายดี")
    
    st.divider()
    
    # Low stock alert
    st.subheader("⚠️ สินค้าใกล้หมดสต็อค")
    low_stock_products = get_low_stock_products(limit=20)
    
    if low_stock_products:
        # Create DataFrame
        low_stock_data = []
        for product in low_stock_products:
            low_stock_data.append({
                'ชื่อสินค้า': product.name,
                'สต็อคคงเหลือ': f"{product.stock_quantity:.2f} {product.unit}",
                'ขั้นต่ำ': f"{product.min_stock:.2f} {product.unit}",
                'สถานะ': '⚠️ ใกล้หมด' if product.stock_quantity <= product.min_stock else '🟡 ต่ำ'
            })
        
        df_low_stock = pd.DataFrame(low_stock_data)
        st.dataframe(
            df_low_stock,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ ไม่มีสินค้าใกล้หมดสต็อค")
    
    st.divider()
    
    # Recent sales
    st.subheader("🛒 การขายล่าสุด")
    session = get_session()
    try:
        recent_sales = session.query(Sale).order_by(
            Sale.created_at.desc()
        ).limit(10).all()
        
        if recent_sales:
            sales_data = []
            for sale in recent_sales:
                payment_text = "💰 เงินสด" if sale.payment_method == 'cash' else "💳 โอนเงิน"
                sales_data.append({
                    'เลขที่': f"#{sale.id:06d}",
                    'วันที่': sale.sale_date.strftime("%d/%m/%Y %H:%M"),
                    'ยอดรวม': format_currency(sale.final_amount),
                    'วิธีชำระ': payment_text,
                    'ผู้ขาย': sale.creator.username if sale.creator else '-'
                })
            
            df_recent = pd.DataFrame(sales_data)
            st.dataframe(
                df_recent,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ยังไม่มีข้อมูลการขาย")
    finally:
        session.close()
    
    # Summary statistics
    st.divider()
    st.subheader("📊 สรุปสถิติ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        session = get_session()
        try:
            total_sales_count = session.query(Sale).count()
            st.metric("จำนวนการขายทั้งหมด", f"{total_sales_count:,} ครั้ง")
        finally:
            session.close()
    
    with col2:
        session = get_session()
        try:
            active_menus = session.query(Menu).filter(Menu.is_active == True).count()
            st.metric("เมนูที่เปิดขาย", f"{active_menus:,} เมนู")
        finally:
            session.close()
    
    with col3:
        session = get_session()
        try:
            total_stock_value = session.query(
                func.sum(Product.stock_quantity * Product.cost_price)
            ).scalar() or 0.0
            st.metric("มูลค่าสต็อคทั้งหมด", format_currency(total_stock_value))
        except:
            st.metric("มูลค่าสต็อคทั้งหมด", format_currency(0.0))
        finally:
            session.close()

if __name__ == "__main__":
    main()

