from django.contrib import admin
from .models import Book, Cart, CartItem


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'year', 'publisher')


class CartItemInline(admin.TabularInline):
	model = CartItem
	extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ('user', 'created_at')
	inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
	list_display = ('cart', 'book', 'quantity', 'added_at')
