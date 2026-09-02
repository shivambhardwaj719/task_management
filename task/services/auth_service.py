from django.contrib.auth.models import User
from task.utils.response.messages import ResponseMessages
from django.contrib.auth import authenticate, login, logout


class AuthService:
    @staticmethod
    def register_user(request, username, password, email="", first_name="", last_name=""):
        if not username or not password:
            return False, ResponseMessages.VALIDATION_ERROR

        if User.objects.filter(username=username).exists():
            return False, ResponseMessages.BAD_REQUEST

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        login(request, user)
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        return True, ResponseMessages.USER_REGISTERED, user_data

    @staticmethod
    def login_user(request, username, password):
        if not username or not password:
            return False, ResponseMessages.VALIDATION_ERROR

        user = authenticate(request, username=username, password=password)
        if user is None:
            return False, ResponseMessages.UNAUTHORIZED, ResponseMessages.INVALID_CREDENTIALS

        login(request, user)
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        return True, ResponseMessages.USER_LOGGED_IN, user_data

    @staticmethod
    def logout_user(request):
        logout(request)
        return True, ResponseMessages.USER_LOGGED_OUT, None

    @staticmethod
    def get_current_user_data(user):
        if not user.is_authenticated:
            return False, ResponseMessages.UNAUTHORIZED

        return True, ResponseMessages.SUCCESS, {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }

    @staticmethod
    def list_all_users():
        users = User.objects.values("id", "username", "email", "first_name", "last_name")
        return list(users)
