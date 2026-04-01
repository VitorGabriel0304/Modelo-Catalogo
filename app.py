from flask import Flask, request, jsonify, send_from_directory, session
import json, os, uuid, base64, hashlib, re
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'sapatos_secret_2024_change_in_production'

# ── Paths ──────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(__file__)
DB_FILE   = os.path.join(BASE, 'db.json')
UPLOAD_DIR = os.path.join(BASE, 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Tiny JSON "database" ───────────────────────────────────────────────────
def read_db():
    if not os.path.exists(DB_FILE):
        default = {
            "admin": {"username": "admin", "password": hashlib.sha256(b"admin123").hexdigest()},
            "products": []
        }
        write_db(default)
        return default
    with open(DB_FILE) as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── Auth decorator ─────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Static pages ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('templates', 'admin.html')

@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ── Auth endpoints ─────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    db   = read_db()
    pw   = hashlib.sha256(data.get('password','').encode()).hexdigest()
    if data.get('username') == db['admin']['username'] and pw == db['admin']['password']:
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

# ── Product endpoints ──────────────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    db = read_db()
    category = request.args.get('category')
    products  = db['products']
    if category and category != 'all':
        products = [p for p in products if p.get('category') == category]
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def create_product():
    db   = read_db()
    data = request.get_json()

    # Save base64 image
    image_url = '/static/uploads/placeholder.png'
    if data.get('image'):
        match = re.match(r'data:image/(\w+);base64,(.+)', data['image'])
        if match:
            ext      = match.group(1)
            raw      = base64.b64decode(match.group(2))
            filename = f"{uuid.uuid4().hex}.{ext}"
            with open(os.path.join(UPLOAD_DIR, filename), 'wb') as f:
                f.write(raw)
            image_url = f'/static/uploads/{filename}'

    product = {
        'id':          str(uuid.uuid4()),
        'name':        data.get('name', ''),
        'description': data.get('description', ''),
        'price':       data.get('price', ''),
        'category':    data.get('category', 'outros'),
        'sizes':       data.get('sizes', ''),
        'image':       image_url,
        'created_at':  datetime.now().isoformat()
    }
    db['products'].insert(0, product)
    write_db(db)
    return jsonify(product), 201

@app.route('/api/products/<pid>', methods=['PUT'])
@login_required
def update_product(pid):
    db   = read_db()
    data = request.get_json()
    for p in db['products']:
        if p['id'] == pid:
            p['name']        = data.get('name', p['name'])
            p['description'] = data.get('description', p['description'])
            p['price']       = data.get('price', p['price'])
            p['category']    = data.get('category', p['category'])
            p['sizes']       = data.get('sizes', p['sizes'])
            if data.get('image') and data['image'].startswith('data:'):
                match = re.match(r'data:image/(\w+);base64,(.+)', data['image'])
                if match:
                    ext      = match.group(1)
                    raw      = base64.b64decode(match.group(2))
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
