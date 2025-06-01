from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class RegistrationForm(UserCreationForm):
    is_seller = forms.BooleanField(required=False, label='Зарегистрироваться как продавец')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'is_seller')