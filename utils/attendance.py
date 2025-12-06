"""
Attendance Management Functions
จัดการเวลาเข้า-ออกงานของพนักงาน
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from database.db import get_session
from database.models import Attendance, EmployeeShift, User, Sale
from sqlalchemy import func, and_, or_
from utils.helpers import format_currency

def clock_in(user_id: int, shift_id: int = None, notes: str = None) -> Optional[Attendance]:
    """บันทึกเวลาเข้างาน"""
    session = get_session()
    try:
        today = datetime.now().date()
        
        # Check if already clocked in today
        existing = session.query(Attendance).filter(
            Attendance.user_id == user_id,
            func.date(Attendance.attendance_date) == today,
            Attendance.clock_out == None
        ).first()
        
        if existing:
            return None  # Already clocked in
        
        # Create new attendance record
        attendance = Attendance(
            user_id=user_id,
            shift_id=shift_id,
            attendance_date=datetime.now(),
            clock_in=datetime.now(),
            is_late=False,
            is_absent=False,
            notes=notes
        )
        
        session.add(attendance)
        session.commit()
        session.refresh(attendance)
        
        print(f"[DEBUG] Clock in successful - User ID: {user_id}, Time: {attendance.clock_in}")
        return attendance
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in clock_in: {str(e)}")
        return None
    finally:
        session.close()

def clock_out(user_id: int, notes: str = None) -> Optional[Attendance]:
    """บันทึกเวลาออกงาน"""
    session = get_session()
    try:
        today = datetime.now().date()
        
        # Find today's attendance without clock out
        attendance = session.query(Attendance).filter(
            Attendance.user_id == user_id,
            func.date(Attendance.attendance_date) == today,
            Attendance.clock_out == None
        ).first()
        
        if not attendance:
            return None  # No clock in record found
        
        # Update clock out
        attendance.clock_out = datetime.now()
        
        # Calculate total hours
        if attendance.clock_in:
            time_diff = attendance.clock_out - attendance.clock_in
            total_seconds = time_diff.total_seconds()
            attendance.total_hours = total_seconds / 3600.0  # Convert to hours
        
        if notes:
            attendance.notes = notes
        
        session.commit()
        session.refresh(attendance)
        
        print(f"[DEBUG] Clock out successful - User ID: {user_id}, Total Hours: {attendance.total_hours:.2f}")
        return attendance
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in clock_out: {str(e)}")
        return None
    finally:
        session.close()

def get_today_attendance(user_id: int) -> Optional[Attendance]:
    """Get today's attendance record"""
    session = get_session()
    try:
        today = datetime.now().date()
        return session.query(Attendance).filter(
            Attendance.user_id == user_id,
            func.date(Attendance.attendance_date) == today
        ).first()
    finally:
        session.close()

def get_attendance_by_date_range(user_id: int, start_date: datetime, end_date: datetime) -> List[Attendance]:
    """Get attendance records by date range"""
    session = get_session()
    try:
        return session.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        ).order_by(Attendance.attendance_date.desc()).all()
    finally:
        session.close()

def get_employee_performance(user_id: int, start_date: datetime, end_date: datetime) -> Dict:
    """Get employee performance statistics"""
    session = get_session()
    try:
        # Attendance stats
        attendances = session.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        ).all()
        
        total_days = len(attendances)
        total_hours = sum(a.total_hours for a in attendances if a.total_hours)
        late_count = sum(1 for a in attendances if a.is_late)
        absent_count = sum(1 for a in attendances if a.is_absent)
        
        # Sales stats
        sales = session.query(Sale).filter(
            Sale.created_by == user_id,
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_void == False
        ).all()
        
        total_sales = sum(s.final_amount for s in sales)
        sales_count = len(sales)
        avg_sale = total_sales / sales_count if sales_count > 0 else 0.0
        
        return {
            'total_days': total_days,
            'total_hours': total_hours,
            'late_count': late_count,
            'absent_count': absent_count,
            'total_sales': total_sales,
            'sales_count': sales_count,
            'avg_sale': avg_sale
        }
    finally:
        session.close()

def create_shift(user_id: int, shift_date: datetime, shift_start: datetime = None, 
                shift_end: datetime = None, break_duration: int = 0, notes: str = None) -> Optional[EmployeeShift]:
    """Create employee shift"""
    session = get_session()
    try:
        shift = EmployeeShift(
            user_id=user_id,
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=shift_end,
            break_duration=break_duration,
            notes=notes
        )
        session.add(shift)
        session.commit()
        session.refresh(shift)
        return shift
    except Exception as e:
        session.rollback()
        print(f"[DEBUG] Error in create_shift: {str(e)}")
        return None
    finally:
        session.close()

def get_shifts_by_date_range(user_id: int, start_date: datetime, end_date: datetime) -> List[EmployeeShift]:
    """Get shifts by date range"""
    session = get_session()
    try:
        return session.query(EmployeeShift).filter(
            EmployeeShift.user_id == user_id,
            EmployeeShift.shift_date >= start_date,
            EmployeeShift.shift_date <= end_date
        ).order_by(EmployeeShift.shift_date.desc()).all()
    finally:
        session.close()

