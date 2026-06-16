# Này xem như là phần xử lí API mà urls.py gọi đến,
# Nó hay gọi đến phần service để xử lí lấy dữ liệu 

from django.shortcuts import render
from django.http import HttpResponse
from .models import Book, Favorite, Borrow
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.http import JsonResponse
from .services import get_filtered_books, get_book_details, search_books_by_title, borrow_book, toggle_favorite, get_user_borrows, get_user_favorites



# T làm biếng quá nên tự hiểu đi
# Cho chuối này 🍌
# Éc éc khẹc khẹc 🐒

def dashboard(request):
    return render(request, "dashboard.html")

def books(request):
    category = request.GET.get("category")
    available = request.GET.get("available")
    sort = request.GET.get("sort")

    books = get_filtered_books(
        category=category,
        available=(available.lower() == "true") if available else None,
        sort=sort,
    )

    return render(request, "books.html", {"books": books, "category": category, "available": available, "sort": sort})

def book_details(request, book_id):
    book = get_book_details(book_id)
    if not book:
        return HttpResponse("Book not found", status=404)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, book=book).exists()

    return render(request, "book_details.html", {"book": book, "is_favorite": is_favorite})


@login_required
def book_borrow(request, book_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    success, msg = borrow_book(request.user, book_id)
    if success:
        messages.success(request, msg)
        return redirect('borrowed')
    else:
        messages.error(request, msg)
        return redirect('book_detail', book_id=book_id)


@login_required
def book_favorite(request, book_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    is_fav, action = toggle_favorite(request.user, book_id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_fav, 'action': action})

    if is_fav:
        messages.success(request, "Đã thêm vào yêu thích")
    else:
        messages.info(request, "Đã bỏ yêu thích")

    return redirect('book_detail', book_id=book_id)

def book_search(request):
    title = request.GET.get("title")
    category = request.GET.get("category")
    available = request.GET.get("available")

    if available is not None and available != "":
        available_bool = available.lower() == "true"
    else:
        available_bool = None

    sort = request.GET.get("sort")

    books = search_books_by_title(title, category=category, available=available_bool, sort=sort)
    return render(request, "book_search.html", {"books": books, "title": title, "category": category, "available": available, "sort": sort})

def borrowed(request):
    if not request.user.is_authenticated:
        return redirect('books')

    borrows = get_user_borrows(request.user)
    return render(request, "borrowed.html", {"borrows": borrows})

def favorites(request):
    if not request.user.is_authenticated:
        return redirect('books')

    favs = get_user_favorites(request.user)
    return render(request, "favorites.html", {"favs": favs})

def home(request):
    return HttpResponse("Chatbot đã sẵn sàng!")
