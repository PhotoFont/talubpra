from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone = Column(String)
    amulet_type = Column(String)       # เช่น เหรียญ, รูปหล่อ, พระปิดตา
    frame_material = Column(String)    # เช่น ทองคำ, เงิน, ทองฝังเพชร
    price = Column(Float)
    status = Column(String, default="รอคิวเลี่ยม")  # รอคิว, กำลังเลี่ยม, เสร็จสิ้น, รับพระแล้ว
    
    # ฟิลด์สำหรับเก็บชื่อไฟล์รูปภาพ (คั่นด้วยเครื่องหมายคอมมา เช่น img1.jpg,img2.jpg)
    before_image = Column(String, nullable=True)
    after_image = Column(String, nullable=True)
    
    # เพิ่มฟิลด์สำหรับเก็บวันที่ลูกค้ารับพระกลับ
    pickup_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)