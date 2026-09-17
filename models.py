from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    phone = Column(String, index=True)
    amulet_type = Column(String)      # เช่น เหรียญ, รูปหล่อ, พระปิดตา
    frame_material = Column(String)    # เช่น ทองคำ, เงิน, ทองฝังเพชร
    price = Column(Float)
    status = Column(String, default="รอคิวเลี่ยม")  # รอคิว, กำลังเลี่ยม, เสร็จสิ้น, รับพระแล้ว
    
    # ช่องสำหรับใส่ข้อความหมายเหตุ / รายละเอียดเพิ่มเติม
    remarks = Column(Text, nullable=True)
    
    # ฟิลด์สำหรับเก็บชื่อไฟล์รูปภาพ (คั่นด้วยเครื่องหมายคอมมา เช่น img1.jpg,img2.jpg)
    before_image = Column(String, nullable=True)
    after_image = Column(String, nullable=True)
    
    # วันที่รับพระเข้ามา (สามารถเลือกวันที่ย้อนหลังได้ หากเว้นว่างจะใช้วันที่ปัจจุบัน)
    order_date = Column(DateTime, default=datetime.now)
    
    # วันที่ลูกค้ารับพระกลับ
    pickup_date = Column(DateTime, nullable=True)
    
    # วันเวลาที่สร้างรายการในระบบ
    created_at = Column(DateTime, default=datetime.now)