from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity

# Initialize the rate limiter
limiter = Limiter(get_remote_address)

# User-based rate limit decorator for authenticated users
def user_rate_limit():
    return limiter.limit("100 per hour", key_func=get_jwt_identity)  # 100 requests per hour for authenticated users

# IP-based rate limit decorator for unauthenticated endpoints
def ip_rate_limit():
    return limiter.limit("10 per minute", key_func=get_remote_address)  # 10 requests per minute for unauthenticated users
