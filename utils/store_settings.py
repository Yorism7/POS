"""
Store Settings Management
จัดการการตั้งค่าร้านและระบบ รวมถึง PromptPay
"""

from database.db import get_session
from database.models import StoreSetting
from datetime import datetime
import json

def get_setting(key: str, default: str = "") -> str:
    """
    อ่านค่าการตั้งค่าจาก database
    
    Args:
        key: คีย์ของการตั้งค่า (เช่น 'store_name', 'promptpay_phone')
        default: ค่าเริ่มต้นถ้าไม่พบ
    
    Returns:
        ค่าของการตั้งค่า (string)
    """
    session = get_session()
    try:
        setting = session.query(StoreSetting).filter(StoreSetting.key == key).first()
        if setting:
            return setting.value or default
        return default
    finally:
        session.close()

def set_setting(key: str, value: str, description: str = None, updated_by: int = None) -> bool:
    """
    บันทึกค่าการตั้งค่าใน database
    
    Args:
        key: คีย์ของการตั้งค่า
        value: ค่าที่จะบันทึก
        description: คำอธิบาย (optional)
        updated_by: ID ของผู้ที่อัพเดท (optional)
    
    Returns:
        True ถ้าบันทึกสำเร็จ, False ถ้าเกิดข้อผิดพลาด
    """
    session = get_session()
    try:
        setting = session.query(StoreSetting).filter(StoreSetting.key == key).first()
        
        if setting:
            # อัพเดทค่าที่มีอยู่
            setting.value = value
            if description:
                setting.description = description
            if updated_by:
                setting.updated_by = updated_by
            setting.updated_at = datetime.now()
        else:
            # สร้างใหม่
            setting = StoreSetting(
                key=key,
                value=value,
                description=description,
                updated_by=updated_by,
                updated_at=datetime.now()
            )
            session.add(setting)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to save setting {key}: {e}")
        return False
    finally:
        session.close()

def get_all_settings() -> dict:
    """
    อ่านการตั้งค่าทั้งหมดจาก database
    
    Returns:
        Dictionary ของการตั้งค่าทั้งหมด {key: value}
    """
    session = get_session()
    try:
        settings = session.query(StoreSetting).all()
        return {s.key: s.value or "" for s in settings}
    finally:
        session.close()

def init_default_settings():
    """
    สร้างการตั้งค่าเริ่มต้นถ้ายังไม่มี
    """
    default_settings = {
        'store_name': ('ร้านขายของชำและอาหารตามสั่ง', 'ชื่อร้าน'),
        'store_address': ('', 'ที่อยู่ร้าน'),
        'store_phone': ('', 'เบอร์โทรศัพท์ร้าน'),
        'store_tax_id': ('', 'เลขประจำตัวผู้เสียภาษี'),
        'promptpay_type': ('phone', 'ประเภทบัญชีพร้อมเพย์ (phone/citizen_id)'),
        'promptpay_phone': ('', 'เบอร์โทรศัพท์พร้อมเพย์'),
        'promptpay_citizen_id': ('', 'เลขบัตรประชาชนพร้อมเพย์'),
        'receipt_footer': ('ขอบคุณที่ใช้บริการ', 'ข้อความท้ายใบเสร็จ'),
        'receipt_show_tax': ('false', 'แสดงภาษีมูลค่าเพิ่มในใบเสร็จ'),
        'receipt_tax_rate': ('7.0', 'อัตราภาษีมูลค่าเพิ่ม (%)'),
        'last_login_username': ('', 'Username ที่ล็อคอินล่าสุด (สำหรับ persistent login)'),
    }
    
    session = get_session()
    try:
        for key, (default_value, description) in default_settings.items():
            existing = session.query(StoreSetting).filter(StoreSetting.key == key).first()
            if not existing:
                setting = StoreSetting(
                    key=key,
                    value=default_value,
                    description=description,
                    updated_at=datetime.now()
                )
                session.add(setting)
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to initialize default settings: {e}")
    finally:
        session.close()

