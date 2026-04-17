from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (("user", "普通用户"), ("admin", "管理员"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
