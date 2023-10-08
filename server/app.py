from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from models import User, Recipe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
api = Api(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    _password_hash = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200))
    bio = db.Column(db.String(255))

    recipes = db.relationship('Recipe', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError("Password is not accessible")

    @password.setter
    def password(self, plain_password):
        self._password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, plain_password):
        return bcrypt.check_password_hash(self._password_hash, plain_password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'image_url': self.image_url,
            'bio': self.bio
        }

# Recipe Model
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.String(1000), nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'user': self.user.to_dict()
        }

# Signup, CheckSession, Login, and Logout Resources
class Signup(Resource):
    def post(self):
        json_data = request.get_json()

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=json_data['username']).first()
        if existing_user:
            return {'message': 'Username already taken'}, 422

        user = User(
            username=json_data['username'],
            password=json_data['password'],  # Remember to hash the password in User model
            image_url=json_data['image_url'],
            bio=json_data['bio']
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id  # Log in the user automatically
        return user.to_dict(), 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return user.to_dict(), 200
        else:
            return {'message': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        json_data = request.get_json()
        user = User.query.filter_by(username=json_data['username']).first()

        if user and user.check_password(json_data['password']):
            session['user_id'] = user.id
            return user.to_dict(), 200
        else:
            return {'message': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id')
            return {}, 204
        else:
            return {'message': 'Unauthorized'}, 401

# RecipeIndex Resource
class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        else:
            return {'message': 'Unauthorized'}, 401

    def post(self):
        user_id = session.get('user_id')
        if user_id:
            json_data = request.get_json()
            recipe = Recipe(
                title=json_data['title'],
                instructions=json_data['instructions'],
                minutes_to_complete=json_data['minutes_to_complete'],
                user_id=user_id
            )
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        else:
            return {'message': 'Unauthorized'}, 401

api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
