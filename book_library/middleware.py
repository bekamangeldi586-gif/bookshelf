"""
Middleware для поддержки правильного формирования redirect_uri для OIDC.
"""

from urllib.parse import urljoin


class OIDCRedirectURIMiddleware:
    """
    Middleware для корректной обработки redirect_uri при работе с OIDC.
    Добавляет OIDC_RP_CALLBACK_URL_NAME к контексту запроса.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.is_secure():
            scheme = 'https'
        else:
            scheme = 'http'

        host = request.get_host()

        callback_url = f"{scheme}://{host}/oidc/callback/"

        request.oidc_callback_url = callback_url

        response = self.get_response(request)
        return response
