"""
Barcode Scanner Component for Streamlit Cloud
Uses st.camera_input + manual input (works everywhere!)
"""

import streamlit as st
from PIL import Image
import io
import base64

def barcode_scanner_component():
    """
    Barcode scanner component that works on Streamlit Cloud
    Uses st.camera_input and manual input as fallback
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดด้วยกล้อง")
    
    # Check if we're on Streamlit Cloud or local
    is_cloud = st.secrets.get("is_cloud", False) if hasattr(st, 'secrets') else False
    
    # Use camera input
    image = st.camera_input(
        "📷 ถ่ายภาพบาร์โค๊ด",
        key="barcode_camera_cloud",
        help="ถ่ายภาพบาร์โค๊ดแล้วดูตัวเลข/ตัวอักษรจากภาพ"
    )
    
    if image is not None:
        # Display the image
        st.image(image, caption="ภาพที่ถ่าย - กรุณาดูบาร์โค๊ดจากภาพ", width='stretch')
        
        # Since we can't decode barcode without pyzbar on cloud,
        # we'll help user by showing the image and asking them to type
        st.info("💡 **วิธีใช้งาน:** ดูบาร์โค๊ดจากภาพด้านบน แล้วพิมพ์ตัวเลข/ตัวอักษรในช่องด้านล่าง")
        
        # Get image as base64 for potential future use
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
        
        # Store in session state for potential future processing
        st.session_state['last_barcode_image'] = img_base64
        
        # Manual input
        col1, col2 = st.columns([3, 1])
        with col1:
            barcode_input = st.text_input(
                "📷 พิมพ์บาร์โค๊ดจากภาพ",
                key="barcode_input_from_image",
                placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                help="ดูบาร์โค๊ดจากภาพแล้วพิมพ์"
            )
        with col2:
            if st.button("✅ ยืนยัน", key="confirm_barcode", width='stretch'):
                if barcode_input:
                    return barcode_input.strip()
        
        if barcode_input:
            return barcode_input.strip()
    else:
        # Show manual input option
        st.divider()
        st.subheader("หรือพิมพ์บาร์โค๊ดด้วยตนเอง")
        st.info("💡 คุณสามารถพิมพ์บาร์โค๊ดโดยตรง หรือใช้เครื่องสแกนบาร์โค๊ด (Keyboard Wedge)")
        
        barcode_input = st.text_input(
            "📷 พิมพ์บาร์โค๊ด",
            key="barcode_manual_cloud",
            placeholder="พิมพ์บาร์โค๊ดที่นี่...",
            help="พิมพ์บาร์โค๊ดแล้วกด Enter หรือใช้เครื่องสแกนบาร์โค๊ด"
        )
        
        if barcode_input:
            return barcode_input.strip()
    
    return None

