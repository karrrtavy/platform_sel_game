from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import RegistrationForm
from django.contrib.auth import logout, login

# Create your views here.
class HomeView(TemplateView):
    template_name = 'module_shop/home.html'

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_seller = form.cleaned_data['is_seller']
            user.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'module_shop/register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')