# truy vấn

from urllib import response

from urllib import response

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
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .forms import AdminAddUserForm
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import authenticate, login


import os
import random
import difflib
import joblib
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import JsonResponse
from ai_brain import get_chatbot_response
intent_model = None



@login_required
def dashboard(request):
    # Tổng số sách
    total_books = Book.objects.count()

    borrowed_count = Borrow.objects.filter(return_date__isnull=True).count()

    favorites_count = Favorite.objects.count()
    total_orders = Order.objects.count()

    active_users = User.objects.filter(is_active=True).count()
    due_soon_count = Borrow.objects.filter(return_date__isnull=True, due_date__lte=timezone.now().date() + timedelta(days=5)).count()

    recent_books = Book.objects.order_by('-created_at')[:5]

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

    book = get_object_or_404(Book, id=book_id)
    due_date = timezone.now().date() + timedelta(days=14)
    
    Borrow.objects.create(
        user=request.user,
        book=book,
        due_date=due_date,
        status='pending' 
    )
    
    messages.success(request, "Đã gửi yêu cầu mượn sách, vui lòng chờ Admin duyệt.")
    return redirect('borrowed')


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

@login_required
def borrowed(request):
    if not request.user.is_authenticated:
        return redirect('books')

    borrows = get_user_borrows(request.user)
    return render(request, "customer/borrowed.html", {"borrows": borrows})

@login_required
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

