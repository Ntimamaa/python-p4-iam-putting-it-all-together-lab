from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})
db = SQLAlchemy(metadata=metadata)

migrate = Migrate(app, db)
db.init_app(app)

bcrypt = Bcrypt(app)

api = Api(app)

# Define the Recipe model with the requested features
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.String(1000), nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    is_member_only = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'is_member_only': self.is_member_only
        }

# Define a Recipe resource for CRUD operations
class RecipeResource(Resource):
    def get(self, recipe_id):
        # Retrieve a recipe by ID and return it as JSON
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            return recipe.to_dict(), 200
        return {'message': 'Recipe not found'}, 404

    def put(self, recipe_id):
        # Update a recipe by ID and return the updated recipe as JSON
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str, required=True)
        parser.add_argument('instructions', type=str, required=True)
        parser.add_argument('minutes_to_complete', type=int, required=True)
        parser.add_argument('is_member_only', type=bool, required=False)
        args = parser.parse_args()
        
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            recipe.title = args['title']
            recipe.instructions = args['instructions']
            recipe.minutes_to_complete = args['minutes_to_complete']
            if 'is_member_only' in args:
                recipe.is_member_only = args['is_member_only']
            db.session.commit()
            return recipe.to_dict(), 200
        return {'message': 'Recipe not found'}, 404

    def delete(self, recipe_id):
        # Delete a recipe by ID and return a success message
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            db.session.delete(recipe)
            db.session.commit()
            return {'message': 'Recipe deleted successfully'}, 204
        return {'message': 'Recipe not found'}, 404

api.add_resource(RecipeResource, '/recipes/<int:recipe_id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
