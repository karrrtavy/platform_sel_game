from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.GameListView.as_view(), name='game_list'),
    path('create/', views.GameCreateView.as_view(), name='game_form'),
    path('<int:pk>/delete/', views.GameDeleteView.as_view(), name='game_delete'),
    path('<int:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('<int:pk>/buy/', views.buy_game, name='buy_game'),
    path('<int:pk>/success/', views.PurchaseSuccessView.as_view(), name='purchase_success'),
    path('<int:pk>/reviews/delete/<int:review_pk>/', views.ReviewDeleteView.as_view(), name='review_delete'),
    path('seller/<str:username>/', views.SellerProfileView.as_view(), name='seller_profile'),
    path('search/', views.GameSearchView.as_view(), name='game_search'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tags/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('featured/', views.FeaturedGamesView.as_view(), name='featured_games'),
    path('favorites/', views.FavoriteGamesView.as_view(), name='favorite_games'),
    path('toggle-favorite/<int:game_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('advanced-search/', views.AdvancedGameSearchView.as_view(), name='advanced_search'),
    path('comment/<int:game_id>/', views.add_comment, name='add_comment'),
    path('reply/<int:review_id>/', views.add_reply, name='add_reply'),
    path('rate-seller/<int:seller_id>/', views.rate_seller, name='rate_seller'),
]