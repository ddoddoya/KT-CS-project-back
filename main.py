from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, database, schemas
from datetime import date

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="KT ERP System")

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "KT ERP Backend is Running"}

# --- Application Submission API ---

@app.post("/api/applications", response_model=schemas.ApplicationResponse)
def create_application(app_data: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    try:
        # 1. Customer Logic
        customer = db.query(models.Customer).filter(
            models.Customer.name == app_data.customer.name,
            models.Customer.rrn_prefix == app_data.customer.rrn_prefix
        ).first()

        if not customer:
            customer = models.Customer(**app_data.customer.model_dump())
            db.add(customer)
            db.flush()

        # 2. Create Application Header
        db_app = models.Application(
            customer_id=customer.id,
            seller_emp_id=app_data.seller_emp_id,
            agency_code=app_data.agency_code,
            seller_name=app_data.seller_name,
            seller_contact=app_data.seller_contact,
            recommender=app_data.recommender,
            tv_joint_sub_serial=app_data.tv_joint_sub_serial,
            status=models.AppStatus.PENDING
        )
        db.add(db_app)
        db.flush()

        # 3. Create Services
        if app_data.internet:
            internet_svc = models.InternetService(
                application_id=db_app.id,
                **app_data.internet.model_dump()
            )
            db.add(internet_svc)

        if app_data.tv:
            tv_svc = models.TVService(
                application_id=db_app.id,
                **app_data.tv.model_dump()
            )
            db.add(tv_svc)

        if app_data.phone:
            phone_svc = models.PhoneService(
                application_id=db_app.id,
                **app_data.phone.model_dump()
            )
            db.add(phone_svc)

        if app_data.device:
            device_svc = models.DeviceService(
                application_id=db_app.id,
                **app_data.device.model_dump()
            )
            db.add(device_svc)

        db.commit()
        db.refresh(db_app)
        
        return schemas.ApplicationResponse(
            id=db_app.id,
            status=db_app.status,
            application_date=db_app.application_date,
            customer_name=customer.name
        )

    except Exception as e:
        db.rollback()
        print(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Dashboard API (Reports) ---

@app.get("/api/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    today_str = date.today().strftime("%Y-%m-%d")
    
    today_count = db.query(models.Application).filter(
        models.Application.application_date == today_str
    ).count()
    
    completed_count = db.query(models.Application).filter(
        models.Application.status == models.AppStatus.COMPLETED
    ).count()
    
    return {
        "today_applications": today_count,
        "month_completed": completed_count,
        "pending_approvals": 5,
        "total_sales_amount": 1500000
    }

@app.get("/api/customers")
def get_customers(db: Session = Depends(get_db)):
    customers = db.query(models.Customer).order_by(models.Customer.id.desc()).limit(50).all()
    
    result = []
    for c in customers:
        result.append({
            "id": str(c.id),
            "name": c.name,
            "phone": c.contact,
            "address": c.address,
            "birthDate": c.birth_date,
            "registeredAt": c.created_at,
            "status": "active"
        })
    return result

@app.get("/api/dashboard/product-mix")
def get_product_mix(db: Session = Depends(get_db)):
    internet_count = db.query(models.InternetService).count()
    tv_count = db.query(models.TVService).count()
    phone_count = db.query(models.PhoneService).count()
    
    return [
        {"name": "인터넷", "value": internet_count},
        {"name": "TV", "value": tv_count},
        {"name": "전화", "value": phone_count},
    ]

# --- Detailed Stats APIs ---

@app.get("/api/stats/internet")
def get_internet_stats(db: Session = Depends(get_db)):
    speed_stats = db.query(
        models.InternetService.speed_category, 
        func.count(models.InternetService.id)
    ).group_by(models.InternetService.speed_category).all()
    
    return {
        "speed_distribution": [{"name": s[0] or "Unknown", "value": s[1]} for s in speed_stats],
        "total_count": db.query(models.InternetService).count()
    }

@app.get("/api/stats/tv")
def get_tv_stats(db: Session = Depends(get_db)):
    type_stats = db.query(
        models.TVService.service_type_1, 
        func.count(models.TVService.id)
    ).group_by(models.TVService.service_type_1).all()
    
    return {
        "type_distribution": [{"name": t[0] or "Unknown", "value": t[1]} for t in type_stats],
        "total_count": db.query(models.TVService).count()
    }

@app.get("/api/stats/phone")
def get_phone_stats(db: Session = Depends(get_db)):
    type_stats = db.query(
        models.PhoneService.phone_type, 
        func.count(models.PhoneService.id)
    ).group_by(models.PhoneService.phone_type).all()
    
    return {
        "type_distribution": [{"name": t[0] or "Unknown", "value": t[1]} for t in type_stats],
        "total_count": db.query(models.PhoneService).count()
    }

# --- Contract List APIs (ERP Tab) ---

@app.get("/api/contracts/internet")
def get_internet_contracts(db: Session = Depends(get_db)):
    # Join with Application and Customer
    contracts = db.query(models.InternetService, models.Application, models.Customer)\
        .join(models.Application, models.InternetService.application_id == models.Application.id)\
        .join(models.Customer, models.Application.customer_id == models.Customer.id)\
        .all()
        
    result = []
    for svc, app, cust in contracts:
        result.append({
            "id": svc.id,
            "customer_name": cust.name,
            "application_date": app.application_date,
            "plan_name": svc.plan_name,
            "speed_category": svc.speed_category,
            "contract_period": svc.contract_period,
            "status": app.status
        })
    return result

@app.get("/api/contracts/tv")
def get_tv_contracts(db: Session = Depends(get_db)):
    contracts = db.query(models.TVService, models.Application, models.Customer)\
        .join(models.Application, models.TVService.application_id == models.Application.id)\
        .join(models.Customer, models.Application.customer_id == models.Customer.id)\
        .all()
        
    result = []
    for svc, app, cust in contracts:
        result.append({
            "id": svc.id,
            "customer_name": cust.name,
            "application_date": app.application_date,
            "service_type": svc.service_type_1,
            "settop_type": svc.genie_tv_type,
            "contract_period": svc.contract_period,
            "status": app.status
        })
    return result

@app.get("/api/contracts/phone")
def get_phone_contracts(db: Session = Depends(get_db)):
    contracts = db.query(models.PhoneService, models.Application, models.Customer)\
        .join(models.Application, models.PhoneService.application_id == models.Application.id)\
        .join(models.Customer, models.Application.customer_id == models.Customer.id)\
        .all()
        
    result = []
    for svc, app, cust in contracts:
        result.append({
            "id": svc.id,
            "customer_name": cust.name,
            "application_date": app.application_date,
            "phone_type": svc.phone_type,
            "plan_name": svc.plan_name,
            "desired_number": svc.desired_number,
            "status": app.status
        })
    return result

@app.get("/api/contracts/device")
def get_device_contracts(db: Session = Depends(get_db)):
    contracts = db.query(models.DeviceService, models.Application, models.Customer)\
        .join(models.Application, models.DeviceService.application_id == models.Application.id)\
        .join(models.Customer, models.Application.customer_id == models.Customer.id)\
        .all()
        
    result = []
    for svc, app, cust in contracts:
        result.append({
            "id": svc.id,
            "customer_name": cust.name,
            "application_date": app.application_date,
            "device_model": svc.device_model,
            "price": svc.price,
            "purchase_type": svc.purchase_type,
            "status": app.status
        })
    return result
