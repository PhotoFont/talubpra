from fastapi import FastAPI, Depends, Form, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, database

app = FastAPI(title="TalubPra Management System")
models.Base.metadata.create_all(bind=database.engine)
templates = Jinja2Templates(directory="templates")

# กำหนดรหัสผ่านผู้ดูแลระบบ
ADMIN_PASSWORD = "21020166"

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
def login(response: Response, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(key="auth_token", value="authenticated", max_age=86400)
        return resp
    return RedirectResponse(url="/login?error=1", status_code=303)

@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(key="auth_token")
    return resp

@app.get("/")
def read_root(request: Request, auth_token: str = Cookie(None), db: Session = Depends(database.get_db)):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)
        
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    return templates.TemplateResponse(request, "index.html", {"orders": orders})

@app.get("/add")
def add_order_page(request: Request, auth_token: str = Cookie(None)):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "add_order.html", {})

@app.post("/add")
def add_order(
    customer_name: str = Form(...),
    phone: str = Form(...),
    amulet_type: str = Form(...),
    frame_material: str = Form(...),
    price: float = Form(...),
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

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
def update_status(
    order_id: int, 
    status: str = Form(...), 
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    return RedirectResponse(url="/", status_code=303)