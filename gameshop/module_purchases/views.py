from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import PurchaseHistory
from django.db.models import Sum, Count

# Create your views here.
class PurchaseHistoryView(LoginRequiredMixin, ListView):
    model = PurchaseHistory
    template_name = 'module_purchases/history.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        return PurchaseHistory.objects.filter(user=self.request.user).select_related('game')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aggregates = PurchaseHistory.objects.filter(user=self.request.user).aggregate(
            total_spent=Sum('price'),
            total_purchases=Count('id'),
        )
        context['total_spent'] = aggregates['total_spent'] or 0
        context['total_purchases'] = aggregates['total_purchases'] or 0
        return context