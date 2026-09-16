from fastapi import FastAPI, Depends, Form, Request, Response, Cookie, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import shutil
import os
import models, database

app = FastAPI(title="TalubPra Management System")

# สร้างตารางฐานข้อมูลอัตโนมัติ
models.Base.metadata.create_all(bind=database.engine)

# ตั้งค่า Template และ Static Files (สำหรับเข้าถึงรูปภาพผ่าน URL เช่น /static/uploads/xxx.jpg)
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    before_image: UploadFile = File(None), # รับรูปภาพก่อนเลี่ยม
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    # จัดการบันทึกไฟล์รูปก่อนเลี่ยม
    before_image_name = None
    if before_image and before_image.filename:
        # ป้องกันชื่อไฟล์ซ้ำด้วยการต่อ timestamp หรือใช้ชื่อเดิมตรงๆ
        file_location = os.path.join(UPLOAD_DIR, before_image.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(before_image.file, buffer)
        before_image_name = before_image.filename

    new_order = models.Order(
        customer_name=customer_name,
        phone=phone,
        amulet_type=amulet_type,
        frame_material=frame_material,
        price=price,
        before_image=before_image_name,
        status="รอคิวเลี่ยม"
    )
    db.add(new_order)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/update-status/{order_id}")
def update_status(
    order_id: int, 
    status: str = Form(...), 
    after_image: UploadFile = File(None), # รองรับการแนบรูปตอนเปลี่ยนสถานะ (เช่น เลี่ยมเสร็จ)
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        
        # ถ้ามีการอัปโหลดรูปตอนเลี่ยมเสร็จ
        if after_image and after_image.filename:
            file_location = os.path.join(UPLOAD_DIR, after_image.filename)
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(after_image.file, buffer)
            order.after_image = after_image.filename
            
        db.commit()
    return RedirectResponse(url="/", status_code=303)