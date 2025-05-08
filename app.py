from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from controller import crawl_sjc, crawl_doji, crawl_pnj

app = Flask(__name__)

# Cấu hình Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:baotran@localhost:3306/ql_tiemvang?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Tắt theo dõi thay đổi
db = SQLAlchemy(app)

# Mô hình cơ sở dữ liệu GoldPrice
class GoldPrice(db.Model):
    __tablename__ = 'gold_prices'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    buy_price = db.Column(db.Float)
    sell_price = db.Column(db.Float)
    scraped_at = db.Column(db.DateTime)
    date = db.Column(db.Date)

# Trang chủ - hiển thị dữ liệu gần nhất (với phân trang)
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)  # Lấy số trang từ query params
    per_page = 50  # Số lượng item trên mỗi trang
    gold_data = GoldPrice.query.order_by(GoldPrice.scraped_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('index.html', gold_data=gold_data)


# Hàm chung để lấy dữ liệu theo nguồn (với phân trang)
def get_gold_data_by_source(source, page=1):
    per_page = 50
    data = GoldPrice.query.filter(GoldPrice.source == source).order_by(GoldPrice.scraped_at.desc()).paginate(page, per_page, False)
    return [{
        'ngay': item.date.strftime('%d-%m-%Y'),
        'gia_mua_vao': item.buy_price,
        'gia_ban_ra': item.sell_price
    } for item in data.items]

# API động để lấy dữ liệu theo nguồn (với phân trang)
@app.route('/api/<source>', methods=['GET'])
def get_gold_by_source(source):
    source = source.upper()
    if source not in ['PNJ', 'DOJI', 'SJC']:
        return jsonify({'error': 'Nguồn không hợp lệ'}), 400

    page = request.args.get('page', 1, type=int)  # Lấy số trang từ query params
    return jsonify(get_gold_data_by_source(source, page))

# API crawl theo từng nguồn (POST)
@app.route('/api/crawl/<source>', methods=['POST'])
def crawl_source(source):
    source = source.upper()
    try:
        if source == 'SJC':
            result = crawl_sjc()
        elif source == 'DOJI':
            result = crawl_doji()
        elif source == 'PNJ':
            result = crawl_pnj()
        else:
            return jsonify({'error': 'Nguồn không hợp lệ'}), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# API lấy dữ liệu cho biểu đồ (tối ưu câu truy vấn)
@app.route('/api/chart_data', methods=['GET'])
def chart_data():
    range_type = request.args.get('range', 'day')  # day, week, month
    source_filter = request.args.get('source', None)  # PNJ, DOJI, SJC

    query = GoldPrice.query

    if source_filter:
        query = query.filter(GoldPrice.source == source_filter)

    today = datetime.today()
    if range_type == 'day':
        start_date = today - timedelta(days=1)
    elif range_type == 'week':
        start_date = today - timedelta(days=7)
    elif range_type == 'month':
        start_date = today - timedelta(days=30)
    else:
        return jsonify({'error': 'Invalid range'}), 400

    # Tối ưu câu truy vấn với start_date
    query = query.filter(GoldPrice.scraped_at >= start_date)
    data = query.order_by(GoldPrice.scraped_at).all()

    chart_data = {}
    for item in data:
        label = item.scraped_at.strftime('%d-%m %H:%M')
        if label not in chart_data:
            chart_data[label] = {}
        chart_data[label][item.source] = {
            'buy': item.buy_price,
            'sell': item.sell_price
        }

    labels = sorted(chart_data.keys())
    sources = ['SJC', 'DOJI', 'PNJ']
    datasets = []
    for source in sources:
        buy_data = [chart_data[label].get(source, {}).get('buy') for label in labels]
        sell_data = [chart_data[label].get(source, {}).get('sell') for label in labels]
        datasets.append({
            'label': f'{source} - Mua vào',
            'data': buy_data,
            'borderColor': get_color(source, 'buy'),
            'fill': False
        })
        datasets.append({
            'label': f'{source} - Bán ra',
            'data': sell_data,
            'borderColor': get_color(source, 'sell'),
            'fill': False
        })

    return jsonify({
        'labels': labels,
        'datasets': datasets
    })

def get_color(source, price_type):
    colors = {
        'SJC': {'buy': '#f39c12', 'sell': '#e67e22'},
        'DOJI': {'buy': '#2980b9', 'sell': '#3498db'},
        'PNJ': {'buy': '#27ae60', 'sell': '#2ecc71'}
    }
    return colors.get(source, {}).get(price_type, '#000000')

if __name__ == '__main__':
    app.run(debug=True)
