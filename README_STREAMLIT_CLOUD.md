# คู่มือการ Deploy บน Streamlit Cloud

## ไฟล์ที่จำเป็น

### 1. requirements.txt
ไฟล์นี้มี dependencies ที่จำเป็นสำหรับระบบ POS โดยลบ library ที่อาจจะไม่รองรับบน Streamlit Cloud ออกแล้ว:
- ❌ `opencv-python` - ไม่จำเป็นและใหญ่เกินไป
- ❌ `pyzbar` - ต้องการ system dependencies ที่ไม่มีบน Streamlit Cloud
- ❌ `streamlit-camera-input-live` - อาจจะไม่รองรับ

### 2. .streamlit/config.toml
ไฟล์ตั้งค่าสำหรับ Streamlit Cloud

### 3. packages.txt (ถ้าจำเป็น)
สำหรับติดตั้ง system packages (ถ้า Streamlit Cloud รองรับ)

## วิธี Deploy

1. **Push โค้ดไปที่ GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **ไปที่ Streamlit Cloud**
   - ไปที่ https://share.streamlit.io
   - Sign in ด้วย GitHub account
   - กด "New app"
   - เลือก repository และ branch
   - ตั้งค่า:
     - **Main file path**: `app.py`
     - **Python version**: 3.11 หรือ 3.10

3. **Deploy**
   - กด "Deploy!"
   - รอให้ build เสร็จ

## ข้อจำกัดบน Streamlit Cloud

### 1. กล้องสแกนบาร์โค๊ด
- ❌ `pyzbar` ไม่สามารถติดตั้งได้ (ต้องการ system dependencies)
- ✅ ใช้ `st.camera_input` (built-in) แทน
- ✅ มี fallback เป็นการพิมพ์บาร์โค๊ดด้วยตนเอง

### 2. ฐานข้อมูล
- ✅ SQLite ใช้งานได้ปกติ
- ⚠️ ข้อมูลจะถูกลบเมื่อ app restart (ถ้าไม่ใช้ persistent storage)

### 3. File System
- ⚠️ ไฟล์ที่เขียนจะถูกลบเมื่อ app restart
- ✅ ใช้ session state สำหรับข้อมูลชั่วคราว

## การแก้ไขปัญหา

### ถ้า build ล้มเหลว
1. ตรวจสอบ `requirements.txt` ว่ามี library ที่ไม่รองรับหรือไม่
2. ตรวจสอบ logs ใน Streamlit Cloud dashboard
3. ลบ library ที่ไม่จำเป็นออก

### ถ้า app ไม่ทำงาน
1. ตรวจสอบ logs
2. ตรวจสอบว่า database path ถูกต้อง
3. ตรวจสอบว่า imports ถูกต้อง

## ฟีเจอร์ที่ยังใช้งานได้

✅ ทุกฟีเจอร์หลักยังใช้งานได้:
- Dashboard
- POS
- จัดการสต็อค
- จัดการเมนู
- รายงาน
- จัดการผู้ใช้
- ตั้งค่า

⚠️ ฟีเจอร์ที่จำกัด:
- สแกนบาร์โค๊ดด้วยกล้อง (ต้องใช้การพิมพ์แทน)
- กล้องอาจจะไม่ทำงานบน Streamlit Cloud

## Tips

1. **ใช้ environment variables** สำหรับข้อมูลที่ sensitive
2. **ใช้ Streamlit Secrets** สำหรับ API keys
3. **ทดสอบ local ก่อน deploy**
4. **ตรวจสอบ logs เป็นประจำ**

