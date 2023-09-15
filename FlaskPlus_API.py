from flask import Flask, request
from flask_restful import Api, Resource, reqparse, abort
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_uploads import configure_uploads, UploadSet, IMAGES

from models import db, User, Item  # You'll need to create the models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['UPLOADED_IMAGES_DEST'] = 'uploads/images'
api = Api(app)
jwt = JWTManager(app)
images = UploadSet('images', IMAGES)
configure_uploads(app, images)

# Initialize the database
db.init_app(app)

# Resource parsers
parser = reqparse.RequestParser()
parser.add_argument('name')
parser.add_argument('description')
parser.add_argument('price', type=float)
parser.add_argument('image', type=str)

# Error handling
def item_not_found(item_id):
    return {"message": f"Item {item_id} not found"}, 404

# Routes
class UserResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Check if the user already exists
        if User.query.filter_by(username=username).first():
            return {"message": "User already exists"}, 400

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return {"message": "User created successfully"}, 201

class ItemResource(Resource):
    @jwt_required
    def get(self, item_id):
        item = Item.query.get(item_id)
        if item:
            return item.serialize(), 200
        return item_not_found(item_id)

    @jwt_required
    def put(self, item_id):
        item = Item.query.get(item_id)
        if not item:
            return item_not_found(item_id)

        data = parser.parse_args()
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)

        db.session.commit()
        return {"message": f"Item {item_id} updated successfully"}, 200

    @jwt_required
    def delete(self, item_id):
        item = Item.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return {"message": f"Item {item_id} deleted successfully"}, 200
        return item_not_found(item_id)

class ItemListResource(Resource):
    @jwt_required
    def get(self):
        items = Item.query.all()
        return [item.serialize() for item in items], 200

    @jwt_required
    def post(self):
        data = parser.parse_args()
        item = Item(**data)
        db.session.add(item)
        db.session.commit()
        return {"message": "Item created successfully", "id": item.id}, 201

class UploadImageResource(Resource):
    @jwt_required
    def post(self):
        user_id = get_jwt_identity()
        image = request.files['image']

        if image:
            image_path = f"images/user_{user_id}_{image.filename}"
            image.save(image_path)
            return {"message": "Image uploaded successfully", "image_url": image_path}, 201
        return {"message": "No image provided"}, 400

api.add_resource(UserResource, '/api/register')
api.add_resource(ItemResource, '/api/items/<int:item_id>')
api.add_resource(ItemListResource, '/api/items')
api.add_resource(UploadImageResource, '/api/upload-image')

if __name__ == '__main__':
    app.run(debug=True)
