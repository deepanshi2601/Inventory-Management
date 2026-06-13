from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models, schemas

# --- Product CRUD ---
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku).first()

def get_products(db: Session):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()

def create_product(db: Session, product: schemas.ProductCreate):
    existing = get_product_by_sku(db, product.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_dict = product_data.model_dump(exclude_unset=True)
    if "sku" in update_dict and update_dict["sku"] != db_product.sku:
        existing = get_product_by_sku(db, update_dict["sku"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{update_dict['sku']}' already exists"
            )
            
    for key, value in update_dict.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    db.delete(db_product)
    db.commit()
    return db_product


# --- Customer CRUD ---
def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()

def get_customers(db: Session):
    return db.query(models.Customer).order_by(models.Customer.id.desc()).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    existing = get_customer_by_email(db, customer.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with email '{customer.email}' already exists"
        )
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer_data: schemas.CustomerUpdate):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
        
    update_dict = customer_data.model_dump(exclude_unset=True)
    if "email" in update_dict and update_dict["email"] != db_customer.email:
        existing = get_customer_by_email(db, update_dict["email"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with email '{update_dict['email']}' already exists"
            )
            
    for key, value in update_dict.items():
        setattr(db_customer, key, value)
        
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    db.delete(db_customer)
    db.commit()
    return db_customer


# --- Order CRUD ---
def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_orders(db: Session):
    return db.query(models.Order).order_by(models.Order.id.desc()).all()

def create_order(db: Session, order_data: schemas.OrderCreate):
    # Check if customer exists
    customer = get_customer(db, order_data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Begin transactional check & stock reduction
    # We will create the Order with 0 total first, then update it
    db_order = models.Order(customer_id=order_data.customer_id, total_amount=0.0)
    db.add(db_order)
    db.flush()  # Generate db_order.id

    total_amount = 0.0
    items_to_add = []

    # Track product reductions to avoid multiple locks/inconsistencies on same product in one order
    product_quantities = {}
    for item in order_data.items:
        product_quantities[item.product_id] = product_quantities.get(item.product_id, 0) + item.quantity

    for product_id, req_quantity in product_quantities.items():
        # Fetch product and lock the row
        product = db.query(models.Product).filter(models.Product.id == product_id).with_for_update().first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {product_id} not found"
            )

        if product.quantity < req_quantity:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. Available: {product.quantity}, Requested: {req_quantity}"
            )

        # Deduct stock
        product.quantity -= req_quantity
        line_total = product.price * req_quantity
        total_amount += line_total

        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=product_id,
            quantity=req_quantity,
            price_at_order=product.price
        )
        items_to_add.append(db_item)

    # Set calculated total amount
    db_order.total_amount = total_amount
    db.add_all(items_to_add)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}"
        )
        
    db.refresh(db_order)
    return db_order

def delete_order(db: Session, order_id: int):
    # Fetch order and lock its rows
    db_order = get_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Restore stock for each item in the order
    for item in db_order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
        if product:
            product.quantity += item.quantity

    db.delete(db_order)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )
