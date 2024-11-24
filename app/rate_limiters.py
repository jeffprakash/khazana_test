from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity

limiter = Limiter(get_remote_address)

def user_rate_limit():
    return limiter.limit("100 per hour", key_func=get_jwt_identity)  
def ip_rate_limit():
    return limiter.limit("10 per minute", key_func=get_remote_address)  
