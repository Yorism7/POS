"""
Image Upload Utilities - ฟังก์ชันช่วยเหลือสำหรับการอัพโหลดและจัดการรูปภาพ
"""

import os
import streamlit as st
from PIL import Image
from io import BytesIO
from datetime import datetime
import uuid
import base64

# โฟลเดอร์สำหรับเก็บรูปภาพ
IMAGE_DIR = "data/images"
PRODUCT_IMAGE_DIR = os.path.join(IMAGE_DIR, "products")
MENU_IMAGE_DIR = os.path.join(IMAGE_DIR, "menus")

def ensure_image_directories():
    """สร้างโฟลเดอร์สำหรับเก็บรูปภาพถ้ายังไม่มี"""
    os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)
    os.makedirs(MENU_IMAGE_DIR, exist_ok=True)

def save_uploaded_image(uploaded_file, image_type="product", max_size=(800, 800), quality=85):
    """
    บันทึกรูปภาพที่อัพโหลด
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        image_type: ประเภทรูปภาพ ("product" หรือ "menu")
        max_size: ขนาดสูงสุด (width, height) สำหรับ resize
        quality: คุณภาพ JPEG (1-100)
    
    Returns:
        str: Path ของไฟล์ที่บันทึก หรือ None ถ้าเกิดข้อผิดพลาด
    """
    try:
        ensure_image_directories()
        
        # ตรวจสอบประเภทไฟล์
        if uploaded_file.type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']:
            st.error("❌ รองรับเฉพาะไฟล์รูปภาพ: JPG, PNG, WebP")
            return None
        
        # อ่านรูปภาพ
        image = Image.open(uploaded_file)
        
        # แปลงเป็น RGB ถ้าเป็น RGBA (สำหรับ PNG)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize ถ้าใหญ่เกินไป
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # สร้างชื่อไฟล์
        file_ext = "jpg"  # ใช้ JPG เสมอเพื่อประหยัดพื้นที่
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}.{file_ext}"
        
        # กำหนดโฟลเดอร์ตามประเภท
        if image_type == "product":
            save_dir = PRODUCT_IMAGE_DIR
        elif image_type == "menu":
            save_dir = MENU_IMAGE_DIR
        else:
            save_dir = IMAGE_DIR
        
        # บันทึกไฟล์
        file_path = os.path.join(save_dir, filename)
        image.save(file_path, "JPEG", quality=quality, optimize=True)
        
        print(f"[DEBUG] บันทึกรูปภาพสำเร็จ: {file_path} - {datetime.now()}")
        return file_path
    
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการบันทึกรูปภาพ: {str(e)}")
        print(f"[DEBUG] Error saving image: {e}")
        return None

def delete_image(image_path):
    """
    ลบไฟล์รูปภาพ
    
    Args:
        image_path: Path ของไฟล์รูปภาพ
    
    Returns:
        bool: True ถ้าลบสำเร็จ, False ถ้าเกิดข้อผิดพลาด
    """
    try:
        if image_path and os.path.exists(image_path):
            # ตรวจสอบว่าเป็นไฟล์ในโฟลเดอร์ images เท่านั้น (เพื่อความปลอดภัย)
            if IMAGE_DIR in os.path.abspath(image_path):
                os.remove(image_path)
                print(f"[DEBUG] ลบรูปภาพสำเร็จ: {image_path}")
                return True
        return False
    except Exception as e:
        print(f"[DEBUG] Error deleting image: {e}")
        return False

def get_image_path_for_display(image_path):
    """
    ตรวจสอบและคืนค่า path ที่ใช้แสดงรูปภาพได้
    
    Args:
        image_path: Path หรือ URL ของรูปภาพ
    
    Returns:
        str: Path หรือ URL ที่ใช้แสดงรูปภาพได้, None ถ้าไม่พบ
    """
    if not image_path:
        return None
    
    # ถ้าเป็น URL
    if image_path.startswith(('http://', 'https://')):
        return image_path
    
    # ถ้าเป็น file path
    if os.path.exists(image_path):
        return image_path
    
    return None

def image_uploader_widget(label, key, image_type="product", help_text=None):
    """
    Widget สำหรับอัพโหลดรูปภาพ
    
    Args:
        label: Label ของ widget
        key: Unique key สำหรับ widget
        image_type: ประเภทรูปภาพ ("product" หรือ "menu")
        help_text: ข้อความช่วยเหลือ
    
    Returns:
        str: Path ของไฟล์ที่บันทึก หรือ None
    """
    uploaded_file = st.file_uploader(
        label,
        type=['jpg', 'jpeg', 'png', 'webp'],
        key=key,
        help=help_text or "รองรับไฟล์: JPG, PNG, WebP (ขนาดแนะนำ: ไม่เกิน 800x800px)"
    )
    
    if uploaded_file is not None:
        # แสดงตัวอย่างรูปภาพ
        image = Image.open(uploaded_file)
        st.image(image, caption="ตัวอย่างรูปภาพ", width=200)
        
        # บันทึกไฟล์
        file_path = save_uploaded_image(uploaded_file, image_type)
        if file_path:
            st.success("✅ อัพโหลดรูปภาพสำเร็จ")
            return file_path
        else:
            return None
    
    return None

def convert_image_to_base64(image_path):
    """
    แปลงรูปภาพเป็น base64 string สำหรับแสดงใน HTML
    
    Args:
        image_path: Path ของไฟล์รูปภาพ
    
    Returns:
        str: Base64 encoded image string หรือ None
    """
    try:
        if not image_path or not os.path.exists(image_path):
            return None
        
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode()
            return f"data:image/jpeg;base64,{img_base64}"
    except Exception as e:
        print(f"[DEBUG] Error converting image to base64: {e}")
        return None

