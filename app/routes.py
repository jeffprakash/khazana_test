import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from .models import User, Goal, Portfolio, Asset, PriceHistory
from . import db, bcrypt, cache
from .rate_limiters import user_rate_limit, ip_rate_limit
from flasgger import swag_from

from .admin_decorator import admin_required




api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/', methods=['GET'])
def home():
    return jsonify(message="Welcome to the Financial Planning API")




# Admin Route
@api_blueprint.route('/admin', methods=['GET'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['Admin'],
    'responses': {
        200: {
            'description': 'Welcome, Admin!',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'example': 'Welcome, Admin!'
                    }
                }
            }
        }
    }
})
def admin():
    return jsonify(message="Welcome, Admin!")

# User Authentication
@api_blueprint.route('/register', methods=['POST'])
@ip_rate_limit()
@swag_from({
    'tags': ['Authentication'],
    'parameters': [
        {
            'name': 'user',
            'in': 'body',
            'type': 'object',
            'required': True,
            'properties': {
                'email': {'type': 'string', 'example': 'user@example.com'},
                'password': {'type': 'string', 'example': 'password123'},
                'name': {'type': 'string', 'example': 'John Doe'},
                'dob': {'type': 'string', 'example': '1990-01-01'},
                'monthly_income': {'type': 'number', 'example': 5000.00}
            }
        }
    ],
    'responses': {
        201: {
            'description': 'User registered successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'User registered successfully'}
                }
            }
        }
    }
})
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(email=data['email'], password=hashed_password, name=data['name'], dob=data.get('dob'), monthly_income=data.get('monthly_income'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User registered successfully"), 201

@api_blueprint.route('/login', methods=['POST'])
@ip_rate_limit()
@swag_from({
    'tags': ['Authentication'],
    'parameters': [
        {
            'name': 'credentials',
            'in': 'body',
            'type': 'object',
            'required': True,
            'properties': {
                'email': {'type': 'string', 'example': 'user@example.com'},
                'password': {'type': 'string', 'example': 'password123'}
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string', 'example': 'your_jwt_token'}
                }
            }
        },
        401: {
            'description': 'Invalid credentials'
        }
    }
})
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify(message="Invalid credentials"), 401

# User Profile
@api_blueprint.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
@user_rate_limit()
@swag_from({
    'tags': ['User'],
    'responses': {
        200: {
            'description': 'User profile data',
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'example': 'user@example.com'},
                    'name': {'type': 'string', 'example': 'John Doe'},
                    'dob': {'type': 'string', 'example': '1990-01-01'},
                    'monthly_income': {'type': 'number', 'example': 5000.00}
                }
            }
        },
        400: {
            'description': 'Invalid input data'
        }
    }
})
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if request.method == 'GET':
        return jsonify(email=user.email, name=user.name, dob=user.dob, monthly_income=user.monthly_income), 200

    if request.method == 'PUT':
        data = request.json
        user.name = data.get('name', user.name)
        user.dob = data.get('dob', user.dob)
        user.monthly_income = data.get('monthly_income', user.monthly_income)
        db.session.commit()
        return jsonify(message="Profile updated"), 200

# Financial Goals
@api_blueprint.route('/goals', methods=['POST', 'GET'])
@jwt_required()
@user_rate_limit()
@swag_from({
    'tags': ['Financial Goals'],
    'parameters': [
        {
            'name': 'goal',
            'in': 'body',
            'type': 'object',
            'required': True,
            'properties': {
                'title': {'type': 'string', 'example': 'Retirement Fund'},
                'target_amount': {'type': 'number', 'example': 1000000},
                'current_savings': {'type': 'number', 'example': 200000},
                'target_date': {'type': 'string', 'example': '2030-12-31'}
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Goal created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Goal created'}
                }
            }
        },
        200: {
            'description': 'List of user goals',
            'schema': {
                'type': 'object',
                'properties': {
                    'goals': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'title': {'type': 'string', 'example': 'Retirement Fund'},
                                'target_amount': {'type': 'number', 'example': 1000000},
                                'current_savings': {'type': 'number', 'example': 200000},
                                'target_date': {'type': 'string', 'example': '2030-12-31'}
                            }
                        }
                    },
                    'total': {'type': 'integer', 'example': 1}
                }
            }
        }
    }
})
def goals():
    user_id = get_jwt_identity()

    if request.method == 'POST':
        data = request.json
        new_goal = Goal(user_id=user_id, title=data['title'], target_amount=data['target_amount'], current_savings=data['current_savings'], target_date=data['target_date'])
        db.session.add(new_goal)
        db.session.commit()
        return jsonify(message="Goal created"), 201

    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        goals = Goal.query.filter_by(user_id=user_id).paginate(page, per_page, False)

        return jsonify(goals=[{
            'id': goal.id,
            'title': goal.title,
            'target_amount': goal.target_amount,
            'current_savings': goal.current_savings,
            'target_date': goal.target_date
        } for goal in goals.items], total=goals.total), 200


