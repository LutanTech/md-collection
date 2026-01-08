from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
from datetime import datetime
import requests
import uuid, json
import os 
from flask_migrate import Migrate

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "31a545ba6763894a4c080c63503a606c")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

def upload_image_to_imgbb(image_file):

    try:

        files = {'image': (image_file.filename, image_file.read(), image_file.content_type)}
        data = {'key': IMGBB_API_KEY}
        response = requests.post(IMGBB_UPLOAD_URL, files=files, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image to ImgBB: {e}")
        return None

class Product(db.Model):
    id = db.Column(db.String(10), primary_key=True, unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    sub_c  = db.Column(db.String(50), nullable=True)
    gender = db.Column(db.String(20), nullable=True, default='Undefined')
    more_images  = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)


    def __repr__(self):
        return f"<Product {self.name}>"

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "discount": self.discount,
            "image": self.image,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "sub_category":self.sub_c,
            "gender":self.gender,
            "more_images":self.more_images,
            "likes":self.likes
        }
class Order(db.Model):
    id = db.Column(db.String(10), primary_key=True, unique=True)
    items = db.Column(db.Text, default=[])
    phone = db.Column(db.String(13))
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":self.id,
            "items":self.items,
            "phone":self.phone,
            "placed_at":self.placed_at
        }
class Requests(db.Model):
    id = db.Column(db.String(10), primary_key=True, unique=True)
    item_name = db.Column(db.Text)
    phone = db.Column(db.String(13))
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":self.id,
            "item":self.item_name,
            "phone":self.phone,
            "placed_at":self.requested_at
        }

# --- API Endpoints ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'jfif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/products', methods=['POST'])
def add_product():
    # Main image check
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected image file"}), 400

    if not allowed_file(image_file.filename):
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400

    imgbb_response = upload_image_to_imgbb(image_file)
    if not imgbb_response or imgbb_response.get('success') is False:
        error_details = imgbb_response.get('error', {}) if imgbb_response else {}
        return jsonify({"error": "Failed to upload image to ImgBB", "details": error_details}), 500

    image_url = imgbb_response['data']['url']

    try:
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        category = request.form['category'].strip().lower()
        sub_c = request.form['subcategory'].strip().lower()
        gender = request.form['gender'].strip().lower()
        price = float(request.form['price'])
        discount = float(request.form.get('discount', 0.0))

        if not (0 <= discount <= 1):
            return jsonify({"error": "Discount must be between 0 and 1 (e.g., 0.2 for 20%)"}), 400
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid number: {e}"}), 400

    more_images = request.files.getlist('more_images')
    more_image_urls = []

    for img in more_images:
        if img and allowed_file(img.filename):
            resp = upload_image_to_imgbb(img)
            if resp and resp.get('success'):
                more_image_urls.append(resp['data']['url'])

    product_id = str(uuid.uuid4())
    new_product = Product(
        id=product_id,
        name=name,
        description=description,
        category=category,
        sub_c=sub_c,
        gender=gender,
        price=price,
        discount=discount,
        image=image_url,
        more_images=json.dumps(more_image_urls),
        uploaded_at=datetime.utcnow()
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        "message": "Product added successfully",
        "product": new_product.to_dict()
    }), 201

@app.route('/api/products/offset-true', methods=['GET'])
def get_products():
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    products = Product.query.order_by(Product.uploaded_at.desc()) \
                            .offset(offset) \
                            .limit(limit) \
                            .all()

    return jsonify([p.to_dict() for p in products]), 200



@app.route('/products/<string:product_id>', methods=['GET'])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        return jsonify(product.to_dict()), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    data = request.form

    if 'image' in request.files and request.files['image'].filename != '':
        image_file = request.files['image']
        if not allowed_file(image_file.filename):
            return jsonify({"error": "Invalid file type for image update"}), 400
        imgbb_response = upload_image_to_imgbb(image_file)
        if not imgbb_response or imgbb_response.get('success') is False:
            error_details = imgbb_response.get('error', {}) if imgbb_response else {}
            return jsonify({"error": "Failed to update image on ImgBB", "details": error_details}), 500
        product.image = imgbb_response['data']['url']

    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.category = data.get('category', product.category)

    if 'price' in data:
        try:
            product.price = float(data['price'])
        except ValueError:
            return jsonify({"error": "Invalid price format"}), 400
    if 'discount' in data:
        try:
            product.discount = float(data['discount'])
        except ValueError:
            return jsonify({"error": "Invalid discount format"}), 400

    db.session.commit()
    return jsonify({"message": "Product updated successfully", "product": product.to_dict()}), 200

@app.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

@app.route('/products/category/<category_name>', methods=['GET'])
def get_products_by_category(category_name):

    filtered_products = Product.query.filter(
        db.func.lower(Product.category) == category_name.lower()
    ).all()
    return jsonify([p.to_dict() for p in filtered_products])

@app.route('/api/categories/all', methods=['GET'])
def get_categories():
    categories = db.session.query(Product.category).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]

    return jsonify({'categories': category_list})

@app.route('/like/<product_id>', methods=['GET'])
def like_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    try:
        product.likes = (product.likes or 0) + 1
        db.session.commit()
        return jsonify({"message": "Liked successfully", "likes": product.likes}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Something went wrong"}), 500

@app.route('/products/trending', methods=['GET'])
def get_trending_products():
    try:
        trending = Product.query.order_by(Product.likes.desc()).limit(10).all()
        result = [{
            "name": p.name,
            "id": p.id,
            "price": p.price,
            "image": p.image,
            "likes": p.likes if p.likes else 0
        } for p in trending]
        return jsonify(result), 200
    except Exception as e:
        print("Trending error:", e)
        return jsonify({"error": "Server error"}), 500

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        data = request.get_json()
        items = json.dumps(data.get("cart", []))
        phone = data.get("phone", "")
        order_id = str(uuid.uuid4())[:8].upper()

        new_order = Order(
            id=order_id,
            items=items,
            phone=phone,
            placed_at=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "Order placed successfully", "order_id": order_id}), 200

    except Exception as e:
        print("Order error:", e)
        return jsonify({"error": "Failed to place order"}), 500

@app.route('/orders/view')
def view_orders():
    orders = Order.query.all()
    return jsonify([o.to_dict() for o in orders])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('created')
    print('running')
    # app.run(debug=True, port=5050)