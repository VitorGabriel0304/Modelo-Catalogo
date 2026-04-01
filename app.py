from flask import Flask, request, jsonify, session, render_template
import json, os, uuid, base64, re
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')

# 🔐 Segurança
app.secret_key = os.getenv("SECRET_KEY", "dev_key_change_this")

# ── Paths ─────────────────────────────────────────
BASE = os.path.dirname(__file__)
DB_FILE = os.path.join(BASE, 'db.json')
UPLOAD_DIR = os.path.join(BASE, 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Database (JSON temporário) ────────────────────
def read_db():
    if not os.path.exists(DB_FILE):
        default = {
            "admin": {
                "username": "admin",
                "password": generate_password_hash("admin123")
            },
            "products": []
        }
        write_db(default)
        return default

    with open(DB_FILE) as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Auth decorator ────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Pages ─────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ── Auth ──────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    db = read_db()

    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Dados inválidos'}), 400

    if data['username'] == db['admin']['username'] and \
       check_password_hash(db['admin']['password'], data['password']):
        session['logged_in'] = True
        return jsonify({'ok': True})

    return jsonify({'error': 'Credenciais inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/me')
def me():
    return jsonify({'logged_in': bool(session.get('logged_in'))})

# ── Produtos ──────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    db = read_db()
    category = request.args.get('category')
    products = db['products']

    if category and category != 'all':
        products = [p for p in products if p.get('category') == category]

    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def create_product():
    db = read_db()
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Nome obrigatório'}), 400

    image_url = '/static/uploads/placeholder.png'

    # Upload imagem
    if data.get('image') and data['image'].startswith('data:'):
        match = re.match(r'data:image/(\w+);base64,(.+)', data['image'])
        if match:
            ext = match.group(1)
            raw = base64.b64decode(match.group(2))
            filename = f"{uuid.uuid4().hex}.{ext}"

            with open(os.path.join(UPLOAD_DIR, filename), 'wb') as f:
                f.write(raw)

            image_url = f'/static/uploads/{filename}'

    product = {
        'id': str(uuid.uuid4()),
        'name': data.get('name'),
        'description': data.get('description', ''),
        'price': data.get('price', ''),
        'category': data.get('category', 'outros'),
        'sizes': data.get('sizes', ''),
        'code': data.get('code', ''),
        'image': image_url,
        'created_at': datetime.now().isoformat()
    }

    db['products'].insert(0, product)
    write_db(db)

    return jsonify(product), 201

@app.route('/api/products/<pid>', methods=['PUT'])
@login_required
def update_product(pid):
    db = read_db()
    data = request.get_json()

    for p in db['products']:
        if p['id'] == pid:
            p['name'] = data.get('name', p['name'])
            p['description'] = data.get('description', p['description'])
            p['price'] = data.get('price', p['price'])
            p['category'] = data.get('category', p['category'])
            p['sizes'] = data.get('sizes', p['sizes'])
            p['code'] = data.get('code', p.get('code', ''))

            if data.get('image') and data['image'].startswith('data:'):
                match = re.match(r'data:image/(\w+);base64,(.+)', data['image'])
                if match:
                    ext = match.group(1)
                    raw = base64.b64decode(match.group(2))
                    filename = f"{uuid.uuid4().hex}.{ext}"

                    with open(os.path.join(UPLOAD_DIR, filename), 'wb') as f:
                        f.write(raw)

                    p['image'] = f'/static/uploads/{filename}'

            write_db(db)
            return jsonify(p)

    return jsonify({'error': 'Produto não encontrado'}), 404

@app.route('/api/products/<pid>', methods=['DELETE'])
@login_required
def delete_product(pid):
    db = read_db()
    db['products'] = [p for p in db['products'] if p['id'] != pid]
    write_db(db)
    return jsonify({'ok': True})