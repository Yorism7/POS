# 💻 คู่มือการใช้งาน Local Development

## 🎯 เป้าหมาย

ให้ทุกฟีเจอร์ใช้งานได้เต็มที่บน localhost รวมถึง:
- ✅ สแกนบาร์โค๊ดด้วยกล้อง (pyzbar)
- ✅ กล้องแบบ real-time (streamlit-camera-input-live)
- ✅ Image processing (opencv-python - ถ้าต้องการ)

## 📦 การติดตั้ง

### 1. ติดตั้ง Dependencies สำหรับ Local

```bash
# ใช้ requirements-local.txt ที่มี library ทั้งหมด
pip install -r requirements-local.txt
```

### 2. System Dependencies (สำหรับ pyzbar)

#### Windows:
```bash
# ติดตั้งผ่าน conda หรือใช้ pre-built wheels
conda install -c conda-forge pyzbar
# หรือ
pip install pyzbar
```

#### macOS:
```bash
# ติดตั้ง zbar ผ่าน Homebrew
brew install zbar
pip install pyzbar
```

#### Linux (Ubuntu/Debian):
```bash
# ติดตั้ง zbar system package
sudo apt-get update
sudo apt-get install libzbar0
pip install pyzbar
```

### 3. รันแอปพลิเคชัน

```bash
streamlit run app.py
```

## 🔧 การตั้งค่า

### Database Path
- Local: ใช้ `data/` directory (สร้างอัตโนมัติ)
- Database: `data/pos.db`

### Camera Access
- ต้องอนุญาตการเข้าถึงกล้องใน browser
- ใช้ HTTPS หรือ localhost
- Browser ที่รองรับ: Chrome, Firefox, Edge

## ✅ ฟีเจอร์ที่ใช้งานได้บน Local

### ฟีเจอร์หลัก
- ✅ Dashboard
- ✅ POS
- ✅ จัดการสต็อค
- ✅ จัดการเมนู
- ✅ รายงาน
- ✅ จัดการผู้ใช้
- ✅ ตั้งค่า

### ฟีเจอร์พิเศษ (Local Only)
- ✅ **สแกนบาร์โค๊ดด้วยกล้อง** (pyzbar)
- ✅ **กล้องแบบ real-time** (streamlit-camera-input-live)
- ✅ **Image processing** (opencv-python - ถ้าติดตั้ง)

## 🆚 เปรียบเทียบ Local vs Cloud

| ฟีเจอร์ | Local | Streamlit Cloud |
|---------|-------|----------------|
| สแกนบาร์โค๊ดด้วยกล้อง | ✅ | ❌ (ใช้พิมพ์แทน) |
| กล้อง real-time | ✅ | ⚠️ (st.camera_input) |
| Image processing | ✅ | ❌ |
| Database persistent | ✅ | ⚠️ (/tmp) |
| System dependencies | ✅ | ❌ |

## 🐛 แก้ไขปัญหา

### ปัญหา: pyzbar ติดตั้งไม่ได้

#### Windows:
```bash
# ใช้ conda
conda install -c conda-forge pyzbar
```

#### macOS:
```bash
# ติดตั้ง zbar ก่อน
brew install zbar
pip install pyzbar
```

#### Linux:
```bash
# ติดตั้ง system package
sudo apt-get install libzbar0
pip install pyzbar
```

### ปัญหา: กล้องไม่ทำงาน

1. **ตรวจสอบ Browser**
   - ใช้ Chrome, Firefox, หรือ Edge
   - อนุญาตการเข้าถึงกล้อง

2. **ตรวจสอบ URL**
   - ใช้ `localhost` หรือ `127.0.0.1`
   - หรือใช้ HTTPS

3. **ตรวจสอบ Permissions**
   - อนุญาตการเข้าถึงกล้องใน browser settings

### ปัญหา: Library ไม่พบ

```bash
# ติดตั้งใหม่
pip install -r requirements-local.txt --upgrade
```

## 📝 หมายเหตุ

- **Local Development**: ใช้ `requirements-local.txt`
- **Streamlit Cloud**: ใช้ `requirements.txt`
- Database บน local จะเก็บใน `data/` directory
- ข้อมูลจะไม่ถูกลบเมื่อ restart (ต่างจาก cloud)

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone <your-repo>
cd POS

# 2. สร้าง virtual environment (แนะนำ)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# หรือ
venv\Scripts\activate  # Windows

# 3. ติดตั้ง dependencies
pip install -r requirements-local.txt

# 4. รันแอป
streamlit run app.py
```

## 💡 Tips

1. **ใช้ Virtual Environment**
   - แยก dependencies ของแต่ละโปรเจค
   - หลีกเลี่ยง conflicts

2. **ทดสอบก่อน Deploy**
   - ทดสอบทุกฟีเจอร์บน local ก่อน
   - ตรวจสอบว่าโค้ดทำงานถูกต้อง

3. **Backup Database**
   - สำรองข้อมูลเป็นประจำ
   - ใช้ฟีเจอร์ backup ในระบบ

