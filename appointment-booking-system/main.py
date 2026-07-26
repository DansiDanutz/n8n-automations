#!/usr/bin/env python3
"""
Appointment Booking System - FastAPI Service
Complete appointment booking and scheduling system
"""

import os
import uuid
import hmac
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, time, timezone
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def required_secret(name: str, minimum_length: int) -> str:
    value = os.getenv(name, "")
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be at least {minimum_length} characters")
    return value


admin_api_key = required_secret("ADMIN_API_KEY", 32)


async def require_admin(x_api_key: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_api_key, admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin API key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_default_time_slots()
    yield


app = FastAPI(
    title="Appointment Booking System",
    description="Professional appointment booking and scheduling service",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
bookings_db = {}
time_slots_db = {}
business_config = {
    "business_name": "Professional Services",
    "timezone": "UTC",
    "working_hours": {
        "monday": {"start": "09:00", "end": "17:00"},
        "tuesday": {"start": "09:00", "end": "17:00"},
        "wednesday": {"start": "09:00", "end": "17:00"},
        "thursday": {"start": "09:00", "end": "17:00"},
        "friday": {"start": "09:00", "end": "17:00"},
        "saturday": {"start": "10:00", "end": "14:00"},
        "sunday": {"start": "closed", "end": "closed"}
    },
    "default_duration": 60,
    "buffer_time": 15
}

class BookingRequest(BaseModel):
    client_name: str
    client_email: EmailStr
    client_phone: Optional[str] = None
    service_type: str
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM format
    duration: int = 60  # minutes
    notes: Optional[str] = None
    send_confirmation: bool = True

class BookingUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_phone: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class TimeSlotRequest(BaseModel):
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    duration: int = 60  # minutes
    service_types: List[str] = Field(default_factory=lambda: ["general"])
    max_bookings: int = 1

class BookingResponse(BaseModel):
    id: str
    client_name: str
    client_email: str
    client_phone: Optional[str]
    service_type: str
    date: str
    time: str
    duration: int
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str

class AvailabilityResponse(BaseModel):
    date: str
    available_slots: List[Dict[str, Any]]
    booked_slots: List[Dict[str, Any]]
    total_available: int

def generate_booking_id() -> str:
    """Generate unique booking ID"""
    return str(uuid.uuid4())[:8].upper()

def validate_date_format(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time_format(time_str: str) -> bool:
    """Validate time format HH:MM"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def is_time_slot_available(date: str, time: str, duration: int) -> bool:
    """Check if time slot is available"""
    slot_key = f"{date}_{time}"
    
    # Check if slot exists in time_slots_db
    if slot_key not in time_slots_db:
        return False
    
    # Check if already booked
    for booking in bookings_db.values():
        if (booking["date"] == date and 
            booking["time"] == time and 
            booking["status"] != "cancelled"):
            return False
    
    return True

def send_email_reminder(booking: Dict[str, Any], background_tasks: BackgroundTasks):
    """Send email confirmation/reminder (placeholder)"""
    # In production, integrate with actual email service
    print(f"📧 Email reminder sent to {booking['client_email']} for booking {booking['id']}")

async def create_default_time_slots():
    """Create default time slots for the next 30 days"""
    today = datetime.now().date()
    
    for i in range(30):
        current_date = today + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A").lower()
        
        # Skip if day is closed
        if business_config["working_hours"][day_name]["start"] == "closed":
            continue
        
        start_time = business_config["working_hours"][day_name]["start"]
        end_time = business_config["working_hours"][day_name]["end"]
        
        # Generate hourly slots
        current_time = datetime.strptime(start_time, "%H:%M")
        end_datetime = datetime.strptime(end_time, "%H:%M")
        
        while current_time < end_datetime:
            slot_key = f"{date_str}_{current_time.strftime('%H:%M')}"
            if slot_key not in time_slots_db:
                time_slots_db[slot_key] = {
                    "date": date_str,
                    "start_time": current_time.strftime("%H:%M"),
                    "end_time": (current_time + timedelta(minutes=60)).strftime("%H:%M"),
                    "duration": 60,
                    "service_types": ["consultation", "meeting", "appointment"],
                    "max_bookings": 1,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            current_time += timedelta(hours=1)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Appointment Booking System",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }

@app.post("/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingRequest, background_tasks: BackgroundTasks):
    """Create a new appointment booking"""
    
    # Validate date and time formats
    if not validate_date_format(booking.date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if not validate_time_format(booking.time):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    # Check if date is in the past
    booking_datetime = datetime.strptime(f"{booking.date} {booking.time}", "%Y-%m-%d %H:%M")
    if booking_datetime < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")
    
    # Check availability
    if not is_time_slot_available(booking.date, booking.time, booking.duration):
        raise HTTPException(status_code=409, detail="Time slot not available")
    
    # Create booking
    booking_id = generate_booking_id()
    new_booking = {
        "id": booking_id,
        "client_name": booking.client_name,
        "client_email": booking.client_email,
        "client_phone": booking.client_phone,
        "service_type": booking.service_type,
        "date": booking.date,
        "time": booking.time,
        "duration": booking.duration,
        "notes": booking.notes,
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    bookings_db[booking_id] = new_booking
    
    # Send confirmation email
    if booking.send_confirmation:
        background_tasks.add_task(send_email_reminder, new_booking, background_tasks)
    
    return BookingResponse(**new_booking)

@app.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    client_email: Optional[str] = Query(None, description="Filter by client email"),
    _admin: None = Depends(require_admin),
):
    """Get all bookings with optional filters"""
    
    bookings = list(bookings_db.values())
    
    # Apply filters
    if date:
        if not validate_date_format(date):
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        bookings = [b for b in bookings if b["date"] == date]
    
    if status:
        bookings = [b for b in bookings if b["status"] == status]
    
    if client_email:
        bookings = [b for b in bookings if b["client_email"] == client_email]
    
    return [BookingResponse(**booking) for booking in bookings]

@app.get("/availability", response_model=AvailabilityResponse)
async def get_availability(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    """Get availability for a specific date"""
    
    if not validate_date_format(date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all slots for the date
    date_slots = {k: v for k, v in time_slots_db.items() if v["date"] == date}
    
    # Get bookings for the date
    date_bookings = [b for b in bookings_db.values() if b["date"] == date and b["status"] != "cancelled"]
    
    available_slots = []
    booked_slots = []
    
    for slot_key, slot in date_slots.items():
        slot_time = slot["start_time"]
        
        # Check if this slot is booked
        is_booked = any(booking["time"] == slot_time for booking in date_bookings)
        
        slot_info = {
            "time": slot_time,
            "duration": slot["duration"],
            "service_types": slot["service_types"],
            "end_time": slot["end_time"]
        }
        
        if is_booked:
            slot_info.update({
                "status": "unavailable",
            })
            booked_slots.append(slot_info)
        else:
            available_slots.append(slot_info)
    
    return AvailabilityResponse(
        date=date,
        available_slots=available_slots,
        booked_slots=booked_slots,
        total_available=len(available_slots)
    )

@app.post("/slots")
async def create_time_slot(slot: TimeSlotRequest, _admin: None = Depends(require_admin)):
    """Create a new time slot"""
    
    if not validate_date_format(slot.date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if not validate_time_format(slot.start_time) or not validate_time_format(slot.end_time):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    slot_key = f"{slot.date}_{slot.start_time}"
    
    if slot_key in time_slots_db:
        raise HTTPException(status_code=409, detail="Time slot already exists")
    
    time_slots_db[slot_key] = {
        "date": slot.date,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "duration": slot.duration,
        "service_types": slot.service_types,
        "max_bookings": slot.max_bookings,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return {
        "message": "Time slot created successfully",
        "slot_key": slot_key,
        "slot_data": time_slots_db[slot_key]
    }

@app.delete("/bookings/{booking_id}")
async def cancel_booking(
    booking_id: str,
    background_tasks: BackgroundTasks,
    _admin: None = Depends(require_admin),
):
    """Cancel a booking"""
    
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id]
    booking["status"] = "cancelled"
    booking["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Send cancellation email
    background_tasks.add_task(send_email_reminder, booking, background_tasks)
    
    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking_id,
        "cancelled_at": booking["updated_at"]
    }

@app.put("/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    update_data: BookingUpdate,
    background_tasks: BackgroundTasks,
    _admin: None = Depends(require_admin),
):
    """Update an existing booking"""
    
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = bookings_db[booking_id].copy()
    
    # Validate new date/time if provided
    if update_data.date and not validate_date_format(update_data.date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if update_data.time and not validate_time_format(update_data.time):
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            booking[field] = value
    
    booking["updated_at"] = datetime.now(timezone.utc).isoformat()
    bookings_db[booking_id] = booking
    
    # Send update notification
    background_tasks.add_task(send_email_reminder, booking, background_tasks)
    
    return BookingResponse(**booking)

@app.get("/stats")
async def get_booking_stats(_admin: None = Depends(require_admin)):
    """Get booking statistics"""
    
    total_bookings = len(bookings_db)
    confirmed_bookings = len([b for b in bookings_db.values() if b["status"] == "confirmed"])
    cancelled_bookings = len([b for b in bookings_db.values() if b["status"] == "cancelled"])
    
    # Today's bookings
    today = datetime.now().strftime("%Y-%m-%d")
    today_bookings = len([b for b in bookings_db.values() if b["date"] == today])
    
    # Next 7 days bookings
    next_week_bookings = 0
    for i in range(7):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        next_week_bookings += len([b for b in bookings_db.values() if b["date"] == date])
    
    return {
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "today_bookings": today_bookings,
        "next_week_bookings": next_week_bookings,
        "total_time_slots": len(time_slots_db),
        "business_config": business_config
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
