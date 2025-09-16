from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.shortcuts import redirect

def jwt_required(view_func):
    """
    Decorator to check JWT token in request cookies or Authorization header for template views.
    """
    def wrapper(request, *args, **kwargs):
        auth = JWTAuthentication()
        
        # Try reading from Authorization header first
        header = request.META.get('HTTP_AUTHORIZATION')
        token = None

        if header:
            try:
                token = header.split()[1]
            except IndexError:
                return redirect('/api/login/')
        else:
            # Fallback: check JWT cookie
            token = request.COOKIES.get('jwt')

        if not token:
            return redirect('/api/login/')

        try:
            validated_token = auth.get_validated_token(token)
            request.user = auth.get_user(validated_token)
            return view_func(request, *args, **kwargs)
        except (InvalidToken, TokenError):
            return redirect('/api/login/')
    return wrapper
