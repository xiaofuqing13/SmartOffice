"""JWT authentication for the smart-office project."""

import jwt
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def generate_jwt_token(user_id, days=1):
    """Generate JWT token for the given user ID.
    
    Args:
        user_id: The ID of the user.
        days: Number of days until the token expires (default: 1 day).
    
    Returns:
        str: The JWT token as a string.
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=days),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_AUTH['JWT_SECRET_KEY'], algorithm=settings.JWT_AUTH['JWT_ALGORITHM'])


class JWTAuthentication(authentication.BaseAuthentication):
    """JWT authentication backend."""
    
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, token).
        """
        auth_header = authentication.get_authorization_header(request).decode('utf-8')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_AUTH['JWT_SECRET_KEY'], 
                algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
            )
            user_id = payload.get('user_id')
            
            if user_id is None:
                raise AuthenticationFailed('Invalid token payload')
            
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                raise AuthenticationFailed('User inactive or deleted')
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.DecodeError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        
        return None 