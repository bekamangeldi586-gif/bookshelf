from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Book
from .forms import BookForm
from translatepy import Translator
import requests
from django.conf import settings

translator = Translator()

def get_lang(request):
    """Получить язык из GET параметра"""
    return request.GET.get('lang', 'ru')

def index(request):
    books = Book.objects.all()
    lang = get_lang(request)

    # Поддержка kazakh в translatepy
    target_lang = lang
    if lang == 'kz':
        target_lang = 'kk'

    if target_lang != 'ru':
        for book in books:
            book.title = translator.translate(book.title, target_lang).result
            book.author = translator.translate(book.author, target_lang).result
            book.description = translator.translate(book.description, target_lang).result

    return render(request, 'library/index.html', {'books': books, 'lang': lang})

def register_view(request):
    lang = get_lang(request)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f'/login/?lang={lang}')
    else:
        form = UserCreationForm()
    return render(request, 'library/register.html', {'form': form, 'lang': lang})

def login_view(request):
    lang = get_lang(request)
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(f'/?lang={lang}')
    return render(request, 'library/login.html', {'form': form, 'lang': lang})

@login_required
def logout_view(request):
    """Logout с поддержкой OIDC"""
    lang = get_lang(request)
    
    # Получаем ID токена из сессии OIDC если он есть
    id_token = request.session.get('oidc_id_token')
    
    logout(request)
    
    # Если пользователь вошел через OIDC, отправляем его на logout эндпоинт Keycloak
    if id_token:
        logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
        post_logout_redirect_uri = request.build_absolute_uri('/')
        return redirect(f"{logout_url}?post_logout_redirect_uri={post_logout_redirect_uri}")
    
    return redirect(f'/login/?lang={lang}')

@login_required
def add_book(request):
    lang = get_lang(request)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')  # после сохранения переходим на главную
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {'form': form, 'lang': lang})

@login_required
def edit_book(request, pk):
    lang = get_lang(request)
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect(f'/?lang={lang}')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'lang': lang})

@login_required
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return redirect('index')

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    lang = get_lang(request)

    target_lang = lang
    if lang == 'kz':
        target_lang = 'kk'

    title = book.title
    author = book.author
    description = book.description

    if target_lang != 'ru':
        title = translator.translate(title, target_lang).result
        author = translator.translate(author, target_lang).result
        description = translator.translate(description, target_lang).result

    return JsonResponse({
        'title': title,
        'author': author,
        'year': book.year,
        'publisher': book.publisher,
        'description': description,
        'cover_url': book.cover.url if book.cover else ''
    })