@login_required(login_url='login')
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

    pending_borrows = Borrow.objects.filter(status='pending').select_related('book', 'user')
    
    due_soon = Borrow.objects.filter(return_date__isnull=True, due_date__lte=timezone.now().date() + timedelta(days=5)).select_related('book', 'user')
    total_orders = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5].prefetch_related('items__book')

    return render(request, 'admin/admin_reports.html', {
        'pending_borrows': pending_borrows, 
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
        # Khởi tạo SetPasswordForm với dữ liệu POST
        pwd_form = SetPasswordForm(user, request.POST)
        
        # Kiểm tra: nếu form chính hợp lệ VÀ (mật khẩu trống HOẶC mật khẩu hợp lệ)
        if form.is_valid():
            # Kiểm tra xem có dữ liệu mật khẩu được gửi lên không
            if request.POST.get('new_password1') or request.POST.get('new_password2'):
                if pwd_form.is_valid():
                    pwd_form.save()
                    form.save()
                    messages.success(request, 'Đã cập nhật tài khoản và mật khẩu!')
                    return redirect('admin_user_list')
            else:
                form.save()
                messages.success(request, 'Đã cập nhật tài khoản!')
                return redirect('admin_user_list')
    else:
        form = UserEditForm(instance=user)
        pwd_form = SetPasswordForm(user)
        
    return render(request, 'admin/user_form.html', {
        'form': form, 
        'pwd_form': pwd_form, 
        'user': user
    })

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
def admin_borrow_requests(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    pending_borrows = Borrow.objects.filter(status='pending').select_related('book', 'user')
    return render(request, 'admin/borrow_requests.html', {'borrows': pending_borrows})

@login_required
def admin_approve_borrow(request, borrow_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    borrow = get_object_or_404(Borrow, id=borrow_id)
    book = borrow.book
    
    if book.available > 0:
        borrow.status = 'approved'
        borrow.save()
        
        book.available -= 1
        book.save()
        messages.success(request, f'Đã duyệt yêu cầu của {borrow.user.username}')
    else:
        messages.error(request, 'Sách đã hết, không thể duyệt!')
        
    return redirect('admin_borrow_requests')

@login_required
def admin_reject_borrow(request, borrow_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    borrow = get_object_or_404(Borrow, id=borrow_id)
    borrow.status = 'rejected'
    borrow.save()
    messages.info(request, 'Đã từ chối yêu cầu mượn.')
    return redirect('admin_borrow_requests')


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


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Đăng ký thành công')
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

from django import forms
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
        else:
            if not request.POST.get('username') or not request.POST.get('password'):
                form.add_error(None, "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            else:
                form.add_error(None, "Tên đăng nhập hoặc mật khẩu không chính xác.")
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Đã đăng xuất')
    return redirect('dashboard')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Cart.objects.create(user=instance)
@staff_member_required
def admin_user_list(request):
    users = User.objects.all()
    # TRUYỀN 'users' (số nhiều) ĐỂ KHÔNG ĐÈ BIẾN 'user' CỦA DÙNG CHUNG
    return render(request, 'admin/admin_user_list.html', {'users': users})
    
@staff_member_required
def add_new_user(request):
    if request.method == 'POST':
        form = AdminAddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = form.cleaned_data['is_staff']
            user.save()
            return redirect('admin_user_list')
    else:
        form = AdminAddUserForm()
    return render(request, 'admin/add_user.html', {'form': form})

@staff_member_required
def admin_change_user_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_user_edit', user_id=user.id)
    else:
        form = SetPasswordForm(user)
    return render(request, 'admin/change_password.html', {'form': form, 'target_user': user})


    

from django.http import JsonResponse
import json
from ai_brain import get_chatbot_response, extract_search_query, is_query_too_short
from .models import Book 

def api_chat_bot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        
        intent, reply = get_chatbot_response(user_message)
        
        if intent == "tim_sach":

            query = extract_search_query(user_message)

            if is_query_too_short(query):
                reply = "Bạn muốn tìm cuốn nào? Hãy gõ tên sách cụ thể hơn nhé (ít nhất 2 ký tự)."
            else:
                sach = Book.objects.filter(title__icontains=query).first()

                if sach:
                    link = f"/books/{sach.id}/" 
                    
                    reply = (
                        f"Mình tìm thấy cuốn <b>{sach.title}</b> rồi!<br>"
                        f"Tác giả: {sach.author}<br>"
                        f"Còn lại: {sach.available} cuốn.<br>"
                        f"<a href='{link}' style='color:blue; font-weight:bold;'>Nhấn vào đây để xem chi tiết & mượn sách</a>"
                    )
                else:
                    reply = f"Mình tìm không thấy cuốn nào tên là '{query}' trong thư viện cả."

        return JsonResponse({"reply": reply, "intent": intent})
    


# chatbot/views.py
from django.http import JsonResponse
import os
from .models import Book 
from vision_brain import predict_book_category
from ai_brain import get_chatbot_response, extract_search_query, is_query_too_short

@csrf_exempt
def chat_view(request):
    if request.method == 'POST':
        # --- 1. XỬ LÝ ẢNH ---
        if request.FILES.get('image'):
            image = request.FILES['image']
            upload_dir = os.path.join('media', 'temp')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            temp_path = os.path.join(upload_dir, image.name)
            with open(temp_path, 'wb+') as f:
                for chunk in image.chunks(): 
                    f.write(chunk)
            
            category = predict_book_category(temp_path)
            sach_goi_y = Book.objects.filter(category__iexact=category).first()
            
            if sach_goi_y:
                link = f"/books/{sach_goi_y.id}/"
                response = (
                    f"Mình thấy ảnh này thuộc thể loại: <b>{category}</b>.<br>"
                    f"Gợi ý cho bạn cuốn: <b>{sach_goi_y.title}</b><br>"
                    f"Tác giả: {sach_goi_y.author}<br>"
                    f"<a href='{link}' style='color:blue; font-weight:bold;'>Nhấn vào đây để xem chi tiết</a>"
                )
            else:
                response = f"Ảnh này thuộc thể loại: {category}, nhưng mình chưa có cuốn nào thuộc thể loại này trong kho."
            # Dọn dẹp file tạm
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return JsonResponse({'reply': response})            
        # --- 2. XỬ LÝ TEXT ---
        else:
            msg = request.POST.get('message', '').strip()
            intent, response = get_chatbot_response(msg)
            
            if intent == "tim_sach":
                query = extract_search_query(msg)

                if is_query_too_short(query):
                    response = "Bạn muốn tìm cuốn nào? Hãy gõ tên sách cụ thể hơn nhé (ít nhất 2 ký tự)."
                else:
                    sach_tim_thay = Book.objects.filter(title__icontains=query).first()

                    if sach_tim_thay:
                        link = f"/books/{sach_tim_thay.id}/"
                        response = (
                            f"Mình tìm thấy cuốn <b>{sach_tim_thay.title}</b> rồi!<br>"
                            f"Tác giả: {sach_tim_thay.author}<br>"
                            f"Còn lại: {sach_tim_thay.available} cuốn.<br>"
                            f"<a href='{link}' style='color:blue; font-weight:bold;'>Nhấn vào đây để xem chi tiết</a>"
                        )
                    else:
                        response = f"Mình tìm không thấy cuốn nào tên là '{query}' trong thư viện cả."

            return JsonResponse({'reply': response})
    
    return JsonResponse({'reply': 'Method không được hỗ trợ'}, status=405)
