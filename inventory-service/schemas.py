from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class InventoryStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    MAINTENANCE = "maintenance"

class InventoryBase(BaseModel):
    vehicle_id: int
    vin: str = Field(..., min_length=17, max_length=17)
    stock_quantity: int = Field(1, ge=0)
    available_quantity: int = Field(1, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    sold_quantity: int = Field(0, ge=0)
    status: InventoryStatus = InventoryStatus.AVAILABLE
    location: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('available_quantity', 'reserved_quantity', 'sold_quantity')
    def validate_quantities(cls, v, values):
        if 'stock_quantity' in values and v > values['stock_quantity']:
            raise ValueError(f"Cannot exceed stock quantity")
        return v

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    stock_quantity: Optional[int] = Field(None, ge=0)
    available_quantity: Optional[int] = Field(None, ge=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    sold_quantity: Optional[int] = Field(None, ge=0)
    status: Optional[InventoryStatus] = None
    location: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=500)

class InventoryItem(InventoryBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

class ReserveRequest(BaseModel):
    vehicle_id: int
    order_id: int
    quantity: int = Field(1, ge=1)

class ReleaseRequest(BaseModel):
    vehicle_id: int
    quantity: int = Field(1, ge=1)

class SaleRequest(BaseModel):
    vehicle_id: int
    order_id: int
    quantity: int = Field(1, ge=1)