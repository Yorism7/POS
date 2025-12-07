"""
PromptPay QR Code Generator
สร้าง QR Code สำหรับชำระเงินผ่าน PromptPay ตามมาตรฐาน EMV
"""

import qrcode
from io import BytesIO
from typing import Optional

def generate_promptpay_qr(
    amount: float,
    promptpay_type: str = "phone",
    promptpay_id: str = "",
    currency: str = "764"  # THB
) -> Optional[BytesIO]:
    """
    สร้าง QR Code สำหรับ PromptPay
    
    Args:
        amount: จำนวนเงิน (บาท)
        promptpay_type: ประเภทบัญชี ("phone" หรือ "citizen_id")
        promptpay_id: หมายเลขบัญชี (เบอร์โทรหรือเลขบัตรประชาชน)
        currency: รหัสสกุลเงิน (default: 764 = THB)
    
    Returns:
        BytesIO object ของ QR Code image หรือ None ถ้าเกิดข้อผิดพลาด
    """
    try:
        # Validate inputs
        if not promptpay_id:
            return None
        
        # Clean promptpay_id (remove dashes, spaces)
        promptpay_id = promptpay_id.replace("-", "").replace(" ", "")
        
        # Validate format
        if promptpay_type == "phone":
            # Phone number should be 10 digits (remove leading 0 if exists)
            if promptpay_id.startswith("0"):
                promptpay_id = promptpay_id[1:]
            if len(promptpay_id) != 9:
                return None
        elif promptpay_type == "citizen_id":
            # Citizen ID should be 13 digits
            if len(promptpay_id) != 13:
                return None
        else:
            return None
        
        # Build EMV QR Code payload
        # Format: [ID][Length][Value]
        
        # Payload Format Indicator (00)
        payload = "000201"
        
        # Point of Initiation Method (01) - 11 = Static, 12 = Dynamic
        # Use 12 for dynamic amount
        payload += "010212"
        
        # Merchant Account Information (29-51)
        # Tag 29: Merchant Account Information Template
        #   - Tag 00: GUID (A000000677010111 for PromptPay)
        #   - Tag 01-02: Account ID (phone or citizen ID)
        
        # Determine account type
        if promptpay_type == "phone":
            # Phone number: 01 = mobile number
            account_type = "01"
            # Format: 01 + length + phone number
            account_info = f"01{len(promptpay_id):02d}{promptpay_id}"
        else:
            # Citizen ID: 02 = national ID
            account_type = "02"
            # Format: 02 + length + citizen ID
            account_info = f"02{len(promptpay_id):02d}{promptpay_id}"
        
        # GUID for PromptPay
        guid = "A000000677010111"
        guid_length = len(guid)
        
        # Account info length
        account_info_length = len(account_info)
        
        # Merchant Account Information Template
        # Format: 00 (GUID) + 01-02 (Account Info)
        merchant_account = f"00{guid_length:02d}{guid}01{account_info_length:02d}{account_info}"
        merchant_account_length = len(merchant_account)
        
        # Tag 29: Merchant Account Information
        payload += f"29{merchant_account_length:02d}{merchant_account}"
        
        # Transaction Currency (53) - 764 = THB
        payload += f"5303{currency}"
        
        # Transaction Amount (54) - Format: XX.XX
        if amount > 0:
            amount_str = f"{amount:.2f}"
            payload += f"54{len(amount_str):02d}{amount_str}"
        
        # Country Code (58) - TH = Thailand
        payload += "5802TH"
        
        # Additional Data Field Template (62) - Optional
        # Can include bill number, reference number, etc.
        
        # CRC (63) - Will be calculated
        # For now, use placeholder (will be calculated properly in production)
        crc_placeholder = "6304"
        payload_without_crc = payload + crc_placeholder
        
        # Simple CRC calculation (CRC-16/CCITT-FALSE)
        # In production, use proper CRC-16/CCITT-FALSE algorithm
        crc = calculate_crc16(payload_without_crc)
        payload = payload + f"6304{crc:04X}"
        
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        return buf
        
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดในการสร้าง PromptPay QR Code: {str(e)}")
        return None

def calculate_crc16(data: str) -> int:
    """
    คำนวณ CRC-16/CCITT-FALSE สำหรับ EMV QR Code
    
    Args:
        data: ข้อมูลที่ต้องการคำนวณ CRC (string)
    
    Returns:
        CRC-16 value (integer)
    """
    # CRC-16/CCITT-FALSE parameters
    crc = 0xFFFF
    polynomial = 0x1021
    
    # Convert string to bytes
    data_bytes = data.encode('utf-8')
    
    for byte in data_bytes:
        # XOR with byte
        crc ^= (byte << 8)
        
        # Process 8 bits
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    
    return crc

def validate_promptpay_settings(promptpay_type: str, promptpay_id: str) -> tuple[bool, str]:
    """
    ตรวจสอบความถูกต้องของการตั้งค่าพร้อมเพย์
    
    Args:
        promptpay_type: ประเภทบัญชี ("phone" หรือ "citizen_id")
        promptpay_id: หมายเลขบัญชี
    
    Returns:
        (is_valid, error_message)
    """
    if not promptpay_id:
        return False, "กรุณากรอกข้อมูลพร้อมเพย์"
    
    # Clean input
    promptpay_id = promptpay_id.replace("-", "").replace(" ", "")
    
    if promptpay_type == "phone":
        # Phone should be 9-10 digits
        if promptpay_id.startswith("0"):
            promptpay_id = promptpay_id[1:]
        if len(promptpay_id) != 9 or not promptpay_id.isdigit():
            return False, "เบอร์โทรศัพท์ต้องเป็นตัวเลข 9-10 หลัก"
    elif promptpay_type == "citizen_id":
        # Citizen ID should be 13 digits
        if len(promptpay_id) != 13 or not promptpay_id.isdigit():
            return False, "เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลัก"
    else:
        return False, "ประเภทบัญชีไม่ถูกต้อง"
    
    return True, ""

