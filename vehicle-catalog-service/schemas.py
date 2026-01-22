from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUGIN_HYBRID = "plugin_hybrid"

class TransmissionType(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"

class VehicleBase(BaseModel):
    vin: str = Field(..., min_length=17, max_length=17)
    brand: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)
    color: Optional[str] = Field(None, max_length=50)
    fuel_type: FuelType
    transmission: TransmissionType
    engine_size: Optional[float] = Field(None, gt=0)
    horsepower: Optional[int] = Field(None, gt=0)
    mileage: Optional[int] = Field(None, ge=0)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    features: Optional[str] = None  # JSON строка
    image_url: Optional[str] = Field(None, max_length=500)

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    vin: Optional[str] = Field(None, min_length=17, max_length=17)
    brand: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year + 1)
    color: Optional[str] = Field(None, max_length=50)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[TransmissionType] = None
    engine_size: Optional[float] = Field(None, gt=0)
    horsepower: Optional[int] = Field(None, gt=0)
    mileage: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    features: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_available: Optional[bool] = None

class Vehicle(VehicleBase):
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True