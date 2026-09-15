from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base  # <-- เปลี่ยนมาอิมพอร์ต Base จาก database โดยตรง

class Order(Base):  # <-- ใช้ Base ตรงๆ ได้เลย
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone = Column(String)
    amulet_type = Column(String)       # เช่น เหรียญ, รูปหล่อ, พระปิดตา
    frame_material = Column(String)    # เช่น ทองคำ, เงิน, ทองฝังเพชร
    price = Column(Float)
    status = Column(String, default="รอคิวเลี่ยม")  # รอคิว, กำลังเลี่ยม, เสร็จสิ้น, รับพระแล้ว
    created_at = Column(DateTime, default=datetime.utcnow)