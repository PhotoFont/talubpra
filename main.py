from fastapi import FastAPI, Depends, Form, Request, Response, Cookie, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from PIL import Image
import shutil
import os
import models, database

app = FastAPI(title="TalubPra Management System")

# สร้างตารางฐานข้อมูลอัตโนมัติ
models.Base.metadata.create_all(bind=database.engine)

# ตั้งค่า Template และ Static Files
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)  # ป้องกันปัญหาโฟลเดอร์ database หาย
app.mount("/static", StaticFiles(directory="static"), name="static")

ADMIN_PASSWORD = "21020166"


def process_and_save_image(upload_file: UploadFile, save_dir: str, max_width: int = 1200) -> Optional[str]:
    """ฟังก์ชันช่วยย่อขนาดและบีบอัดภาพก่อนบันทึกลงเซิร์ฟเวอร์"""
    if not upload_file or not upload_file.filename:
        return None
    
    file_location = os.path.join(save_dir, upload_file.filename)
    
    try:
        # เปิดไฟล์ภาพด้วย Pillow
        image = Image.open(upload_file.file)
        
        # แปลงโหมดสีภาพ (เช่น PNG พื้นใส หรือโหมด Palette ให้เป็น RGB เพื่อป้องกัน Error ตอนเซฟเป็น JPG)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # คำนวณสัดส่วนและย่อขนาดเฉพาะกรณีที่รูปภาพกว้างเกิน max_width
        width_percent = (max_width / float(image.size[0]))
        if width_percent < 1.0:
            target_height = int(float(image.size[1]) * float(width_percent))
            image = image.resize((max_width, target_height), Image.Resampling.LANCZOS)
            
        # บันทึกภาพพร้อมบีบอัดคุณภาพ (Quality=85) เพื่อลดขนาดไฟล์
        image.save(file_location, optimize=True, quality=85)
        return upload_file.filename
    except Exception:
        # หากไฟล์ไม่ใช่รูปภาพ หรือเกิดข้อผิดพลาด ให้เซฟไฟล์ต้นฉบับสำรองแทน
        upload_file.file.seek(0)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return upload_file.filename


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
def read_root(
    request: Request, 
    q: Optional[str] = None,  # รองรับรับค่าคำค้นหา
    auth_token: str = Cookie(None), 
    db: Session = Depends(database.get_db)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)
        
    query = db.query(models.Order)
    
    # หากมีการพิมพ์ค้นหา กรองจาก ชื่อลูกค้า, เบอร์โทรศัพท์ หรือประเภทพระ
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            (models.Order.customer_name.ilike(search_filter)) | 
            (models.Order.phone.ilike(search_filter)) |
            (models.Order.amulet_type.ilike(search_filter))
        )
        
    orders = query.order_by(models.Order.id.desc()).all()
    
    return templates.TemplateResponse(request, "index.html", {
        "orders": orders,
        "q": q or ""  # ส่งค่าคำค้นหากลับไปแสดงที่ช่องค้นหา
    })


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
    remarks: Optional[str] = Form(None),  # รองรับรับค่าหมายเหตุตอนสร้างออเดอร์
    order_date: Optional[str] = Form(None),  # รองรับการเลือกวันที่รับพระเข้ามา (เพิ่มข้อมูลย้อนหลังได้)
    before_images: List[UploadFile] = File([]),
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    # จัดการวันที่รับพระ (ถ้าเลือกย้อนหลังมาให้ใช้ค่านั้น ถ้าไม่เลือกให้ใช้วันเวลาปัจจุบัน)
    parsed_order_date = datetime.now()
    if order_date:
        try:
            parsed_order_date = datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError:
            pass

    # วนลูปผ่านฟังก์ชันย่อและบันทึกรูปภาพตอนรับงาน
    saved_filenames = []
    for img in before_images:
        filename = process_and_save_image(img, UPLOAD_DIR)
        if filename:
            saved_filenames.append(filename)

    # รวมชื่อไฟล์ด้วยเครื่องหมายคอมมาเพื่อเก็บลง DB
    images_string = ",".join(saved_filenames) if saved_filenames else None

    new_order = models.Order(
        customer_name=customer_name,
        phone=phone,
        amulet_type=amulet_type,
        frame_material=frame_material,
        price=price,
        remarks=remarks,  # บันทึกหมายเหตุลงฐานข้อมูล
        before_image=images_string,
        status="รอคิวเลี่ยม",
        order_date=parsed_order_date  # บันทึกวันที่รับพระตามที่เลือก (หรือปัจจุบัน)
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
    pickup_date: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),  # รองรับรับค่าหมายเหตุตอนอัปเดตสถานะ
    after_images: List[UploadFile] = File([]),
    db: Session = Depends(database.get_db),
    auth_token: str = Cookie(None)
):
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        order.remarks = remarks  # อัปเดตหมายเหตุ
        
        # จัดการบันทึกวันที่ลูกค้ารับพระกลับ
        if pickup_date:
            try:
                order.pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d")
            except ValueError:
                pass
        else:
            order.pickup_date = None

        # วนลูปผ่านฟังก์ชันย่อและบันทึกรูปภาพตอนงานเสร็จ
        saved_filenames = []
        for img in after_images:
            filename = process_and_save_image(img, UPLOAD_DIR)
            if filename:
                saved_filenames.append(filename)
                
        if saved_filenames:
            order.after_image = ",".join(saved_filenames)
            
        db.commit()
        
    return RedirectResponse(url=f"/order/{order_id}", status_code=303)