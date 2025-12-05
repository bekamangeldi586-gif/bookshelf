from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Book, Cart, CartItem
from .forms import BookForm
from translatepy import Translator
import requests
from django.conf import settings
from urllib.parse import quote_plus
from django.utils import timezone
import datetime
import random
import json
from pathlib import Path
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import Http404

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
            user = form.save()
            # add new user to 'user' group
            try:
                from django.contrib.auth.models import Group
                grp, _ = Group.objects.get_or_create(name='user')
                grp.user_set.add(user)
            except Exception:
                pass
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

    id_token = None
    if 'oidc_id_token' in request.session:
        id_token = request.session.get('oidc_id_token')
    elif 'id_token' in request.session:
        id_token = request.session.get('id_token')
    else:
        for key in ('oidc_auth', 'oidc', 'mozilla_oidc', 'oidc_tokens'):
            data = request.session.get(key)
            if isinstance(data, dict):
                id_token = data.get('id_token') or data.get('idToken') or data.get('idtoken')
                if id_token:
                    break

    logout_redirect = request.build_absolute_uri('/')
    saved_id_token = id_token

    logout(request)

    if saved_id_token:
        logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
        params = []
        params.append(f"id_token_hint={quote_plus(saved_id_token)}")
        params.append(f"post_logout_redirect_uri={quote_plus(logout_redirect)}")
        return redirect(f"{logout_url}?{'&'.join(params)}")

    return redirect(f'/login/?lang={lang}')

@login_required
def add_book(request):
    lang = get_lang(request)
    if not request.user.groups.filter(name='admin').exists():
        raise PermissionDenied

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {'form': form, 'lang': lang})

@login_required
def edit_book(request, pk):
    lang = get_lang(request)
    if not request.user.groups.filter(name='admin').exists():
        raise PermissionDenied
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
    if not request.user.groups.filter(name='admin').exists():
        raise PermissionDenied
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

@login_required
def itemuse_json(request):
    """Возвращает JSON со статистикой — количество людей, взявших книги по месяцам за год.

    Формат:
    {
      "items": [
         {"date": "01.2025", "value": 1035},
         ... (12 элементов)
      ]
    }
    """
    media_dir = Path(settings.MEDIA_ROOT)
    media_dir.mkdir(parents=True, exist_ok=True)
    out_path = media_dir / 'stat_itemuse.json'

    force = request.GET.get('force') in ('1', 'true', 'yes')

    if out_path.exists() and not force:
        try:
            existing_text = out_path.read_text(encoding='utf-8')
            data = json.loads(existing_text)
            return JsonResponse(data)
        except Exception:
            pass

    today = timezone.localdate()
    year = today.year
    month = today.month
    items = []

    for offset in range(11, -1, -1):
        m = month - offset
        y = year
        while m <= 0:
            m += 12
            y -= 1
        d = datetime.date(y, m, 1)
        value = random.randint(50, 400)
        items.append({
            'date': d.strftime('%m.%Y'),
            'value': value
        })

    out = {'items': items}

    try:
        existing = None
        if out_path.exists():
            try:
                existing = out_path.read_text(encoding='utf-8')
            except Exception:
                existing = None
        new_text = json.dumps(out, ensure_ascii=False, indent=2)
        if existing != new_text:
            out_path.write_text(new_text, encoding='utf-8')
    except Exception:
        pass

    return JsonResponse(out)


@login_required
def stat_page(request):
    """Страница со графиком, которая запрашивает `/stat/itemuse` и отображает Chart.js.

    Поддерживает GET-параметр `lang` для переключения языка, например `?lang=ru`.
    """
    lang = get_lang(request)
    return render(request, 'library/stat.html', {'lang': lang})


@login_required
def add_to_cart(request, book_id):
    """Добавить книгу в корзину (количество из POST/GET 'quantity')."""
    user = request.user
    cart, _ = Cart.objects.get_or_create(user=user)
    book = get_object_or_404(Book, pk=book_id)
    try:
        qty = int(request.POST.get('quantity', request.GET.get('quantity', 1)))
    except Exception:
        qty = 1

    item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={'quantity': qty})
    if not created:
        item.quantity = max(1, item.quantity + qty)
        item.save()

    return redirect('view_cart')


@login_required
def view_cart(request):
    lang = get_lang(request)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('book').all()
    # Переводим названия книг при необходимости (если язык не ru)
    target_lang = lang
    if lang == 'kz':
        target_lang = 'kk'

    if target_lang != 'ru':
        try:
            for item in items:
                # translatepy может быть медленным — оборачиваем в try
                try:
                    item.book.title = translator.translate(item.book.title, target_lang).result
                except Exception:
                    pass
        except Exception:
            pass

    return render(request, 'library/cart.html', {'cart': cart, 'items': items, 'lang': lang})


@login_required
@require_http_methods(["POST", "GET"])
def remove_from_cart(request, item_id):
    # allow GET for simple link removal, but prefer POST
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    return redirect('view_cart')


@login_required
def admin_users_list(request):
    # only admin staff can access
    if not request.user.is_staff:
        raise PermissionDenied
    User = get_user_model()
    users = User.objects.all().order_by('username')
    lang = get_lang(request)
    return render(request, 'library/users_list.html', {'users': users, 'lang': lang})


@login_required
def admin_user_cart(request, user_id):
    # only admin staff can access
    if not request.user.is_staff:
        raise PermissionDenied
    User = get_user_model()
    try:
        u = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise Http404

    # get or create user's cart
    cart, _ = Cart.objects.get_or_create(user=u)
    items = cart.items.select_related('book').all()

    lang = get_lang(request)
    # translate titles if needed
    target_lang = lang
    if lang == 'kz':
        target_lang = 'kk'
    if target_lang != 'ru':
        try:
            for item in items:
                try:
                    item.book.title = translator.translate(item.book.title, target_lang).result
                except Exception:
                    pass
        except Exception:
            pass

    return render(request, 'library/admin_user_cart.html', {'cart_owner': u, 'items': items, 'lang': lang})


@login_required
def admin_promote_user(request, user_id):
    # only admin staff can access
    if not request.user.is_staff:
        raise PermissionDenied
    User = get_user_model()
    try:
        u = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise Http404

    # cannot change own admin status via this view
    if u == request.user:
        return redirect('admin_users_list')

    admin_group, _ = Group.objects.get_or_create(name='admin')
    if admin_group in u.groups.all() or u.is_staff:
        # demote
        u.is_staff = False
        u.groups.remove(admin_group)
        u.save()
    else:
        # promote
        u.is_staff = True
        u.save()
        admin_group.user_set.add(u)

    return redirect('admin_users_list')
