from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from enum import Enum

# ========================================
# Generic Schemas
# ========================================

class PortalStatus(Enum):
    active = "active"
    inactive = "inactive"

# ========================================
# Order Schemas
# ========================================
class OrderStop(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    real_lat: Optional[float] = None
    real_lng: Optional[float] = None
    type: Optional[str] = None

class OrderPrice(BaseModel):
    booking_fee: Optional[float] = None
    cancellation_fee: Optional[float] = None
    cash_discount: Optional[float] = None
    net_earnings: Optional[float] = None
    tip: Optional[float] = None
    commission: Optional[float] = None
    in_app_discount: Optional[float] = None
    toll_fee: Optional[float] = None
    ride_price: Optional[float] = None

class FleetOrder(BaseModel):
    order_reference: Optional[str] = None
    driver_name: Optional[str] = None
    payment_method: Optional[str] = None
    driver_uuid: Optional[str] = None
    driver_phone: Optional[str] = None
    partner_uuid: Optional[str] = None
    payment_confirmed_timestamp: Optional[int] = None
    order_created_timestamp: Optional[int] = None
    order_status: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_license_plate: Optional[str] = None
    price_review_reason: Optional[str] = None
    pickup_address: Optional[str] = None
    ride_distance: Optional[float] = None
    order_accepted_timestamp: Optional[int] = None
    order_pickup_timestamp: Optional[int] = None
    order_drop_off_timestamp: Optional[int] = None
    order_finished_timestamp: Optional[int] = None
    order_stops: Optional[List[OrderStop]] = None
    order_price: Optional[OrderPrice] = None

# ========================================
# Vehicle Schemas
# ========================================
class Vehicle(BaseModel):
    id: int
    model: str
    year: int
    reg_number: str
    uuid: UUID
    state: PortalStatus


# ========================================
# Driver Schemas
# ========================================
class Driver(BaseModel):
    driver_uuid: UUID
    partner_uuid: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    state: PortalStatus
    has_cash_payment: bool

# ========================================
# Fleet State Log Schemas
# ========================================
class FleetStateLog(BaseModel):
    created: int
    state: str
    driver_uuid: UUID
    vehicle_uuid: UUID
    lat: float
    lng: float