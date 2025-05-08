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
    buy_price = Column(Float, nullable=False)               # Giá mua (kiểu số)
    sell_price = Column(Float, nullable=False)              # Giá bán (kiểu số)
    date = Column(Date, nullable=True)                      # Ngày được cập nhật trên web
    time = Column(Time, nullable=True)                      # Giờ cập nhật (nếu có)
    scraped_at = Column(DateTime, default=datetime.utcnow)  # Thời điểm hệ thống lấy dữ liệu

    __table_args__ = (
        Index('ix_gold_type_date', 'gold_type', 'date'),
    )

# Thông tin kết nối
DB_USER = 'root'
DB_PASSWORD = 'baotran'
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'ql_tiemvang'

# Kết nối ban đầu để kiểm tra sự tồn tại của database
try:
    initial_engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}', echo=False)
    inspector = inspect(initial_engine)
    databases = inspector.get_schema_names()

    if DB_NAME not in databases:
        with initial_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            print(f"✅ Cơ sở dữ liệu '{DB_NAME}' đã được tạo thành công.")
    else:
        print(f"✅ Cơ sở dữ liệu '{DB_NAME}' đã tồn tại.")
except Exception as e:
    print("❌ Lỗi khi kết nối hoặc tạo cơ sở dữ liệu:", e)
    exit(1)

# Kết nối lại với cơ sở dữ liệu đã có
engine = create_engine(
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4', echo=False
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

def test_session_connection():
    session = Session()
    try:
        # Kiểm tra kết nối bằng cách đếm số bản ghi
        count = session.query(GoldPrice).count()
        print(f"✅ Kết nối thành công. Hiện có {count} bản ghi trong bảng 'gold_prices'.")
    except Exception as e:
        print("❌ Lỗi khi truy vấn bảng:", e)
    finally:
        session.close()

# Gọi thử
test_session_connection()
