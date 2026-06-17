# Này xem như là phần xử lí API mà urls.py gọi đến,
# Nó hay gọi đến phần service để xử lí lấy dữ liệu 

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .services import get_filtered_books, get_book_details, search_books_by_title, borrow_book, toggle_favorite, get_user_borrows, get_user_favorites
from .forms import RegisterForm, BookForm, UserEditForm, ProfileEditForm, ReviewForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book, Favorite, Borrow, UserProfile, Cart, CartItem, Order, OrderItem, Review



# T làm biếng quá nên tự hiểu đi
# Cho chuối này 🍌
# Éc éc khẹc khẹc 🐒

def dashboard(request):
    # Tổng số sách
    total_books = Book.objects.count()

    # Số sách đang được mượn (chưa trả)
    borrowed_count = Borrow.objects.filter(return_date__isnull=True).count()

    # Tổng số mục yêu thích
    favorites_count = Favorite.objects.count()
    total_orders = Order.objects.count()

    # Số người dùng active (dùng làm chỉ số sơ bộ)
    active_users = User.objects.filter(is_active=True).count()
    due_soon_count = Borrow.objects.filter(return_date__isnull=True, due_date__lte=timezone.now().date() + timedelta(days=5)).count()

    # Sách mới thêm gần đây
    recent_books = Book.objects.order_by('-created_at')[:5]

    # Top sách được mượn (theo số lần mượn)
    top_borrowed_qs = (
        Borrow.objects.values('book__id', 'book__title')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    top_borrowed = [
        {'title': item['book__title'], 'count': item['count']}
        for item in top_borrowed_qs
    ]

    context = {
        'total_books': total_books,
        'borrowed_count': borrowed_count,
        'favorites_count': favorites_count,
        'active_users': active_users,
        'recent_books': recent_books,
        'top_borrowed': top_borrowed,
        'total_orders': total_orders,
        'due_soon_count': due_soon_count,
    }

    return render(request, "customer/dashboard.html", context)

def books(request):
    category = request.GET.get("category")
    available = request.GET.get("available")
    sort = request.GET.get("sort")

    books = get_filtered_books(
        category=category,
        available=(available.lower() == "true") if available else None,
        sort=sort,
    )

    return render(request, "customer/books.html", {"books": books, "category": category, "available": available, "sort": sort})

def book_details(request, book_id):
    book = get_book_details(book_id)
    if not book:
        return HttpResponse("Book not found", status=404)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, book=book).exists()

    reviews = book.reviews.select_related('user').order_by('-created_at')
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] if reviews.exists() else None

    return render(request, "customer/book_details.html", {
        "book": book,
        "is_favorite": is_favorite,
        "reviews": reviews,
        "review_form": ReviewForm(),
        "average_rating": average_rating,
    })


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
    return render(request, "customer/book_search.html", {"books": books, "title": title, "category": category, "available": available, "sort": sort})

def borrowed(request):
    if not request.user.is_authenticated:
        return redirect('books')

    borrows = get_user_borrows(request.user)
    return render(request, "customer/borrowed.html", {"borrows": borrows})

def favorites(request):
    if not request.user.is_authenticated:
        return redirect('books')

    favs = get_user_favorites(request.user)
    return render(request, "customer/favorites.html", {"favs": favs})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        items = cart.items.all()
        if not items:
            messages.info(request, 'Giỏ hàng đang trống')
            return redirect('cart')

        order = Order.objects.create(user=request.user, status='completed')
        for item in items:
            OrderItem.objects.create(
                order=order,
                book=item.book,
                quantity=item.quantity,
                unit_price=item.book.price
            )
        items.delete()
        messages.success(request, 'Thanh toán đơn hàng thành công')
        return redirect('order_history')

    return render(request, 'customer/checkout.html', {'cart': cart, 'total': cart.get_total_price()})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book').order_by('-created_at')
    return render(request, 'customer/order_history.html', {'orders': orders})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật thông tin cá nhân')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'auth/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Đã đổi mật khẩu thành công')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'auth/password_change.html', {'form': form})

@login_required
def add_review(request, book_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    book = get_object_or_404(Book, id=book_id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.book = book
        review.user = request.user
        review.save()
        messages.success(request, 'Cảm ơn bạn đã đánh giá sách')
    else:
        messages.error(request, 'Đánh giá không hợp lệ')
    return redirect('book_detail', book_id=book.id)

@login_required
def admin_reports(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    due_soon = Borrow.objects.filter(return_date__isnull=True, due_date__lte=timezone.now().date() + timedelta(days=5)).select_related('book', 'user')
    total_orders = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5].prefetch_related('items__book')

    return render(request, 'admin/admin_reports.html', {
        'due_soon': due_soon,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
    })

def home(request):
    return HttpResponse("Chatbot đã sẵn sàng!")


@login_required
def admin_user_list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    users = User.objects.all()
    return render(request, 'admin/admin_user_list.html', {'users': users})


@login_required
def admin_user_edit(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật tài khoản')
            return redirect('admin_user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'admin/user_form.html', {'form': form, 'user': user})


@login_required
def admin_user_delete(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    user = get_object_or_404(User, id=user_id)
    if request.user.id == user.id:
        messages.error(request, 'Không thể xóa tài khoản của chính mình')
        return redirect('admin_user_list')
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Đã xóa tài khoản')
        return redirect('admin_user_list')
    return render(request, 'admin/user_confirm_delete.html', {'user': user})


@login_required
def admin_book_list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    books = Book.objects.all()
    return render(request, 'admin/admin_book_list.html', {'books': books})


@login_required
def admin_book_add(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm sách')
            return redirect('admin_book_list')
    else:
        form = BookForm()
    return render(request, 'admin/book_form.html', {'form': form, 'action': 'Thêm sách'})


@login_required
def admin_book_edit(request, book_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật sách')
            return redirect('admin_book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'admin/book_form.html', {'form': form, 'action': 'Chỉnh sửa sách'})


@login_required
def admin_book_delete(request, book_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Đã xóa sách')
        return redirect('admin_book_list')
    return render(request, 'admin/book_confirm_delete.html', {'book': book})


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'customer/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, book_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    book = get_object_or_404(Book, id=book_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add or update item
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, book=book)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'Đã thêm "{book.title}" vào giỏ hàng')
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Đã xóa khỏi giỏ hàng')
    return redirect('cart')


@login_required
def update_cart_item(request, item_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.POST.get('quantity', 1)
    
    try:
        quantity = int(quantity)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cập nhật giỏ hàng')
        else:
            cart_item.delete()
            messages.success(request, 'Đã xóa khỏi giỏ hàng')
    except ValueError:
        messages.error(request, 'Số lượng không hợp lệ')
    
    return redirect('cart')


@login_required
def profile_view(request):
    return render(request, 'auth/profile.html', {'user': request.user})


# --- Authentication views ---
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # profile will be created by signal
            login(request, user)
            messages.success(request, 'Đăng ký thành công')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Đăng nhập thành công')
            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Đã đăng xuất')
    return redirect('dashboard')


# Create UserProfile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Cart.objects.create(user=instance)
