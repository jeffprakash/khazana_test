import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from routes import api_blueprint  # Assuming your API Blueprint is called api_blueprint
from app import db, bcrypt  # Assuming app.py holds your app creation logic

# Mock Database Setup
@pytest.fixture(scope='module')
def test_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'secret'
    app.register_blueprint(api_blueprint)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def create_user(client):
    """Fixture for creating a user."""
    data = {
        'email': 'testuser@example.com',
        'password': 'password123',
        'name': 'Test User',
        'dob': '1990-01-01',
        'monthly_income': 5000
    }
    response = client.post('/register', json=data)
    assert response.status_code == 201
    return data


@pytest.fixture
def login(create_user, client):
    """Fixture for logging in and getting JWT token."""
    login_data = {
        'email': create_user['email'],
        'password': create_user['password']
    }
    response = client.post('/login', json=login_data)
    assert response.status_code == 200
    return response.json['access_token']


# Example Test Cases

def test_register(client):
    data = {
        'email': 'newuser@example.com',
        'password': 'password123',
        'name': 'New User',
        'dob': '1995-05-15',
        'monthly_income': 4000
    }
    response = client.post('/register', json=data)
    assert response.status_code == 201
    assert response.json['message'] == "User registered successfully"


def test_login(client, create_user):
    data = {
        'email': create_user['email'],
        'password': create_user['password']
    }
    response = client.post('/login', json=data)
    assert response.status_code == 200
    assert 'access_token' in response.json


def test_profile_get(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    response = client.get('/profile', headers=headers)
    assert response.status_code == 200
    assert response.json['email'] == 'testuser@example.com'


def test_profile_put(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    data = {
        'name': 'Updated User',
        'dob': '1995-01-01',
        'monthly_income': 6000
    }
    response = client.put('/profile', json=data, headers=headers)
    assert response.status_code == 200
    assert response.json['message'] == "Profile updated"


def test_goals_create(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    data = {
        'title': 'Save for Vacation',
        'target_amount': 10000,
        'current_savings': 2000,
        'target_date': '2025-01-01'
    }
    response = client.post('/goals', json=data, headers=headers)
    assert response.status_code == 201
    assert response.json['message'] == "Goal created"


def test_goals_get(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    response = client.get('/goals', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json['goals'], list)


def test_goals_update(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    goal_data = {
        'title': 'Save for Car',
        'target_amount': 15000,
        'current_savings': 5000,
        'target_date': '2025-06-01'
    }
    # Create a goal first
    response = client.post('/goals', json=goal_data, headers=headers)
    goal_id = response.json['goal_id']

    # Update the goal
    updated_data = {
        'title': 'Save for Car - Updated',
        'target_amount': 20000,
        'current_savings': 7000,
        'target_date': '2025-12-01'
    }
    response = client.put(f'/goals/{goal_id}', json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json['message'] == "Goal updated"


def test_portfolio_create(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    data = {
        'name': 'Retirement Fund'
    }
    response = client.post('/portfolio', json=data, headers=headers)
    assert response.status_code == 201
    assert response.json['message'] == "Portfolio created"


def test_portfolio_get(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    response = client.get('/portfolio', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json['portfolios'], list)


def test_add_bitcoin_to_portfolio(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    # First create a portfolio
    portfolio_data = {
        'name': 'Crypto Portfolio'
    }
    response = client.post('/portfolio', json=portfolio_data, headers=headers)
    portfolio_id = response.json['portfolio_id']

    # Add bitcoin to the portfolio
    bitcoin_data = {
        'name': 'Bitcoin',
        'type': 'Cryptocurrency',
        'amount_invested': 1.5,  # Amount in BTC
        'purchase_date': '2023-01-01'
    }
    response = client.post(f'/portfolio/{portfolio_id}/bitcoin', json=bitcoin_data, headers=headers)
    assert response.status_code == 201
    assert response.json['message'] == "Bitcoin added to portfolio"


def test_get_bitcoin_from_portfolio(client, login):
    headers = {
        'Authorization': f'Bearer {login}'
    }
    # First create a portfolio and add bitcoin
    portfolio_data = {
        'name': 'Blockchain Portfolio'
    }
    response = client.post('/portfolio', json=portfolio_data, headers=headers)
    portfolio_id = response.json['portfolio_id']
    
    bitcoin_data = {
        'name': 'Bitcoin',
        'type': 'Cryptocurrency',
        'amount_invested': 2.0,  # Amount in BTC
        'purchase_date': '2023-06-01'
    }
    response = client.post(f'/portfolio/{portfolio_id}/bitcoin', json=bitcoin_data, headers=headers)
    
    response = client.get(f'/portfolio/{portfolio_id}/bitcoin', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json['bitcoins'], list)
    assert len(response.json['bitcoins']) > 0
