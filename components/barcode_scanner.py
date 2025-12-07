"""
Barcode Scanner Component using Camera
Uses Streamlit's built-in st.camera_input and pyzbar for barcode scanning
"""

import streamlit as st
from PIL import Image
import numpy as np
try:
    from pyzbar import pyzbar
except ImportError:
    pyzbar = None

def barcode_scanner_component():
    """Create a barcode scanner component using camera
    Returns the scanned barcode value or None
    """
    st.markdown("### 📷 สแกนบาร์โค๊ดด้วยกล้อง")
    st.info("💡 **วิธีใช้งาน:** กดปุ่มกล้องด้านล่างเพื่อเปิดกล้องและถ่ายภาพบาร์โค๊ด")
    
    # Check browser support
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
    <small>⚠️ <strong>หมายเหตุ:</strong> ต้องใช้ HTTPS หรือ localhost และ Browser ที่รองรับ (Chrome, Firefox, Edge)</small>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Use Streamlit's built-in camera input
        # This will show a camera button that opens the camera when clicked
        image = st.camera_input(
            "📷 กดเพื่อเปิดกล้อง",
            key="barcode_camera",
            help="กดปุ่มนี้เพื่อเปิดกล้องและถ่ายภาพบาร์โค๊ด"
        )
        
        if image is not None:
            if pyzbar is None:
                st.error("⚠️ ไม่พบ library pyzbar")
                st.info("💡 กรุณาติดตั้งด้วย: pip install pyzbar")
                # Fallback to manual input
                barcode_input = st.text_input(
                    "📷 พิมพ์บาร์โค๊ด",
                    key="barcode_manual_pyzbar",
                    placeholder="พิมพ์บาร์โค๊ดที่นี่...",
                    help="พิมพ์บาร์โค๊ดแล้วกด Enter"
                )
                return barcode_input if barcode_input else None
                
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
                st.image(image, caption=f"บาร์โค๊ดที่สแกน: {barcode_data}", use_container_width=True)
                
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
            return barcode_input if barcode_input else None
            
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
        return barcode_input if barcode_input else None