def get_store_settings() -> dict:
    """
    อ่านการตั้งค่าร้านทั้งหมด
    
    Returns:
        Dictionary ของการตั้งค่าร้าน
    """
    return {
        'store_name': get_setting('store_name', 'ร้านขายของชำและอาหารตามสั่ง'),
        'store_address': get_setting('store_address', ''),
        'store_phone': get_setting('store_phone', ''),
        'store_tax_id': get_setting('store_tax_id', ''),
    }

def get_promptpay_settings() -> dict:
    """
    อ่านการตั้งค่าพร้อมเพย์
    
    Returns:
        Dictionary ของการตั้งค่าพร้อมเพย์
    """
    return {
        'promptpay_type': get_setting('promptpay_type', 'phone'),
        'promptpay_phone': get_setting('promptpay_phone', ''),
        'promptpay_citizen_id': get_setting('promptpay_citizen_id', ''),
    }

def get_receipt_settings() -> dict:
    """
    อ่านการตั้งค่าใบเสร็จ
    
    Returns:
        Dictionary ของการตั้งค่าใบเสร็จ
    """
    receipt_show_tax_str = get_setting('receipt_show_tax', 'false')
    receipt_tax_rate_str = get_setting('receipt_tax_rate', '7.0')
    
    return {
        'receipt_footer': get_setting('receipt_footer', 'ขอบคุณที่ใช้บริการ'),
        'receipt_show_tax': receipt_show_tax_str.lower() == 'true',
        'receipt_tax_rate': float(receipt_tax_rate_str) if receipt_tax_rate_str else 7.0,
    }

def save_store_settings(store_name: str, store_address: str = "", store_phone: str = "", 
                       store_tax_id: str = "", updated_by: int = None) -> bool:
    """
    บันทึกการตั้งค่าร้าน
    
    Returns:
        True ถ้าบันทึกสำเร็จ
    """
    success = True
    success = success and set_setting('store_name', store_name, 'ชื่อร้าน', updated_by)
    success = success and set_setting('store_address', store_address, 'ที่อยู่ร้าน', updated_by)
    success = success and set_setting('store_phone', store_phone, 'เบอร์โทรศัพท์ร้าน', updated_by)
    success = success and set_setting('store_tax_id', store_tax_id, 'เลขประจำตัวผู้เสียภาษี', updated_by)
    return success

def save_promptpay_settings(promptpay_type: str, promptpay_phone: str = "", 
                            promptpay_citizen_id: str = "", updated_by: int = None) -> bool:
    """
    บันทึกการตั้งค่าพร้อมเพย์
    
    Returns:
        True ถ้าบันทึกสำเร็จ
    """
    success = True
    success = success and set_setting('promptpay_type', promptpay_type, 'ประเภทบัญชีพร้อมเพย์', updated_by)
    success = success and set_setting('promptpay_phone', promptpay_phone, 'เบอร์โทรศัพท์พร้อมเพย์', updated_by)
    success = success and set_setting('promptpay_citizen_id', promptpay_citizen_id, 'เลขบัตรประชาชนพร้อมเพย์', updated_by)
    return success

def save_receipt_settings(receipt_footer: str, receipt_show_tax: bool = False, 
                         receipt_tax_rate: float = 7.0, updated_by: int = None) -> bool:
    """
    บันทึกการตั้งค่าใบเสร็จ
    
    Returns:
        True ถ้าบันทึกสำเร็จ
    """
    success = True
    success = success and set_setting('receipt_footer', receipt_footer, 'ข้อความท้ายใบเสร็จ', updated_by)
    success = success and set_setting('receipt_show_tax', 'true' if receipt_show_tax else 'false', 'แสดงภาษีมูลค่าเพิ่มในใบเสร็จ', updated_by)
    success = success and set_setting('receipt_tax_rate', str(receipt_tax_rate), 'อัตราภาษีมูลค่าเพิ่ม (%)', updated_by)
    return success

