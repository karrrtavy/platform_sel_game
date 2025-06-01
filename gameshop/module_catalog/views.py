from django.views.generic import ListView, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from .models import Game, Purchase, GameCategory, GameTag, Comment, ReviewReply, SellerRating
from .forms import GameForm, ReviewForm, CommentForm, ReviewReplyForm, SellerRatingForm
from django.views.generic.edit import FormMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Review
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.db.models import Q
from django.views.generic import ListView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Favorite

# Create your views here.
User = get_user_model()

class GameCreateView(LoginRequiredMixin, CreateView):
    model = Game
    form_class = GameForm
    template_name = 'module_catalog/game_form.html'
    success_url = reverse_lazy('catalog:game_list')

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

class GameDeleteView(LoginRequiredMixin, DeleteView):
    model = Game
    template_name = 'module_catalog/game_confirm_delete.html'
    success_url = reverse_lazy('catalog:game_list')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.seller != self.request.user:
            raise PermissionDenied("Вы можете удалять только свои игры")
        return obj
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Игра успешно удалена')
        return super().delete(request, *args, **kwargs)

class GameDetailView(FormMixin, DetailView):
    model = Game
    template_name = 'module_catalog/game_detail.html'
    form_class = ReviewForm
    
    def get_success_url(self):
        return reverse('catalog:game_detail', kwargs={'pk': self.object.pk})
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        review = form.save(commit=False)
        review.game = self.object
        review.user = self.request.user
        review.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.object
        context['reviews'] = game.reviews.all().select_related('user')
        if self.request.user.is_authenticated:
            context['user_review'] = game.reviews.filter(user=self.request.user).first()
            context['has_purchased'] = Purchase.objects.filter(
                game=game,
                buyer=self.request.user
            ).exists()
        context['form'] = self.get_form()
        return context
            
class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'module_catalog/review_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('catalog:game_detail', kwargs={'pk': self.object.game.pk})
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied("Вы не можете удалить этот отзыв")
        return obj
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Отзыв успешно удален')
        return response

def buy_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST' and request.user != game.seller:
        Purchase.objects.create(game=game, buyer=request.user)
        return redirect('catalog:purchase_success', pk=pk)
    return redirect('catalog:game_detail', pk=pk)

class PurchaseSuccessView(DetailView):
    model = Purchase
    template_name = 'module_catalog/purchase_success.html'
    context_object_name = 'purchase'

    def get_object(self):
        game_id = self.kwargs.get('pk')
        return Purchase.objects.filter(
            game_id=game_id, 
            buyer=self.request.user
        ).first()
    
class GameListView(ListView):
    model = Game
    template_name = 'module_catalog/game_list.html'
    context_object_name = 'games'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.GET.get('category')
        sort = self.request.GET.get('sort', '-created_at')
        
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        valid_sorts = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'rating': '-average_rating',
            'popular': '-sales_count'
        }
        sort_field = valid_sorts.get(sort, '-created_at')
        
        return queryset.order_by(sort_field).select_related('seller').prefetch_related('categories', 'tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sort_options'] = [
            ('newest', 'Сначала новые'),
            ('oldest', 'Сначала старые'),
            ('price_asc', 'Цена по возрастанию'),
            ('price_desc', 'Цена по убыванию'),
            ('rating', 'По рейтингу'),
            ('popular', 'По популярности')
        ]
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context
    
class SellerProfileView(DetailView):
    model = User
    template_name = 'module_catalog/seller_profile.html'
    context_object_name = 'seller'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seller = self.object
        
        games = seller.games.all()
        
        total_sales = Purchase.objects.filter(game__seller=seller).count()
        
        avg_game_rating = Review.objects.filter(game__seller=seller).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        seller_rating = seller.ratings.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        context.update({
            'games': games,
            'total_sales': total_sales,
            'avg_game_rating': round(avg_game_rating, 2) if avg_game_rating else None,
            'seller_avg_rating': round(seller_rating, 2) if seller_rating else None,
            'rating_count': seller.ratings.count(),
            'game_count': games.count()
        })
        return context
    
