from rest_framework import generics, permissions
from .serializers import UserSerializer,RegisterSerializer
from django.contrib.auth import get_user_model

class MeView(generics.RetrieveAPIView):
    """返回当前登录用户信息"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

User = get_user_model()
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]   # 游客可访问