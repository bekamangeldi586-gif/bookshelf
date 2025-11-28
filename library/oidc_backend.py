"""
Custom OIDC Authentication Backend для поддержки Keycloak с дополнительными возможностями.
"""

from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """
    Custom backend для аутентификации через Keycloak OIDC.
    Поддерживает сохранение дополнительной информации пользователя из OIDC claims.
    """

    def create_user(self, claims):
        """
        Переопределяем метод создания пользователя для сохранения дополнительной информации.
        """
        user = super().create_user(claims)
        
        # Сохраняем дополнительные данные из Keycloak
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')
        user.save()
        
        return user

    def update_user(self, user, claims):
        """
        Переопределяем метод обновления пользователя для синхронизации данных из Keycloak.
        """
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email', '')
        user.save()
        
        return user

    def get_userinfo(self, access_token, id_token, payload):
        """
        Получаем информацию о пользователе из ID токена и/или userinfo эндпоинта.
        """
        user_info = super().get_userinfo(access_token, id_token, payload)
        # Не сохраняем сессию здесь — session доступна в request, а этот метод
        # вызывается вне контекста запроса у некоторых реализаций.
        # Сохранение/чтение id_token делается в logout_view из session.
        
        return user_info
