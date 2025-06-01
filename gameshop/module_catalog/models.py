from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from module_purchases.models import PurchaseHistory

# Create your models here.
User = get_user_model()

class GameCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = 'Категория игр'
        verbose_name_plural = 'Категории игр'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class GameTag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name = 'Тег игры'
        verbose_name_plural = 'Теги игр'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Game(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='games')
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='game_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    sales_count = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(GameCategory, related_name='games')
    tags = models.ManyToManyField(GameTag, related_name='games', blank=True)
    release_date = models.DateField(null=True, blank=True)
    platform = models.CharField(max_length=50, blank=True)
    system_requirements = models.TextField(blank=True)
    discount = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0, verbose_name='Количество просмотров')
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    def __str__(self):
        return self.title

    def update_sales_count(self):
        self.sales_count = self.purchase_set.count()
        self.save(update_fields=['sales_count'])

    def update_average_rating(self):
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        self.average_rating = round(avg_rating, 2)
        self.save(update_fields=['average_rating'])

    def save(self, *args, **kwargs):
        if self.discount > 0:
            self.discounted_price = self.price * (100 - self.discount) / 100
        else:
            self.discounted_price = None
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        if self.discount > 0 and self.discounted_price:
            return self.discounted_price
        return self.price
    
    @property
    def current_price(self):
        return self.discounted_price if self.discounted_price else self.price

class Purchase(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE) 
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        if not self.key:
            from uuid import uuid4
            self.key = str(uuid4())[:20]

            PurchaseHistory.objects.create(
                user=self.buyer,
                game=self.game,
                price=self.game.current_price,
                original_price=self.game.price,
                discount=self.game.discount,
                activation_key=self.key
            )
            
            self.game.sales_count = self.game.purchase_set.count()
            self.game.save(update_fields=['sales_count'])

        super().save(*args, **kwargs)

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Нормально'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    text = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('game', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв {self.user.username} на {self.game.title} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.game.update_average_rating()
    
    def delete(self, *args, **kwargs):
        game = self.game
        super().delete(*args, **kwargs)
        game.update_average_rating()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game')
        ordering = ['-created_at']

class SellerRating(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('seller', 'rater')
        
    def __str__(self):
        return f"{self.rating}/5 for {self.seller.username} by {self.rater.username}"

class Comment(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Comment by {self.user.username} on {self.game.title}"

class ReviewReply(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='reply')
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Reply to review by {self.seller.username}"