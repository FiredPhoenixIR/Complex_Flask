from flask import Flask, request, jsonify
from prometheus_client import make_wsgi_app, Counter, Histogram
from prometheus_client.exposition import generate_latest
from prometheus_client.middleware import PrometheusMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Prometheus metrics
app.wsgi_app = PrometheusMiddleware(app.wsgi_app)
request_counter = Counter('api_requests_total', 'Total API Requests')
request_latency = Histogram('api_request_latency_seconds', 'API Request Latency')

# PostgreSQL database configuration
db_url = "postgresql://username:password@localhost:5432/database_name"
engine = create_engine(db_url)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define a model for the database
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# API route to create an item
@app.route('/items', methods=['POST'])
def create_item():
    request_counter.inc()
    with request_latency.time():
        try:
            data = request.get_json()
            new_item = Item(name=data['name'])
            session = Session()
            session.add(new_item)
            session.commit()
            return jsonify({'message': 'Item created successfully'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# API route to get all items
@app.route('/items', methods=['GET'])
def get_items():
    request_counter.inc()
    with request_latency.time():
        try:
            session = Session()
            items = session.query(Item).all()
            items_list = [{'id': item.id, 'name': item.name} for item in items]
            return jsonify({'items': items_list}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Prometheus metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    request_counter.inc()
    return generate_latest(), 200

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)
