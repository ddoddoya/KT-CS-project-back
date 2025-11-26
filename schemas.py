from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- Base Models (Shared) ---

class InternetBase(BaseModel):
    plan_name: Optional[str] = None
    speed_category: Optional[str] = None # 100M, 500M, 1G
    package_wifi: Optional[str] = None
    contract_period: Optional[str] = None
    discount_type: Optional[str] = None
    install_method: Optional[str] = None

class TVBase(BaseModel):
    service_type_1: Optional[str] = None
    service_type_2: Optional[str] = None
    genie_tv_type: Optional[str] = None
    contract_period: Optional[str] = None
    add_ons: Optional[str] = None
    install_info: Optional[str] = None

class PhoneBase(BaseModel):
    phone_type: str # "일반전화" or "인터넷전화"
    plan_name: Optional[str] = None
    contract_period: Optional[str] = None
    desired_number: Optional[str] = None
    confirmed_number: Optional[str] = None
    add_ons: Optional[str] = None
    directory_listing: Optional[str] = None
    # Specific fields
    install_fee: Optional[str] = None # 일반전화
    install_method: Optional[str] = None # 인터넷전화
    access_internet: Optional[str] = None # 인터넷전화

class DeviceBase(BaseModel):
    device_model: Optional[str] = None
    purchase_type: Optional[str] = None # "일시불", "할부"
    price: Optional[int] = 0
    payment_method: Optional[str] = None
    installment_fee: Optional[int] = 0
    penalty_subsidy: Optional[str] = None

class CustomerBase(BaseModel):
    name: str
    birth_date: str
    rrn_prefix: str
    address: str
    contact: str

# --- Create Request Model ---

class ApplicationCreate(BaseModel):
    # Customer Info
    customer: CustomerBase
    
    # Sales Info (Header)
    seller_emp_id: Optional[str] = None
    agency_code: Optional[str] = None
    seller_name: Optional[str] = None
    seller_contact: Optional[str] = None
    recommender: Optional[str] = None
    tv_joint_sub_serial: Optional[str] = None
    
    # Services (Optional)
    internet: Optional[InternetBase] = None
    tv: Optional[TVBase] = None
    phone: Optional[PhoneBase] = None
    device: Optional[DeviceBase] = None

# --- Response Model ---

class ApplicationResponse(BaseModel):
    id: int
    status: str
    application_date: str
    customer_name: str
    
    class Config:
        from_attributes = True

