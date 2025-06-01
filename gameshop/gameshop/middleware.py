from django.utils.deprecation import MiddlewareMixin
from module_catalog.models import Game

class GameViewCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.path.startswith('/catalog/') and request.method == 'GET':
            path_parts = request.path.split('/')
            if len(path_parts) > 2 and path_parts[2].isdigit():
                try:
                    game = Game.objects.get(pk=int(path_parts[2]))
                    game.views_count += 1
                    game.save(update_fields=['views_count'])
                except Game.DoesNotExist:
                    pass
        
        return response