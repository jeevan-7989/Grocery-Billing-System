from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query

from database import Base, LocalSession, engine

from models import (
    Product,
    Customer,
    Order,
    OrderItem,
    CartItem
)

from schemas import (
    CustomerCreate,
    CustomerResponse,
    ProductResponse,
    CartItemCreate,
    CartResponse,
    CartItemResponse,
    OrderResponse,
    OrderDetailsResponse,
    OrderItemResponse
)


api = FastAPI(
    title="Online Grocery Store API",
   # description="Grocery Store using FastAPI + SQLAlchemy + SQLite",
    version="1.0.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


# =========================================================
# HOME
# =========================================================

@api.get("/")
def home():

    return {
        "message": "Online Grocery Store API is running"
    }


# =========================================================
# PRODUCTS
# =========================================================

@api.get(
    "/products",
    response_model=list[ProductResponse]
)
def show_products():

    db = LocalSession()

    products = db.query(Product).order_by(
        Product.product_id
    ).all()

    db.close()

    return products


# =========================================================
# GET PRODUCT BY ID
# =========================================================

@api.get(
    "/products/{product_id}",
    response_model=ProductResponse
)
def get_product(product_id: int):

    db = LocalSession()

    product = db.query(Product).filter(
        Product.product_id == product_id
    ).first()

    db.close()

    if product is None:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =========================================================
# SEARCH PRODUCTS
# =========================================================

@api.get(
    "/products/search",
    response_model=list[ProductResponse]
)
def search_products(
    keyword: str = Query(min_length=1)
):

    db = LocalSession()

    products = db.query(Product).filter(
        Product.product_name.ilike(
            f"%{keyword}%"
        )
    ).order_by(
        Product.product_name
    ).all()

    db.close()

    return products


# =========================================================
# CREATE CUSTOMER
# =========================================================

@api.post(
    "/customers",
    response_model=CustomerResponse
)
def add_customer(request: CustomerCreate):

    db = LocalSession()

    existing_customer = db.query(Customer).filter(
        Customer.email == request.email
    ).first()

    if existing_customer:

        db.close()

        return existing_customer

    customer = Customer(
        customer_name=request.customer_name,
        email=request.email,
        phone=request.phone
    )

    db.add(customer)

    db.commit()

    db.refresh(customer)

    db.close()

    return customer


# =========================================================
# GET CUSTOMER
# =========================================================

@api.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse
)
def get_customer(customer_id: int):

    db = LocalSession()

    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()

    db.close()

    if customer is None:

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


# =========================================================
# ADD PRODUCT TO CART
# =========================================================

@api.post(
    "/cart/{customer_id}/items",
    response_model=CartResponse
)
def add_to_cart(
    customer_id: int,
    request: CartItemCreate
):

    db = LocalSession()

    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()

    if customer is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    product = db.query(Product).filter(
        Product.product_id == request.product_id
    ).first()

    if product is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    if request.quantity > product.stock:

        db.close()

        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock} items are available"
        )


    cart_item = db.query(CartItem).filter(
        CartItem.customer_id == customer_id,
        CartItem.product_id == request.product_id
    ).first()


    if cart_item:

        new_quantity = (
            cart_item.quantity +
            request.quantity
        )

        if new_quantity > product.stock:

            db.close()

            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock} items are available"
            )

        cart_item.quantity = new_quantity


    else:

        cart_item = CartItem(
            customer_id=customer_id,
            product_id=request.product_id,
            quantity=request.quantity
        )

        db.add(cart_item)


    db.commit()

    db.close()

    return view_cart(customer_id)


# =========================================================
# VIEW CART
# =========================================================

