from fastapi import FastAPI, Depends, Form, Request, Response, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, database

app = FastAPI(title="TalubPra Management System")
models.Base.metadata.create_all(bind=database.engine)
templates = Jinja2Templates(directory="templates")

# กำหนดรหัสผ่านผู้ดูแลระบบง่ายๆ (สามารถเปลี่ยนได้ตามต้องการ)
ADMIN_PASSWORD = "21020166"

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
def login(response: Response, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/", status_code=303)
        # ตั้งค่า Cookie ยืนยันตัวตน (อายุ 1 วัน)
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
    # เช็คว่า Login หรือยัง ถ้ายังให้เด้งไปหน้า Login
    if auth_token != "authenticated":
        return RedirectResponse(url="/login", status_code=303)
        
    orders = db.query(models.Order).order_by(models.Order.id.desc()).all()
    return templates.TemplateResponse(request, "index.html", {"orders": orders})

# (ฟังก์ชัน /add และ /update-status เดิมของคุณ สามารถใส่การเช็ค auth_token เพิ่มเติมได้ในทำนองเดียวกันครับ)