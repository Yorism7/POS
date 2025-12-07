#!/bin/bash
# Script สำหรับติดตั้ง dependencies บน Linux/Mac (Local Development)

echo "========================================"
echo "ติดตั้ง Dependencies สำหรับ Local Development"
echo "========================================"
echo ""

# ตรวจสอบว่า Python ติดตั้งแล้วหรือไม่
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] ไม่พบ Python3 กรุณาติดตั้ง Python3 ก่อน"
    exit 1
fi

echo "[1/4] สร้าง Virtual Environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "[ERROR] ไม่สามารถสร้าง virtual environment ได้"
    exit 1
fi

echo "[2/4] เปิดใช้งาน Virtual Environment..."
source venv/bin/activate

echo "[3/4] อัพเดต pip..."
pip install --upgrade pip

echo "[4/4] ติดตั้ง Dependencies..."
pip install -r requirements-local.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[WARNING] มีบาง library ที่ติดตั้งไม่ได้"
    echo "กรุณาติดตั้ง system dependencies ตามที่ระบุใน LOCAL_DEVELOPMENT.md"
    echo ""
    echo "สำหรับ Linux (Ubuntu/Debian):"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install libzbar0"
    echo ""
    echo "สำหรับ macOS:"
    echo "  brew install zbar"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "ติดตั้งเสร็จสมบูรณ์!"
echo "========================================"
echo ""
echo "วิธีรันแอป:"
echo "  1. เปิดใช้งาน virtual environment: source venv/bin/activate"
echo "  2. รันแอป: streamlit run app.py"
echo ""

