from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from library import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stat/', views.stat_page, name='stat_page'),
    path('stat/itemuse', views.itemuse_json, name='itemuse_json'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('book/add/', views.add_book, name='add_book'),
    path('book/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('book/<int:pk>/delete/', views.delete_book, name='delete_book'),
    path('book/<int:pk>/detail/', views.book_detail, name='book_detail'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('manage/users/', views.admin_users_list, name='admin_users_list'),
    path('manage/user/<int:user_id>/cart/', views.admin_user_cart, name='admin_user_cart'),
    path('manage/user/<int:user_id>/promote/', views.admin_promote_user, name='admin_promote_user'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
