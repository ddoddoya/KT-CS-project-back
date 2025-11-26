from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Enum, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import date, datetime
from database import Base

# --- Enums for better data integrity ---
class AppStatus(str, enum.Enum):
    PENDING = "접수"
    COMPLETED = "개통완료"
    HOLD = "보류"
    CANCELED = "취소"

class PhoneType(str, enum.Enum):
    GENERAL = "일반전화"
    INTERNET = "인터넷전화"

class PurchaseType(str, enum.Enum):
    ONE_OFF = "일시불"
    INSTALLMENT = "할부"

# --- 1. Customer (고객) ---
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, comment="고객명")
    birth_date = Column(String, comment="생년월일(YYYYMMDD)")
    rrn_prefix = Column(String, comment="주민번호 앞자리")
    address = Column(String, comment="설치 주소")
    contact = Column(String, comment="연락처")
    
    # Store as String for SQLite compatibility "YYYY-MM-DD HH:MM:SS"
    # created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    created_at = Column(String, default="2024-01-01 12:00:00")

    applications = relationship("Application", back_populates="customer")

# --- 2. Application Master (신청서 마스터) ---
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(Enum(AppStatus), default=AppStatus.PENDING, index=True)
    
    # Store as String "YYYY-MM-DD"
    # application_date = Column(String, default=lambda: date.today().strftime("%Y-%m-%d"), comment="신청일자")
    application_date = Column(String, default="2024-01-01", comment="신청일자")
    
    # Sales Info (판매정보)
    seller_emp_id = Column(String, nullable=True, comment="판매자 사번")
    agency_code = Column(String, nullable=True, comment="위탁점코드")
    seller_name = Column(String, nullable=True, comment="판매자명")
    seller_contact = Column(String, nullable=True, comment="판매자 연락처")
    recommender = Column(String, nullable=True, comment="추천인")
    tv_joint_sub_serial = Column(String, nullable=True, comment="TV공동청약 일련번호")

    # Financial Summary (for Reporting)
    total_monthly_fee = Column(Integer, default=0, comment="월 예상 납부금 합계")

    customer = relationship("Customer", back_populates="applications")
    
    # One-to-One relationships with services
    internet_svc = relationship("InternetService", back_populates="application", uselist=False)
    tv_svc = relationship("TVService", back_populates="application", uselist=False)
    phone_svc = relationship("PhoneService", back_populates="application", uselist=False)
    device_svc = relationship("DeviceService", back_populates="application", uselist=False)

# --- 3. Services (서비스 상세) ---

class InternetService(Base):
    __tablename__ = "svc_internet"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    
    plan_name = Column(String, comment="요금제")
    speed_category = Column(String, comment="속도구분(100M/500M/1G)") 
    package_wifi = Column(String, comment="패키지/Wifi")
    contract_period = Column(String, comment="약정기간")
    discount_type = Column(String, comment="할인정보")
    install_method = Column(String, comment="설치방법")

    application = relationship("Application", back_populates="internet_svc")

class TVService(Base):
    __tablename__ = "svc_tv"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))

    service_type_1 = Column(String, comment="서비스선택1")
    service_type_2 = Column(String, comment="서비스선택2")
    genie_tv_type = Column(String, comment="GenieTV 셋탑종류")
    contract_period = Column(String, comment="약정기간")
    add_ons = Column(String, comment="부가서비스")
    install_info = Column(String, comment="설치정보")

    application = relationship("Application", back_populates="tv_svc")

class PhoneService(Base):
    __tablename__ = "svc_phone"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))

    phone_type = Column(Enum(PhoneType), comment="전화 구분")
    plan_name = Column(String, comment="요금제")
    contract_period = Column(String, comment="약정기간")
    
    # Common
    desired_number = Column(String, comment="희망번호")
    confirmed_number = Column(String, comment="확정번호")
    add_ons = Column(String, comment="부가서비스")
    directory_listing = Column(String, comment="번호안내 희망")

    # General Phone specific
    install_fee = Column(String, nullable=True, comment="설치비")

    # Internet Phone specific
    install_method = Column(String, nullable=True, comment="설치방법")
    access_internet = Column(String, nullable=True, comment="접속인터넷")

    application = relationship("Application", back_populates="phone_svc")

class DeviceService(Base):
    __tablename__ = "svc_device"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))

    device_model = Column(String, comment="단말종류")
    purchase_type = Column(Enum(PurchaseType), comment="구매형태")
    price = Column(Integer, comment="판매가액")
    payment_method = Column(String, comment="대금결제")
    installment_fee = Column(Integer, comment="할부수수료")
    penalty_subsidy = Column(String, comment="위약금 및 보조금 기준")

    application = relationship("Application", back_populates="device_svc")
