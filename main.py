from fastapi import FastAPI, Depends, Form, Request, Response, Cookie, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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
    before_images: List[UploadFile] = File([]), # รองรับการอัปโหลดหลายรูปตอนรับงาน
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    # วนลูปบันทึกไฟล์รูปภาพทั้งหมด
    saved_filenames = []
    for img in before_images:
        if img and img.filename:
            file_location = os.path.join(UPLOAD_DIR, img.filename)
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            saved_filenames.append(img.filename)

    # รวมชื่อไฟล์ด้วยเครื่องหมายคอมมาเพื่อเก็บลง DB
    images_string = ",".join(saved_filenames) if saved_filenames else None

    new_order = models.Order(
        customer_name=customer_name,
        phone=phone,
        amulet_type=amulet_type,
        frame_material=frame_material,
        price=price,
        before_image=images_string,
        status="รอคิวเลี่ยม"
    )
    db.add(new_order)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/order/{order_id}")
def order_detail(
    request: Request, 
    order_id: int, 
    auth_token: str = Cookie(None), 
    db: Session = Depends(database.get_db)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/", status_code=303)
        
    # แปลงสตริงชื่อไฟล์คั่นด้วยคอมมา ให้กลับเป็น List สำหรับใช้วนลูปแสดงรูปใน HTML
    before_images = order.before_image.split(",") if order.before_image else []
    after_images = order.after_image.split(",") if order.after_image else []
    
    return templates.TemplateResponse(request, "order_detail.html", {
        "order": order,
        "before_images": before_images,
        "after_images": after_images
    })

@app.post("/update-status/{order_id}")
def update_status(
    order_id: int, 
    status: str = Form(...), 
    pickup_date: Optional[str] = Form(None), # รับค่าวันที่ลูกค้ารับพระกลับจากฟอร์ม
    after_images: List[UploadFile] = File([]), # รองรับการอัปโหลดหลายรูปตอนงานเสร็จ
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        
        # จัดการบันทึกวันที่ลูกค้ารับพระกลับ (แปลงจาก String 'YYYY-MM-DD' เป็น Datetime)
        if pickup_date:
            try:
                order.pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d")
            except ValueError:
                pass
        else:
            # หากเคลียร์ค่าวันที่ว่างมา สามารถตั้งค่าให้เป็น None ได้
            order.pickup_date = None

        # วนลูปบันทึกรูปภาพตอนเลี่ยมเสร็จ
        saved_filenames = []
        for img in after_images:
            if img and img.filename:
                file_location = os.path.join(UPLOAD_DIR, img.filename)
                with open(file_location, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)
                saved_filenames.append(img.filename)
                
        if saved_filenames:
            order.after_image = ",".join(saved_filenames)
            
        db.commit()
        
    # เปลี่ยนเส้นทางกลับไปที่หน้ารายละเอียดออเดอร์นั้นๆ เพื่อให้เห็นผลลัพธ์ทันที
    return RedirectResponse(url=f"/order/{order_id}", status_code=303)