@api_blueprint.route('/goals/<int:goal_id>', methods=['PUT', 'DELETE'])
@jwt_required()
@user_rate_limit()
@swag_from({
    'tags': ['Financial Goals'],
    'parameters': [
        {
            'name': 'goal',
            'in': 'body',
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'example': 'Updated Goal'},
                'target_amount': {'type': 'number', 'example': 1200000},
                'current_savings': {'type': 'number', 'example': 300000},
                'target_date': {'type': 'string', 'example': '2032-12-31'}
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Goal updated',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Goal updated successfully'}
                }
            }
        },
        404: {
            'description': 'Goal not found'
        }
    }
})
def goal(goal_id):
    user_id = get_jwt_identity()
    goal = Goal.query.filter_by(user_id=user_id, id=goal_id).first()

    if not goal:
        return jsonify(message="Goal not found"), 404

    if request.method == 'PUT':
        data = request.json
        goal.title = data.get('title', goal.title)
        goal.target_amount = data.get('target_amount', goal.target_amount)
        goal.current_savings = data.get('current_savings', goal.current_savings)
        goal.target_date = data.get('target_date', goal.target_date)
        db.session.commit()
        return jsonify(message="Goal updated successfully"), 200

    if request.method == 'DELETE':
        db.session.delete(goal)
        db.session.commit()
        return jsonify(message="Goal deleted successfully"), 200


from flasgger import swag_from

# Portfolio Management - Create Portfolio
@api_blueprint.route('/portfolio', methods=['POST'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Create a new portfolio for the user.',
    'parameters': [
        {
            'name': 'name',
            'in': 'body',
            'required': True,
            'type': 'string',
            'example': 'My Investment Portfolio'
        }
    ],
    'responses': {
        201: {
            'description': 'Portfolio created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {
                        'type': 'string',
                        'example': 'Portfolio created'
                    }
                }
            }
        }
    }
})
def post_portfolio():
    user_id = get_jwt_identity()

    if 'name' not in data or not isinstance(data['name'], str):
        return jsonify(message="Invalid data. 'name' is required and should be a string."), 400

    if request.method == 'POST':
        data = request.json
        new_portfolio = Portfolio(user_id=user_id, name=data['name'])
        db.session.add(new_portfolio)
        db.session.commit()
        return jsonify(message="Portfolio created"), 201

# Portfolio Management - Get User Portfolios
@api_blueprint.route('/portfolio', methods=['GET'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Get all portfolios of the user with pagination.',
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'default': 1,
            'example': 1
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'default': 10,
            'example': 10
        }
    ],
    'responses': {
        200: {
            'description': 'List of portfolios',
            'schema': {
                'type': 'object',
                'properties': {
                    'portfolios': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'name': {'type': 'string', 'example': 'My Investment Portfolio'}
                            }
                        }
                    },
                    'total': {'type': 'integer', 'example': 3}
                }
            }
        }
    }
})
def get_portfolio():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    portfolios = Portfolio.query.filter_by(user_id=user_id).paginate(page, per_page, False)
    return jsonify(portfolios=[{
        'id': portfolio.id,
        'name': portfolio.name
    } for portfolio in portfolios.items], total=portfolios.total), 200

# Portfolio Summary - Total Investments
@api_blueprint.route('/portfolio/summary', methods=['GET'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Get the total amount invested in all portfolios of the user.',
    'responses': {
        200: {
            'description': 'Total investment in portfolios',
            'schema': {
                'type': 'object',
                'properties': {
                    'total_investments': {'type': 'number', 'example': 10000}
                }
            }
        }
    }
})
def portfolio_summary():
    user_id = get_jwt_identity()
    portfolios = Portfolio.query.filter_by(user_id=user_id).all()
    total_investments = 0

    for portfolio in portfolios:
        assets = Asset.query.filter_by(portfolio_id=portfolio.id).all()
        for asset in assets:
            total_investments += asset.amount_invested

    return jsonify(total_investments=total_investments), 200


