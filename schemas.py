from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=15)


class CustomerResponse(CustomerCreate):
    customer_id: int
    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    product_id: int
    product_name: str
    category: str
    price: float
    stock: int
    model_config = ConfigDict(from_attributes=True)


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float


class CartResponse(BaseModel):
    customer_id: int
    items: list[CartItemResponse]
    total_amount: float


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    price: float
    subtotal: float


class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    order_date: datetime | None
    total_amount: float


class OrderDetailsResponse(OrderResponse):
    items: list[OrderItemResponse]
