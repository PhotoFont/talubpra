from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, database

app = FastAPI(title="TalubPra Management System")
models.Base.metadata.create_all(bind=database.engine)
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root(request: Request, db: Session = Depends(database.get_db)):
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "orders": orders})

@app.get("/add")
def add_order_page(request: Request):
    return templates.TemplateResponse("add_order.html", {"request": request})

@app.post("/add")
def add_order(
    customer_name: str = Form(...),
    phone: str = Form(...),
    amulet_type: str = Form(...),
    frame_material: str = Form(...),
    price: float = Form(...),
    db: Session = Depends(database.get_db)
):
    new_order = models.Order(
        customer_name=customer_name,
        phone=phone,
        amulet_type=amulet_type,
        frame_material=frame_material,
        price=price,
        status="รอคิวเลี่ยม"
    )
    db.add(new_order)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/update-status/{order_id}")
def update_status(order_id: int, status: str = Form(...), db: Session = Depends(database.get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return RedirectResponse(url="/", status_code=303)