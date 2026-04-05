from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            AuditLog.objects.create(
                user=request.user,
                action=f'{request.method} {request.path}',
                details={'data': dict(request.POST)},
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        return response
