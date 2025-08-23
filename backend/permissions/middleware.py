import logging
from django.http import JsonResponse
from django.core.cache import cache
from .utils import get_user_permissions

logger = logging.getLogger('permissions')


class PermissionMiddleware:
    """
    Middleware для автоматической проверки прав доступа.
    
    Этот middleware можно использовать для дополнительной логики,
    например, для логирования всех запросов или предварительной проверки.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Логируем запрос (опционально)
        if hasattr(request, 'user') and request.user.is_authenticated:
            logger.info(f"Запрос от пользователя {request.user.email}: {request.method} {request.path}")
        
        # Вызываем следующий middleware/view
        response = self.get_response(request)
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Обрабатывает view перед его выполнением.
        Здесь можно добавить дополнительную логику проверки прав.
        """
        return None


class ResourceOwnerMiddleware:
    """
    Middleware для автоматического определения владельца ресурса.
    
    Этот middleware добавляет owner_id в request для упрощения проверки прав.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Добавляем owner_id в request для упрощения проверки прав
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Для GET запросов можно определить owner_id из query_params
            if request.method == 'GET':
                request.resource_owner_id = request.GET.get('owner_id')
            
            # Для POST/PUT/PATCH запросов можно определить owner_id из data
            elif request.method in ['POST', 'PUT', 'PATCH']:
                request.resource_owner_id = request.data.get('owner_id')
        
        response = self.get_response(request)
        return response