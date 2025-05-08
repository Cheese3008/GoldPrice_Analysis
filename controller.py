# controller.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import GoldPrice
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# Cấu hình database (chỉ khai báo 1 lần dùng chung)
engine = create_engine('mysql+pymysql://root:baotran@localhost:3306/ql_tiemvang?charset=utf8mb4', echo=False)
Session = sessionmaker(bind=engine)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def crawl_sjc():
    driver = setup_driver()
    url = "https://sjc.com.vn/gia-vang-online"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sjc-table-show-price-online'))
        )
        today = datetime.today().date()
        now_time = datetime.now().time()

        gold_table = driver.find_element(By.CLASS_NAME, 'sjc-table-show-price-online')
        rows = gold_table.find_elements(By.TAG_NAME, 'tr')

        session = Session()
        existing = session.query(GoldPrice).filter(
            GoldPrice.source == 'SJC',
            GoldPrice.date == today
        ).order_by(GoldPrice.scraped_at.desc()).first()

        if existing and (datetime.utcnow() - existing.scraped_at).total_seconds() < 1800:
            session.close()
            driver.quit()
            return {'status': 'not_changed', 'message': '✅ Dữ liệu không thay đổi gần đây.'}

        new_data = []
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) >= 3:
                gold_type = cols[0].text.strip()
                buy_price = cols[1].text.strip()
                sell_price = cols[2].text.strip()

                gold_entry = GoldPrice(
                    source="SJC",
                    gold_type=gold_type,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    date=today,
                    time=now_time,
                    scraped_at=datetime.utcnow()
                )
                session.add(gold_entry)
                new_data.append({
                    'gold_type': gold_type,
                    'gia_mua_vao': buy_price,
                    'gia_ban_ra': sell_price
                })

        session.commit()
        session.close()
        driver.quit()

        return {'status': 'success', 'message': '✅ Đã crawl và lưu dữ liệu SJC.', 'data': new_data}

    except Exception as e:
        driver.quit()
        return {'status': 'error', 'message': f'Lỗi SJC: {e}'}

def crawl_doji():
    driver = setup_driver()
    url = "http://update.giavang.doji.vn/system/doji_92411/92411"
    driver.get(url)

    try:
        date_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'day'))
        ).text.strip()
        date = datetime.strptime(date_text, '%d-%m-%Y').date()

        time_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//em[contains(text(), "giờ")]/following-sibling::span'))
        ).text.strip()
        time_val = datetime.strptime(time_text, '%H:%M:%S').time()

        session = Session()
        existing = session.query(GoldPrice).filter(
            GoldPrice.source == 'DOJI',
            GoldPrice.date == date
        ).order_by(GoldPrice.scraped_at.desc()).first()

        if existing and (datetime.utcnow() - existing.scraped_at).total_seconds() < 1800:
            session.close()
            driver.quit()
            return {'status': 'not_changed', 'message': '✅ Dữ liệu DOJI đã được lấy gần đây.'}

        rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[ng-repeat="bg in bgs"]'))
        )

        new_data = []

        for row in rows:
            try:
                gold_type = row.find_element(By.CSS_SELECTOR, '.table-cell:first-child').text.strip()
                buy_price = row.find_element(By.CSS_SELECTOR, '.table-cell.buy').text.strip()
                sell_price = row.find_element(By.CSS_SELECTOR, '.table-cell.send').text.strip()

                gold_entry = GoldPrice(
                    source="DOJI",
                    gold_type=gold_type,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    date=date,
                    time=time_val,
                    scraped_at=datetime.utcnow()
                )
                session.add(gold_entry)
                new_data.append({
                    'gold_type': gold_type,
                    'gia_mua_vao': buy_price,
                    'gia_ban_ra': sell_price
                })
            except:
                continue

        session.commit()
        session.close()
        driver.quit()

        return {'status': 'success', 'message': '✅ Đã crawl và lưu dữ liệu DOJI.', 'data': new_data}

    except Exception as e:
        driver.quit()
        return {'status': 'error', 'message': f'Lỗi DOJI: {e}'}

def crawl_pnj():
    driver = setup_driver()
    url = "https://www.pnj.com.vn/site/gia-vang"
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table tbody tr'))
        )

        try:
            update_text = driver.find_element(By.CSS_SELECTOR, 'p.text-sm.text-gray-400.mt-1').text
            match = re.search(r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2})', update_text)
            if match:
                date = datetime.strptime(match.group(1), '%d/%m/%Y').date()
                time_val = datetime.strptime(match.group(2), '%H:%M').time()
            else:
                date = datetime.today().date()
                time_val = datetime.now().time()
        except:
            date = datetime.today().date()
            time_val = datetime.now().time()

        rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')

        session = Session()
        existing = session.query(GoldPrice).filter(
            GoldPrice.source == 'PNJ',
            GoldPrice.date == date
        ).order_by(GoldPrice.scraped_at.desc()).first()

        if existing and (datetime.utcnow() - existing.scraped_at).total_seconds() < 1800:
            session.close()
            driver.quit()
            return {'status': 'not_changed', 'message': '✅ Dữ liệu PNJ đã được lấy gần đây.'}

        new_data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) >= 3:
                gold_type = cols[0].text.strip()
                buy_price = cols[1].text.strip()
                sell_price = cols[2].text.strip()

                gold_entry = GoldPrice(
                    source="PNJ",
                    gold_type=gold_type,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    date=date,
                    time=time_val,
                    scraped_at=datetime.utcnow()
                )
                session.add(gold_entry)
                new_data.append({
                    'gold_type': gold_type,
                    'gia_mua_vao': buy_price,
                    'gia_ban_ra': sell_price
                })

        session.commit()
        session.close()
        driver.quit()

        return {'status': 'success', 'message': '✅ Crawl PNJ thành công.', 'data': new_data}

    except Exception as e:
        driver.quit()
        return {'status': 'error', 'message': f'Lỗi khi crawl PNJ: {e}'}
