# Online Grocery Store API

Converted from the original console/MySQL project to:

- FastAPI
- SQLAlchemy ORM
- SQLite
- Pydantic

## Run

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:api --reload
```

Open:

http://127.0.0.1:8000/docs

## Main API flow

1. GET /products
2. POST /customers
3. POST /cart/{customer_id}/items
4. GET /cart/{customer_id}
5. POST /checkout/{customer_id}
6. GET /customers/{customer_id}/orders
7. GET /orders/{order_id}
