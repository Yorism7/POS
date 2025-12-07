@echo off
REM Script สำหรับติดตั้ง dependencies บน Windows (Local Development)
echo ========================================
echo ติดตั้ง Dependencies สำหรับ Local Development
echo ========================================
echo.

REM ตรวจสอบว่า Python ติดตั้งแล้วหรือไม่
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python ก่อน
    pause
    exit /b 1
)

echo [1/3] สร้าง Virtual Environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] ไม่สามารถสร้าง virtual environment ได้
    pause
    exit /b 1
)

echo [2/3] เปิดใช้งาน Virtual Environment...
call venv\Scripts\activate.bat

echo [3/3] ติดตั้ง Dependencies...
pip install --upgrade pip
pip install -r requirements-local.txt

if errorlevel 1 (
    echo.
    echo [WARNING] มีบาง library ที่ติดตั้งไม่ได้
    echo กรุณาติดตั้ง system dependencies ตามที่ระบุใน LOCAL_DEVELOPMENT.md
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ติดตั้งเสร็จสมบูรณ์!
echo ========================================
echo.
echo วิธีรันแอป:
echo   1. เปิดใช้งาน virtual environment: venv\Scripts\activate
echo   2. รันแอป: streamlit run app.py
echo.
pause

