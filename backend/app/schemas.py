from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime

# --- Product Schemas ---
class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, description="Unique SKU code")
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    quantity: int = Field(..., ge=0)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1)
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    quantity: Optional[int] = Field(None, ge=0)

class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone_digits(cls, v):
        if v is not None and v != "":
            digits = "".join([c for c in v if c.isdigit()])
            if len(digits) not in (10, 12):
                raise ValueError("Phone number must contain exactly 10 or 12 digits")
        return v

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone_digits(cls, v):
        if v is not None and v != "":
            digits = "".join([c for c in v if c.isdigit()])
            if len(digits) not in (10, 12):
                raise ValueError("Phone number must contain exactly 10 or 12 digits")
        return v

class CustomerOut(CustomerBase):
    id: int

    class Config:
        from_attributes = True


# --- Order Item Schemas ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_order: float
    product: Optional[ProductOut] = None

    class Config:
        from_attributes = True


# --- Order Schemas ---
class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v

class OrderOut(BaseModel):
    id: int
    customer_id: int
    total_amount: float
    created_at: datetime
    customer: CustomerOut
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
