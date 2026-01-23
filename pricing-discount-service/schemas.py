from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"
    BUY_ONE_GET_ONE = "bogo"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    FINANCING = "financing"
    LEASE = "lease"

class DiscountBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_type: DiscountType
    value: float = Field(..., gt=0)
    min_purchase_amount: float = Field(0, ge=0)
    max_discount_amount: Optional[float] = Field(None, gt=0)
    valid_from: datetime
    valid_to: datetime
    usage_limit: Optional[int] = Field(None, gt=0)
    applies_to_all_vehicles: bool = True
    vehicle_ids: Optional[str] = None  # JSON строка
    customer_group: str = Field("all", max_length=50)

    @validator('valid_to')
    def valid_to_after_valid_from(cls, v, values):
        if 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_to must be after valid_from')
        return v

class DiscountCreate(DiscountBase):
    pass

class DiscountUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=3, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_type: Optional[DiscountType] = None
    value: Optional[float] = Field(None, gt=0)
    min_purchase_amount: Optional[float] = Field(None, ge=0)
    max_discount_amount: Optional[float] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    applies_to_all_vehicles: Optional[bool] = None
    vehicle_ids: Optional[str] = None
    customer_group: Optional[str] = Field(None, max_length=50)

class Discount(DiscountBase):
    id: int
    is_active: bool
    used_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PriceCalculationRequest(BaseModel):
    vehicle_id: int
    customer_id: Optional[int] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    trade_in_value: Optional[float] = Field(None, ge=0)
    discount_code: Optional[str] = None
    accessories: Optional[List[Dict[str, Any]]] = None

class PriceCalculationResponse(BaseModel):
    base_price: float
    final_price: float
    applied_discounts: List[Dict[str, Any]]
    currency: str = "USD"

class DiscountValidationRequest(BaseModel):
    discount_code: str
    customer_id: Optional[int] = None
    vehicle_id: Optional[int] = None

class DiscountValidationResponse(BaseModel):
    is_valid: bool
    message: str
    discount: Optional[Discount] = None