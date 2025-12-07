# 📚 Library บน Streamlit Cloud

## ✅ Streamlit Cloud ติดตั้ง Library ได้!

Streamlit Cloud **สามารถติดตั้ง library เพิ่มเองได้** โดยใช้ไฟล์ `requirements.txt`

## 🔧 วิธีติดตั้ง Library

### 1. เพิ่มใน `requirements.txt`
```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
your-library>=1.0.0  # เพิ่ม library ที่ต้องการ
```

### 2. Push ไป GitHub
```bash
git add requirements.txt
git commit -m "Add new library"
git push origin main
```

### 3. Streamlit Cloud จะติดตั้งอัตโนมัติ
- เมื่อ push ไป GitHub, Streamlit Cloud จะ rebuild app
- ระบบจะอ่าน `requirements.txt` และติดตั้ง library ทั้งหมด

## ⚠️ ข้อจำกัด

### ❌ Library ที่ติดตั้งไม่ได้

#### 1. Library ที่ต้องการ System Dependencies
**ตัวอย่าง:**
- `pyzbar` - ต้องการ `libzbar0` (system package)
- `opencv-python` - ต้องการ system libraries
- บาง library ที่ compile จาก C/C++

**วิธีแก้:**
- ใช้ `packages.txt` สำหรับ system packages (แต่ Streamlit Cloud ไม่รองรับทั้งหมด)
- หรือใช้ library แทนที่

#### 2. Library ที่ต้องการ Hardware Access
- Library ที่เข้าถึง hardware โดยตรง
- Camera libraries บางตัว

### ✅ Library ที่ติดตั้งได้

#### Pure Python Libraries
- ✅ `pandas`, `numpy`, `plotly`
- ✅ `sqlalchemy`, `bcrypt`
- ✅ `qrcode`, `Pillow`
- ✅ `reportlab`, `openpyxl`
- ✅ `streamlit-camera-input-live` (อาจจะได้)

#### Libraries ที่มี Binary Wheels
- ✅ Library ที่มี pre-compiled wheels สำหรับ Linux
- ✅ ส่วนใหญ่ติดตั้งได้

## 🔍 วิธีตรวจสอบว่า Library ติดตั้งได้หรือไม่

### 1. ตรวจสอบใน Documentation
- ดูว่า library รองรับ Linux หรือไม่
- ดูว่าต้องการ system dependencies หรือไม่

### 2. ทดสอบ Local
```bash
# สร้าง virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# หรือ
venv\Scripts\activate  # Windows

# ติดตั้ง
pip install -r requirements.txt
```

### 3. ดู Logs บน Streamlit Cloud
- ไปที่ dashboard
- ดู build logs
- ตรวจสอบ error messages

## 💡 วิธีแก้ไขปัญหา Library ที่ติดตั้งไม่ได้

### วิธีที่ 1: ใช้ Alternative Library
```python
# แทน pyzbar
try:
    from pyzbar import pyzbar
except ImportError:
    # ใช้ fallback
    pyzbar = None
```

### วิธีที่ 2: ใช้ Built-in Functions
```python
# แทน opencv
from PIL import Image  # ใช้ Pillow แทน
```

### วิธีที่ 3: ใช้ Optional Dependencies
```python
try:
    import optional_library
except ImportError:
    optional_library = None
    # ใช้ fallback
```

## 📋 Library ที่เราใช้ในระบบ

### ✅ ติดตั้งได้ (อยู่ใน requirements.txt)
- `streamlit` - Framework หลัก
- `sqlalchemy` - ORM
- `pandas` - Data processing
- `plotly` - Charts
- `reportlab` - PDF generation
- `bcrypt` - Password hashing
- `openpyxl` - Excel files
- `python-barcode` - Barcode generation
- `Pillow` - Image processing
- `numpy` - Numerical computing
- `qrcode[pil]` - QR Code generation

### ❌ ติดตั้งไม่ได้ (ลบออกแล้ว)
- `pyzbar` - ต้องการ `libzbar0`
- `opencv-python` - ใหญ่เกินไปและไม่จำเป็น
- `streamlit-camera-input-live` - อาจจะไม่รองรับ

## 🚀 วิธีเพิ่ม Library ใหม่

### ตัวอย่าง: เพิ่ม `requests`
1. แก้ไข `requirements.txt`:
   ```txt
   requests>=2.31.0
   ```

2. Push ไป GitHub:
   ```bash
   git add requirements.txt
   git commit -m "Add requests library"
   git push origin main
   ```

3. Streamlit Cloud จะ rebuild และติดตั้งอัตโนมัติ

## 📝 หมายเหตุ

- Streamlit Cloud ใช้ **Linux environment**
- Library ต้องรองรับ Linux
- System dependencies จำกัด
- Build time อาจจะนานขึ้นถ้ามี library ใหญ่

## 🔗 เอกสารเพิ่มเติม

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Python Package Index](https://pypi.org/)
- [Streamlit Components](https://streamlit.io/components)

