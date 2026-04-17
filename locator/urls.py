from django.urls import path
from .views import LocatorView, DatabaseImageView,RecognizeView,CaptionView, ChatView

urlpatterns = [
    path('', LocatorView.as_view(), name='locator'),
    path('db-image/<str:filename>/', DatabaseImageView.as_view()),
    path('recognize/', RecognizeView.as_view(), name='recognize'),
    path('caption/',  CaptionView.as_view(),  name='caption'),   # ← 新增
    path('chat/',     ChatView.as_view(),     name='chat'),
               ]
