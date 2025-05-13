from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey,
    text, Date, Time, Index, inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Khởi tạo lớp cơ sở
Base = declarative_base()

# Định nghĩa bảng GoldPrice
class GoldPrice(Base):
    __tablename__ = 'gold_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False)             # SJC / DOJI / PNJ
    gold_type = Column(String(100), nullable=False)         # Loại vàng
    buy_price = Column(String(225), nullable=False)         # Giá mua (kiểu số)
    sell_price = Column(String(225), nullable=False)        # Giá bán (kiểu số)
    date = Column(Date, nullable=True)                      # Ngày được cập nhật trên web
    time = Column(Time, nullable=True)                      # Giờ cập nhật (nếu có)
    scraped_at = Column(DateTime, default=datetime.utcnow)  # Thời điểm hệ thống lấy dữ liệu

    __table_args__ = (
        Index('ix_gold_type_date', 'gold_type', 'date'),
    )

DATABASE_URL = "postgresql+psycopg2://laravel:npg_iy7pRE5rLmtj@ep-odd-lake-a1450ad3.aws-ap-southeast-1.pg.laravel.cloud:5432/main"

# Kết nối PostgreSQL ban đầu để kiểm tra sự tồn tại của database
try:
    initial_engine = create_engine(DATABASE_URL, echo=True)

    with initial_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1"))
        print(f"✅ Kết nối đến PostgreSQL thành công.")
except Exception as e:
    print("❌ Lỗi khi kết nối:", e)
    exit(1)

# Kết nối lại với PostgreSQL đã có
engine = create_engine(
    DATABASE_URL, echo=False
)

# Tạo bảng nếu chưa tồn tại
try:
    inspector = inspect(engine)
    if 'gold_prices' not in inspector.get_table_names():
        Base.metadata.create_all(engine)
        print("✅ Bảng 'gold_prices' đã được tạo thành công.")
    else:
        print("✅ Bảng 'gold_prices' đã tồn tại, không cần tạo lại.")
except Exception as e:
    print("❌ Lỗi khi tạo bảng:", e)
    exit(1)

# Tạo session và đóng sau khi dùng
Session = sessionmaker(bind=engine)