@api.get(
    "/cart/{customer_id}",
    response_model=CartResponse
)
def view_cart(customer_id: int):

    db = LocalSession()

    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()

    if customer is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    cart_items = db.query(CartItem).filter(
        CartItem.customer_id == customer_id
    ).all()


    items = []

    total = Decimal("0.00")


    for cart_item in cart_items:

        product = db.query(Product).filter(
            Product.product_id == cart_item.product_id
        ).first()

        subtotal = (
            Decimal(str(product.price))
            * cart_item.quantity
        )

        total += subtotal


        items.append(
            CartItemResponse(
                product_id=product.product_id,
                product_name=product.product_name,
                price=float(product.price),
                quantity=cart_item.quantity,
                subtotal=float(subtotal)
            )
        )


    db.close()


    return CartResponse(
        customer_id=customer_id,
        items=items,
        total_amount=float(total)
    )


# =========================================================
# DELETE CART ITEM
# =========================================================

@api.delete(
    "/cart/{customer_id}/items/{product_id}"
)
def remove_cart_item(
    customer_id: int,
    product_id: int
):

    db = LocalSession()

    cart_item = db.query(CartItem).filter(
        CartItem.customer_id == customer_id,
        CartItem.product_id == product_id
    ).first()


    if cart_item is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )


    db.delete(cart_item)

    db.commit()

    db.close()


    return {
        "message": "Item removed from cart"
    }


# =========================================================
# CHECKOUT
# =========================================================

@api.post(
    "/checkout/{customer_id}",
    response_model=OrderDetailsResponse
)
def checkout(customer_id: int):

    db = LocalSession()


    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()


    if customer is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    cart_items = db.query(CartItem).filter(
        CartItem.customer_id == customer_id
    ).all()


    if not cart_items:

        db.close()

        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )


    total = Decimal("0.00")

    response_items = []


    for cart_item in cart_items:

        product = db.query(Product).filter(
            Product.product_id == cart_item.product_id
        ).first()


        if cart_item.quantity > product.stock:

            db.close()

            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.product_name}"
            )


        price = Decimal(
            str(product.price)
        )

        subtotal = (
            price *
            cart_item.quantity
        )

        total += subtotal


        response_items.append(
            OrderItemResponse(
                product_id=product.product_id,
                product_name=product.product_name,
                quantity=cart_item.quantity,
                price=float(price),
                subtotal=float(subtotal)
            )
        )


    # Create order

    order = Order(
        customer_id=customer_id,
        total_amount=total
    )

    db.add(order)

    db.commit()

    db.refresh(order)


    # Create order items

    for cart_item in cart_items:

        product = db.query(Product).filter(
            Product.product_id == cart_item.product_id
        ).first()


        order_item = OrderItem(
            order_id=order.order_id,
            product_id=product.product_id,
            quantity=cart_item.quantity,
            price=product.price
        )

        db.add(order_item)


        # Reduce stock

        product.stock -= cart_item.quantity


        # Remove cart item

        db.delete(cart_item)


    db.commit()

    db.refresh(order)

    db.close()


    return OrderDetailsResponse(
        order_id=order.order_id,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=float(order.total_amount),
        items=response_items
    )


# =========================================================
# ORDER HISTORY
# =========================================================

@api.get(
    "/customers/{customer_id}/orders",
    response_model=list[OrderResponse]
)
def order_history(customer_id: int):

    db = LocalSession()


    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()


    if customer is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    orders = db.query(Order).filter(
        Order.customer_id == customer_id
    ).order_by(
        Order.order_date.desc()
    ).all()


    db.close()


    return orders


# =========================================================
# ORDER DETAILS
# =========================================================

@api.get(
    "/orders/{order_id}",
    response_model=OrderDetailsResponse
)
def order_details(order_id: int):

    db = LocalSession()


    order = db.query(Order).filter(
        Order.order_id == order_id
    ).first()


    if order is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order_id
    ).all()


    items = []


    for item in order_items:

        product = db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()


        subtotal = (
            Decimal(str(item.price))
            * item.quantity
        )


        items.append(
            OrderItemResponse(
                product_id=product.product_id,
                product_name=product.product_name,
                quantity=item.quantity,
                price=float(item.price),
                subtotal=float(subtotal)
            )
        )


    db.close()


    return OrderDetailsResponse(
        order_id=order.order_id,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=float(order.total_amount),
        items=items
    )