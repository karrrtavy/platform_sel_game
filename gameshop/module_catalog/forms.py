from django import forms
from .models import Game, Review, Comment, ReviewReply, SellerRating

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'description', 'price', 'image', 'categories', 'tags', 
                 'release_date', 'platform', 'system_requirements', 'discount']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'system_requirements': forms.Textarea(attrs={'rows': 4}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте ваш отзыв...'}),
        }
        labels = {
            'text': 'Текст отзыва',
            'rating': 'Оценка',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Оставьте ваш комментарий...'})
        }

class ReviewReplyForm(forms.ModelForm):
    class Meta:
        model = ReviewReply
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ваш ответ на отзыв...'})
        }

class SellerRatingForm(forms.ModelForm):
    class Meta:
        model = SellerRating
        fields = ['rating']