from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()

class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    game = models.ForeignKey('module_catalog.Game', on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2) 
    discount = models.PositiveIntegerField(default=0) 
    activation_key = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = 'История покупок'
        verbose_name_plural = 'Истории покупок'
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.game.title}"