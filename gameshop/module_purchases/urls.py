from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('history/', views.PurchaseHistoryView.as_view(), name='history'),
]