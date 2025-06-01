from django.urls import path
from .views import HomeView, register, user_logout
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', register, name='register'),
     path('logout/', user_logout, name='logout')
]