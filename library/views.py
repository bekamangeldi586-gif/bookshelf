from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Book
from .forms import BookForm
from translatepy import Translator

translator = Translator()

def index(request):
    books = Book.objects.all()
    lang = request.GET.get('lang', 'ru')

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
    lang = request.GET.get('lang', 'ru')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f'/login/?lang={lang}')
    else:
        form = UserCreationForm()
    return render(request, 'library/register.html', {'form': form, 'lang': lang})

def login_view(request):
    lang = request.GET.get('lang', 'ru')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(f'/?lang={lang}')
    return render(request, 'library/login.html', {'form': form, 'lang': lang})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_book(request):
    lang = request.GET.get('lang', 'ru')
    if lang == 'kz':
        lang = 'kz'

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
    lang = request.GET.get('lang', 'ru')
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
    lang = request.GET.get('lang', 'ru')

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
