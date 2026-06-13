from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.config import settings
from app.db import Base, engine, get_db
from app import crud, schemas, models

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory & Order Management System API",
    description="Backend API for managing products, customers, and orders.",
    version="1.0.0"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dashboard API ---
@app.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_products = db.query(models.Product).count()
    total_customers = db.query(models.Customer).count()
    total_orders = db.query(models.Order).count()
    
    # Low stock definition: quantity < 10
    low_stock_products = db.query(models.Product).filter(models.Product.quantity < 10).all()
    
    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "low_stock_products": [schemas.ProductOut.model_validate(p) for p in low_stock_products]
    }


# --- Products APIs ---
@app.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)

@app.get("/products", response_model=List[schemas.ProductOut])
def get_products(db: Session = Depends(get_db)):
    return crud.get_products(db)

@app.get("/products/{id}", response_model=schemas.ProductOut)
def get_product(id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return db_product

@app.put("/products/{id}", response_model=schemas.ProductOut)
def update_product(id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    return crud.update_product(db, id, product)

@app.delete("/products/{id}", response_model=schemas.ProductOut)
def delete_product(id: int, db: Session = Depends(get_db)):
    return crud.delete_product(db, id)


# --- Customers APIs ---
@app.post("/customers", response_model=schemas.CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)

@app.get("/customers", response_model=List[schemas.CustomerOut])
def get_customers(db: Session = Depends(get_db)):
    return crud.get_customers(db)

@app.get("/customers/{id}", response_model=schemas.CustomerOut)
def get_customer(id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return db_customer

@app.delete("/customers/{id}", response_model=schemas.CustomerOut)
def delete_customer(id: int, db: Session = Depends(get_db)):
    return crud.delete_customer(db, id)


# --- Orders APIs ---
@app.post("/orders", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db, order)

@app.get("/orders", response_model=List[schemas.OrderOut])
def get_orders(db: Session = Depends(get_db)):
    return crud.get_orders(db)

@app.get("/orders/{id}", response_model=schemas.OrderOut)
def get_order(id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return db_order

@app.delete("/orders/{id}")
def delete_order(id: int, db: Session = Depends(get_db)):
    crud.delete_order(db, id)
    return {"message": "Order deleted successfully"}
