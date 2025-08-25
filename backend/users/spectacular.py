from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class CustomJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Схема аутентификации для CustomJWTAuthentication в drf-spectacular."""
    
    target_class = 'users.authentication.CustomJWTAuthentication'
    name = 'Bearer'  # Имя схемы в OpenAPI
    
    def get_security_definition(self, auto_schema):
        """Возвращает определение безопасности для OpenAPI схемы."""
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix='Bearer',
            bearer_format='JWT'
        )
