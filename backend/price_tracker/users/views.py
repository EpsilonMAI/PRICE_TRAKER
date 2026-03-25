"""Views для регистрации пользователей и управления профилями."""
from typing import Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, ProfileSerializer


class UserRegistration(APIView):
    """API для регистрации новых пользователей.
    
    Создает пользователя и возвращает JWT токены для авторизации.
    """
    
    def post(self, request: Request) -> Response:
        """Зарегистрировать нового пользователя.
        
        Args:
            request: HTTP запрос с данными пользователя (username, email, password)
            
        Returns:
            Response: Данные пользователя и JWT токены или ошибки валидации
        """
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "user": {
                    "username": user.username,
                    "email": user.email
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GetProfile(generics.RetrieveAPIView):
    """API для получения профиля текущего пользователя.
    
    Возвращает расширенную информацию о пользователе, включая
    данные из связанного UserProfile и статистику отслеживания.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> User:
        """Получить объект текущего пользователя.
        
        Returns:
            User: Текущий авторизованный пользователь
        """
        return self.request.user
            
