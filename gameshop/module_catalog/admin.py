from django.contrib import admin
from .models import Game, GameCategory, GameTag

# Register your models here.
admin.site.register(Game)
admin.site.register(GameCategory)
admin.site.register(GameTag)