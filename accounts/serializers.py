from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password')   # 只开放必要字段

    def create(self, validated_data):
        # 使用 Django 自带的 create_user，自动做密码哈希
        return User.objects.create_user(**validated_data)