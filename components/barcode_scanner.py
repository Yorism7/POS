"""
Barcode Scanner Component using Camera
Auto-detects environment and uses appropriate method:
- Local: Uses pyzbar for automatic barcode scanning
- Streamlit Cloud: Uses camera + manual input (works everywhere!)
"""

import streamlit as st
from PIL import Image
import numpy as np
import os

# Try to import pyzbar (only available on local)
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    pyzbar = None
    PYZBAR_AVAILABLE = False

def is_streamlit_cloud():
    """Check if running on Streamlit Cloud"""
    # Streamlit Cloud sets this environment variable
    return os.environ.get('STREAMLIT_CLOUD', '').lower() == 'true'

def barcode_scanner_component():
    """
    Create a barcode scanner component using camera
    Auto-detects environment and uses best available method
    Returns the scanned barcode value or None
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดด้วยกล้อง")
    
    # Check if we're on Streamlit Cloud
    is_cloud = is_streamlit_cloud()
    
    if is_cloud or not PYZBAR_AVAILABLE:
        # Use Streamlit Cloud compatible method
        st.info("💡 **วิธีใช้งาน:** ถ่ายภาพบาร์โค๊ดแล้วดูตัวเลข/ตัวอักษรจากภาพ แล้วพิมพ์ในช่องด้านล่าง")
        
        # Use camera input
        image = st.camera_input(
            "📷 ถ่ายภาพบาร์โค๊ด",
            key="barcode_camera",
            help="ถ่ายภาพบาร์โค๊ด"
        )
        
        if image is not None:
            # Display the image
            st.image(image, caption="ภาพที่ถ่าย - กรุณาดูบาร์โค๊ดจากภาพ", width='stretch')
            st.info("💡 **ดูบาร์โค๊ดจากภาพด้านบน แล้วพิมพ์ตัวเลข/ตัวอักษรในช่องด้านล่าง**")
            
            # Manual input
            barcode_input = st.text_input(
                "📷 พิมพ์บาร์โค๊ดจากภาพ",
                key="barcode_input_from_image",
                placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                help="ดูบาร์โค๊ดจากภาพแล้วพิมพ์"
            )
            
            if barcode_input:
                st.success(f"✅ รับบาร์โค๊ด: {barcode_input}")
                return barcode_input.strip()
        else:
            # Show manual input option
            st.divider()
            st.subheader("หรือพิมพ์บาร์โค๊ดด้วยตนเอง")
            barcode_input = st.text_input(
                "📷 พิมพ์บาร์โค๊ด",
                key="barcode_manual_camera",
                placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                help="พิมพ์บาร์โค๊ดแล้วกด Enter"
            )
            return barcode_input.strip() if barcode_input else None
    else:
        # Local: Use pyzbar for automatic scanning
        st.info("💡 **วิธีใช้งาน:** กดปุ่มกล้องด้านล่างเพื่อเปิดกล้องและถ่ายภาพบาร์โค๊ด ระบบจะสแกนอัตโนมัติ")
        
        # Check browser support
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <small>⚠️ <strong>หมายเหตุ:</strong> ต้องใช้ HTTPS หรือ localhost และ Browser ที่รองรับ (Chrome, Firefox, Edge)</small>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Use Streamlit's built-in camera input
            image = st.camera_input(
                "📷 กดเพื่อเปิดกล้อง",
                key="barcode_camera",
                help="กดปุ่มนี้เพื่อเปิดกล้องและถ่ายภาพบาร์โค๊ด"
            )
            
            if image is not None:
                # Convert PIL Image to numpy array for pyzbar
                img_array = np.array(image)
                
                # Decode barcode
                barcodes = pyzbar.decode(img_array)
                
                if barcodes:
                    # Get first barcode
                    barcode_data = barcodes[0].data.decode('utf-8')
                    barcode_type = barcodes[0].type
                    
                    st.success(f"✅ พบบาร์โค๊ด: {barcode_data} (ประเภท: {barcode_type})")
                    
                    # Display image with barcode highlighted
                    st.image(image, caption=f"บาร์โค๊ดที่สแกน: {barcode_data}", width='stretch')
                    
                    # Auto-add to search
                    return barcode_data
                else:
                    st.warning("⚠️ ไม่พบบาร์โค๊ดในภาพ กรุณาถ่ายภาพใหม่อีกครั้ง")
                    st.info("💡 หมายเหตุ: ต้องชี้กล้องให้เห็นบาร์โค๊ดชัดเจน")
                    return None
            else:
                # Show manual input option
                st.divider()
                st.subheader("หรือพิมพ์บาร์โค๊ดด้วยตนเอง")
                barcode_input = st.text_input(
                    "📷 พิมพ์บาร์โค๊ด",
                    key="barcode_manual_camera",
                    placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                    help="พิมพ์บาร์โค๊ดแล้วกด Enter"
                )
                return barcode_input.strip() if barcode_input else None
                
        except Exception as e:
            st.warning(f"⚠️ เกิดข้อผิดพลาดในการใช้กล้อง: {str(e)}")
            st.info("💡 กรุณาใช้วิธีพิมพ์บาร์โค๊ดแทน")
            
            # Fallback to manual input
            barcode_input = st.text_input(
                "📷 พิมพ์บาร์โค๊ด",
                key="barcode_manual_error",
                placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                help="พิมพ์บาร์โค๊ดแล้วกด Enter"
            )
            return barcode_input.strip() if barcode_input else None
    
    return None