class GameSearchView(ListView):
    model = Game
    template_name = 'module_catalog/game_search.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Game.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(seller__username__icontains=query)
            )
        return Game.objects.none()

class CategoryListView(ListView):
    model = GameCategory
    template_name = 'module_catalog/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    model = GameCategory
    template_name = 'module_catalog/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = self.object.games.all()
        return context

class TagDetailView(DetailView):
    model = GameTag
    template_name = 'module_catalog/tag_detail.html'
    context_object_name = 'tag'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = self.object.games.all()
        return context

class FeaturedGamesView(ListView):
    model = Game
    template_name = 'module_catalog/featured_games.html'
    context_object_name = 'games'
    queryset = Game.objects.filter()

@login_required
@require_POST
def toggle_favorite(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        game=game
    )
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed', 'is_favorite': False})
    
    return JsonResponse({'status': 'added', 'is_favorite': True})

class FavoriteGamesView(LoginRequiredMixin, ListView):
    model = Game
    template_name = 'module_catalog/favorite_games.html'
    context_object_name = 'games'
    paginate_by = 12
    
    def get_queryset(self):
        return Game.objects.filter(
            favorited_by__user=self.request.user
        ).select_related('seller').prefetch_related('categories', 'tags')
    
@login_required
@require_POST
def add_comment(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.game = game
        comment.user = request.user
        comment.save()
        return JsonResponse({
            'success': True,
            'comment': {
                'text': comment.text,
                'username': comment.user.username,
                'date': comment.created_at.strftime("%d.%m.%Y %H:%M")
            }
        })
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
@require_POST
def add_reply(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.game.seller:
        return JsonResponse({'success': False, 'error': 'Только продавец может отвечать на отзывы'})
    
    form = ReviewReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.review = review
        reply.seller = request.user
        reply.save()
        return JsonResponse({
            'success': True,
            'reply': {
                'text': reply.text,
                'username': reply.seller.username,
                'date': reply.created_at.strftime("%d.%m.%Y %H:%M")
            }
        })
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
@require_POST
def rate_seller(request, seller_id):
    seller = get_object_or_404(User, id=seller_id)
    if request.user == seller:
        return JsonResponse({'success': False, 'error': 'Нельзя оценить самого себя'})
    
    form = SellerRatingForm(request.POST)
    if form.is_valid():
        rating, created = SellerRating.objects.update_or_create(
            seller=seller,
            rater=request.user,
            defaults={'rating': form.cleaned_data['rating']}
        )
        return JsonResponse({
            'success': True,
            'rating': rating.rating,
            'average': seller.ratings.aggregate(Avg('rating'))['rating__avg']
        })
    return JsonResponse({'success': False, 'errors': form.errors})

class AdvancedGameSearchView(ListView):
    model = Game
    template_name = 'module_catalog/advanced_search.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        category = self.request.GET.get('category')
        platform = self.request.GET.get('platform')
        sort = self.request.GET.get('sort', '-created_at')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(seller__username__icontains=query)
            )

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if category:
            queryset = queryset.filter(categories__slug=category)
        if platform:
            queryset = queryset.filter(platform__iexact=platform)

        valid_sorts = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_asc': 'price',
            'price_desc': '-price',
            'rating': '-average_rating',
            'popular': '-sales_count',
            'views': '-views_count'
        }
        sort_field = valid_sorts.get(sort, '-created_at')

        return queryset.order_by(sort_field).select_related('seller').prefetch_related('categories', 'tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = GameCategory.objects.all()
        context['platforms'] = Game.objects.values_list('platform', flat=True).distinct().exclude(platform='')
        context['current_query'] = self.request.GET.get('q', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_platform'] = self.request.GET.get('platform', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context