# Get Assets from Portfolio
@api_blueprint.route('/portfolio/<int:id>/assets', methods=['GET'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Get all assets from a specific portfolio.',
    'responses': {
        200: {
            'description': 'List of assets in the portfolio',
            'schema': {
                'type': 'object',
                'properties': {
                    'assets': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'example': 1},
                                'name': {'type': 'string', 'example': 'Bitcoin'},
                                'type': {'type': 'string', 'example': 'Cryptocurrency'},
                                'amount_invested': {'type': 'number', 'example': 5000},
                                'purchase_date': {'type': 'string', 'example': '2023-10-01'}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_assets_from_portfolio(id):
    user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=id, user_id=user_id).first_or_404()

    assets = Asset.query.filter_by(portfolio_id=portfolio.id).all()
    return jsonify(assets=[{
        'id': asset.id,
        'name': asset.name,
        'type': asset.type,
        'amount_invested': asset.amount_invested,
        'purchase_date': asset.purchase_date
    } for asset in assets]), 200



# Fetch Asset Price
@api_blueprint.route('/asset/<string:asset_name>/price', methods=['GET'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Fetch the current price of a specific asset.',
    'parameters': [
        {
            'name': 'asset_name',
            'in': 'path',
            'required': True,
            'type': 'string',
            'example': 'Bitcoin'
        }
    ],
    'responses': {
        200: {
            'description': 'Price of the asset',
            'schema': {
                'type': 'object',
                'properties': {
                    'asset_name': {'type': 'string', 'example': 'Bitcoin'},
                    'price': {'type': 'number', 'example': 50000}
                }
            }
        },
        404: {
            'description': 'Asset price not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Asset price not found from external API'}
                }
            }
        }
    }
})
def fetch_asset_price(asset_name):
    cache_key = f"asset_price_{asset_name}"

    cached_price = cache.get(cache_key)
    if cached_price:
        return jsonify(asset_name=asset_name, price=cached_price), 200

    price = get_assets_from_portfolio(asset_name)
    
    if price:
        cache.set(cache_key, price, timeout=3600)  

        asset = Asset.query.filter_by(name=asset_name).first()
        
        if asset:
            today = datetime.utcnow().date()
            existing_entry = PriceHistory.query.filter_by(asset_id=asset.id, date=today).first()

            if not existing_entry:
                new_entry = PriceHistory(asset_id=asset.id, date=today, price=price)
                db.session.add(new_entry)
                db.session.commit()

        return jsonify(asset_name=asset_name, price=price), 200

    return jsonify(message="Asset price not found from external API"), 404

# Add Asset to Portfolio
@api_blueprint.route('/portfolio/<int:id>/assets', methods=['POST'])
@jwt_required()
@user_rate_limit() 
@swag_from({
    'description': 'Add a new asset to a portfolio.',
    'parameters': [
        {
            'name': 'name',
            'in': 'body',
            'required': True,
            'type': 'string',
            'example': 'Bitcoin'
        },
        {
            'name': 'type',
            'in': 'body',
            'required': True,
            'type': 'string',
            'example': 'Cryptocurrency'
        },
        {
            'name': 'amount_invested',
            'in': 'body',
            'required': True,
            'type': 'number',
            'example': 5000
        },
        {
            'name': 'purchase_date',
            'in': 'body',
            'required': True,
            'type': 'string',
            'example': '2023-10-01'
        }
    ],
    'responses': {
        201: {
            'description': 'Asset added to the portfolio successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Asset added to portfolio'}
                }
            }
        }
    }
})
def add_asset_to_portfolio(id):
    user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(id=id, user_id=user_id).first_or_404()

    data = request.json
    new_asset = Asset(
        portfolio_id=portfolio.id,
        name=data['name'],
        type=data['type'],
        amount_invested=data['amount_invested'],
        purchase_date=data['purchase_date']
    )
    
    db.session.add(new_asset)
    db.session.commit()

    return jsonify(message="Asset added to portfolio"), 201

