import os
import json
import random
import difflib
from datetime import timedelta
from .models import Book, Category  
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm, AuthenticationForm
from django.db.models import Count, Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rapidfuzz import fuzz
# Import Models & Forms
from .models import Book, Favorite, Borrow, UserProfile, Cart, CartItem, Order, OrderItem, Review
from .forms import RegisterForm, BookForm, UserEditForm, ProfileEditForm, ReviewForm, AdminAddUserForm
from django.db.models import Q
from .services import (
    get_filtered_books, get_book_details, search_books_by_title, 
    toggle_favorite, get_user_borrows, get_user_favorites
)

# Import AI & Computer Vision Modules
from ai_brain import (
    get_chatbot_response, extract_search_query, is_query_too_short, 
    find_book_by_query, extract_author_query, find_books_by_author, 
    extract_category_query, find_books_by_category
)
from vision_brain import extract_text_from_image, predict_book_category

# ==========================================
# 1. USER & CUSTOMER VIEWS
# ==========================================

@login_required
def dashboard(request):
    total_books = Book.objects.count()
    borrowed_count = Borrow.objects.filter(return_date__isnull=True).count()
    favorites_count = Favorite.objects.count()
    total_orders = Order.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    due_soon_count = Borrow.objects.filter(
        return_date__isnull=True, 
        due_date__lte=timezone.now().date() + timedelta(days=5)
    ).count()

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

def home(request):
    return HttpResponse("Chatbot đã sẵn sàng!")

def books(request):
    category_slug = request.GET.get('category', '')
    available = request.GET.get('available', '')
    sort = request.GET.get('sort', '')

    book_list = Book.objects.all()

    # 1. Lọc theo thể loại (giữ nguyên logic đang hoạt động tốt của bạn)
    if category_slug:
        book_list = book_list.filter(category__code__iexact=category_slug)

    # 2. Lọc theo trạng thái còn/hết sách (giữ nguyên)
    if available:
        if available == 'true':
            book_list = book_list.filter(quantity__gt=0)
        elif available == 'false':
            book_list = book_list.filter(quantity=0)

    # 3. Sắp xếp (Thêm đoạn ánh xạ 'year' -> 'published_year' ở đây để tránh FieldError)
    if sort:
        if sort == 'year':
            sort_field = 'published_year'
        elif sort == '-year':
            sort_field = '-published_year'
        else:
            sort_field = sort
            
        book_list = book_list.order_by(sort_field)

    categories = Category.objects.all()

    context = {
        'books': book_list,
        'categories': categories,
        'category': category_slug,
        'available': available,
        'sort': sort,
    }
    
    return render(request, 'customer/books.html', context)

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

    return redirect(request.META.get('HTTP_REFERER', 'books'))

from django.db.models import Q

def book_search(request):
    query = request.GET.get("q") or request.GET.get("title", "")
    category = request.GET.get("category")
    available = request.GET.get("available")
    available_bool = (available.lower() == "true") if available else None
    sort = request.GET.get("sort")

    # Lọc đồng thời theo tiêu đề hoặc tác giả chứa từ khóa
    books_qs = Book.objects.all()
    if query:
        books_qs = books_qs.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )
    
    if category:
        books_qs = books_qs.filter(category__code__iexact=category)
    if available_bool is not None:
        if available_bool:
            books_qs = books_qs.filter(quantity__gt=0)
        else:
            books_qs = books_qs.filter(quantity=0)
    if sort:
        books_qs = books_qs.order_by(sort)

    return render(request, "customer/book_search.html", {
        "books": books_qs, "query": query, "category": category, 
        "available": available, "sort": sort
    })

@login_required
def borrowed(request):
    borrows = get_user_borrows(request.user)
    return render(request, "customer/borrowed.html", {"borrows": borrows})

@login_required
def favorites(request):
    favs = get_user_favorites(request.user)
    return render(request, "customer/favorites.html", {"favs": favs})

# ==========================================
# 2. CART & CHECKOUT
# ==========================================

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'customer/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, book_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    
    book = get_object_or_404(Book, id=book_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
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
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        items = cart.items.all()
        if not items:
            messages.info(request, 'Giỏ hàng đang trống')
            return redirect('cart')

        for item in items:
            if item.book.available < item.quantity:
                messages.error(
                    request, 
                    f'Sách "{item.book.title}" chỉ còn {item.book.available} cuốn, không đủ số lượng bạn đặt ({item.quantity} cuốn).'
                )
                return redirect('cart')

        with transaction.atomic():
            order = Order.objects.create(user=request.user, status='completed')
            for item in items:
                OrderItem.objects.create(
                    order=order, book=item.book, 
                    quantity=item.quantity, unit_price=item.book.price
                )
                item.book.available -= item.quantity
                item.book.quantity -= item.quantity
                item.book.save()

            items.delete()

        messages.success(request, 'Thanh toán đơn hàng thành công!')
        return redirect('order_history')

    return render(request, 'customer/checkout.html', {'cart': cart, 'total': cart.get_total_price()})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__book').order_by('-created_at')
    return render(request, 'customer/order_history.html', {'orders': orders})

# ==========================================
# 3. AUTH & PROFILE VIEWS
# ==========================================

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

def logout_view(request):
    logout(request)
    messages.info(request, 'Đã đăng xuất')
    return redirect('dashboard')

@login_required
def profile_view(request):
    return render(request, 'auth/profile.html', {'user': request.user})

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

# ==========================================
# 4. ADMIN MANAGEMENT VIEWS
# ==========================================

@staff_member_required
def admin_reports(request):
    pending_borrows = Borrow.objects.filter(status='pending').select_related('book', 'user')
    due_soon = Borrow.objects.filter(
        return_date__isnull=True, 
        due_date__lte=timezone.now().date() + timedelta(days=5)
    ).select_related('book', 'user')
    total_orders = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5].prefetch_related('items__book')

    return render(request, 'admin/admin_reports.html', {
        'pending_borrows': pending_borrows, 
        'due_soon': due_soon,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
    })

@staff_member_required
def admin_user_list(request):
    users = User.objects.all()
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
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        pwd_form = SetPasswordForm(user, request.POST)
        
        if form.is_valid():
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
        'form': form, 'pwd_form': pwd_form, 'user': user
    })

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

@staff_member_required
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.id == user.id:
        messages.error(request, 'Không thể xóa tài khoản của chính mình')
        return redirect('admin_user_list')
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Đã xóa tài khoản')
        return redirect('admin_user_list')
    return render(request, 'admin/user_confirm_delete.html', {'user': user})

@staff_member_required
def admin_book_list(request):
    books_qs = Book.objects.all()
    return render(request, 'admin/admin_book_list.html', {'books': books_qs})

@staff_member_required
def admin_book_add(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm sách')
            return redirect('admin_book_list')
    else:
        form = BookForm()
    return render(request, 'admin/book_form.html', {'form': form, 'action': 'Thêm sách'})

@staff_member_required
def admin_book_edit(request, book_id):
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

@staff_member_required
def admin_book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Đã xóa sách')
        return redirect('admin_book_list')
    return render(request, 'admin/book_confirm_delete.html', {'book': book})

@staff_member_required
def admin_borrow_requests(request):
    pending_borrows = Borrow.objects.filter(status='pending').select_related('book', 'user')
    return render(request, 'admin/borrow_requests.html', {'borrows': pending_borrows})

@staff_member_required
def admin_approve_borrow(request, borrow_id):
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

@staff_member_required
def admin_reject_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)
    borrow.status = 'rejected'
    borrow.save()
    messages.info(request, 'Đã từ chối yêu cầu mượn.')
    return redirect('admin_borrow_requests')

@staff_member_required
def admin_category_add(request):
    """View cho phép Admin tạo thể loại sách mới"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().lower()

        if name and code:
            # Sửa chữ 'c' thường thành chữ 'C' hoa ở Category:
            category, created = Category.objects.get_or_create(
                code=code, 
                defaults={'name': name}
            )
            if created:
                messages.success(request, f'Đã thêm thể loại mới: "{name}"')
                return redirect('admin_book_list')
            else:
                messages.error(request, f'Mã thể loại "{code}" đã tồn tại!')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ tên và mã thể loại.')

    return render(request, 'admin/category_form.html')


# ==========================================
# 5. AI CHATBOT & VISION VIEWS
# ==========================================
import re

import unicodedata
from PIL import Image

def remove_accents(input_str):
    """Hàm chuyển chuỗi tiếng Việt có dấu thành không dấu (VD: 'Chí Phèo' -> 'chi pheo')"""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    no_accent = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return no_accent.replace('đ', 'd').replace('Đ', 'D').lower()

@csrf_exempt
def chat_view(request):
    """View chính xử lý cả tin nhắn Text và Ảnh gửi tới Chatbot"""
    if request.method == 'POST':
        current_intent = "nhan_dien_anh"

        # --- BẮT ĐẦU ĐOẠN THÊM MỚI ---
    # Chặn người chưa đăng nhập sử dụng chatbot
    if not request.user.is_authenticated:
        return JsonResponse({'reply': 'Vui lòng đăng nhập để sử dụng chatbot.'}, status=401)
    # --- KẾT THÚC ĐOẠN THÊM MỚI ---

    if request.method == 'POST':
        current_intent = "nhan_dien_anh"

        # --- A. XỬ LÝ ẢNH BÌA SÁCH ---
        if request.FILES.get('image'):
            image = request.FILES['image']
            upload_dir = os.path.join('media', 'temp')
            os.makedirs(upload_dir, exist_ok=True)
            temp_path = os.path.join(upload_dir, image.name)
            
            try:
                # Lưu file tạm
                with open(temp_path, 'wb+') as f:
                    for chunk in image.chunks(): 
                        f.write(chunk)
                try:
                    img_pil = Image.open(temp_path).convert('RGB')
                    temp_path_jpg = temp_path + ".jpg"
                    img_pil.save(temp_path_jpg, "JPEG")
                    temp_path = temp_path_jpg # Dùng đường dẫn file .jpg mới cho các bước sau
                except Exception as e:
                    print(f"⚠️ Lỗi chuyển đổi ảnh: {e}")

                sach_goi_y = None
                
                ## 1. Đọc OCR chữ trên ảnh bìa
                detected_text = extract_text_from_image(temp_path)
                print(f"🔍 [DEBUG OCR] Chuỗi gốc: '{detected_text}'")

                if detected_text:
                    # Chuẩn hóa chuỗi OCR: Bỏ dấu tiếng Việt + Viết thường
                    ocr_clean = remove_accents(detected_text)
                    
                    # Trích xuất các số nguyên vẹn đứng độc lập (Loại bỏ số dính chữ như '8Mg')
                    ocr_numbers = set(re.findall(r'\b\d+\b', ocr_clean))
                    best_match = None
                    highest_score = 0

                    for book in Book.objects.all():
                        title_clean = remove_accents(book.title)
                        book_numbers = set(re.findall(r'\b\d+\b', title_clean))
                        
                        # So khớp độ tương đồng
                        score_set = fuzz.token_set_ratio(title_clean, ocr_clean)
                        score_partial = fuzz.partial_ratio(title_clean, ocr_clean)
                        score = max(score_set, score_partial)

                        # 🛑 RÀNG BUỘC SỐ CHẶT CHẼ ĐỂ TRÁNH NHẦM LẪN SÁCH NGOÀI
                        if book_numbers and ocr_numbers:
                            # Nếu khác số lớp/tập (VD: 5 khác 8), trừ điểm hoặc bỏ qua ngay lập tức
                            if not book_numbers.intersection(ocr_numbers):
                                continue

                        # Nâng ngưỡng nhận diện sách trong kho lên 85% để ảnh ngoài không bị bắt ép khớp sai
                        if score > highest_score and score >= 85:
                            highest_score = score
                            best_match = book

                    if best_match:
                        sach_goi_y = best_match
                        print(f"🎯 Khớp thành công: '{best_match.title}' với độ tin cậy {highest_score}%")

                # 2. Tìm theo tên file tải lên (nếu OCR không thấy)
                if not sach_goi_y:
                    image_name = os.path.splitext(image.name)[0].lower()
                    if len(image_name) > 2 and image_name not in ['image', 'images', 'download', 'untitle', 'untitled']:
                        sach_goi_y = Book.objects.filter(title__icontains=image_name).first()
                
                # Trả về kết quả
                if sach_goi_y:
                    link = f"/books/{sach_goi_y.id}/"
                    response = (
                        f"Mình nhận diện được sách: <b>{sach_goi_y.title}</b><br>"
                        f"Tác giả: {sach_goi_y.author}<br>"
                        f"<a href='{link}' style='color:blue; font-weight:bold;'>Nhấn vào đây để xem chi tiết & mượn sách</a>"
                    )
                else:
                    # 3. Tận dụng CNN dự đoán thể loại & GỢI Ý SÁCH CÙNG THỂ LOẠI TƯƠNG TỰ
                    predicted_cat = predict_book_category(temp_path)
                    if predicted_cat:
                        # Lấy thông tin thể loại từ database Category mới
                        cat_obj = Category.objects.filter(code__iexact=predicted_cat).first()
                        cat_display = cat_obj.name if cat_obj else predicted_cat.upper()

                        # Query lấy tối đa 3 cuốn sách thuộc thể loại đó (Dùng category__code)
                        similar_books = Book.objects.filter(category__code__iexact=predicted_cat)[:3]

                        if similar_books.exists():
                            items_html = "".join(
                                f"<li><b>{b.title}</b> ({b.author}) — "
                                f"<a href='/books/{b.id}/' style='color:blue; font-weight:bold;'>Xem chi tiết</a></li>"
                                for b in similar_books
                            )
                            response = (
                                f"Không tìm thấy chính xác cuốn sách này trong kho, nhưng mình đoán ảnh thuộc thể loại <b>{cat_display}</b>.<br><br>"
                                f"<b>💡 Gợi ý một số sách cùng thể loại hiện có sẵn:</b>"
                                f"<ul style='margin-top: 5px; padding-left: 20px;'>{items_html}</ul>"
                            )
                        else:
                            response = f"Không tìm thấy chính xác cuốn sách này, nhưng mình đoán ảnh thuộc thể loại <b>{cat_display}</b> (hiện chưa có sách nào thuộc thể loại này trong kho)."
                    else:
                        response = "Không tìm thấy truyện/sách nào tương ứng với ảnh bạn gửi trong thư viện."

            finally:
                # Dọn dẹp file tạm an toàn
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            return JsonResponse({'reply': response, 'intent': current_intent})

        # --- B. XỬ LÝ TIN NHẮN CHỮ (TEXT CHAT) ---
        else:
            msg = request.POST.get('message', '').strip()
            if not msg:
                # Trường hợp nhận dữ liệu JSON
                try:
                    data = json.loads(request.body)
                    msg = data.get('message', '').strip()
                except Exception:
                    pass

            intent, response = get_chatbot_response(msg)
            
            if intent == "tim_sach":
                query = extract_search_query(msg)
                if is_query_too_short(query):
                    response = "Bạn muốn tìm cuốn nào? Hãy gõ tên sách cụ thể hơn nhé (ít nhất 2 ký tự)."
                else:
                    sach = find_book_by_query(query, Book.objects.all())
                    if sach:
                        link = f"/books/{sach.id}/"
                        response = (
                            f"Mình tìm thấy cuốn <b>{sach.title}</b> rồi!<br>"
                            f"Tác giả: {sach.author}<br>"
                            f"Còn lại: {sach.available} cuốn.<br>"
                            f"<a href='{link}' style='color:blue; font-weight:bold;'>Nhấn vào đây để xem chi tiết & mượn sách</a>"
                        )
                    else:
                        response = f"Mình tìm không thấy cuốn nào tên là '{query}' trong thư viện cả."

            elif intent == "tim_theo_tac_gia":
                author_query = extract_author_query(msg)
                if is_query_too_short(author_query):
                    response = "Bạn muốn tìm sách của tác giả nào? Hãy gõ tên tác giả cụ thể hơn nhé (ít nhất 2 ký tự)."
                else:
                    sach_list = find_books_by_author(author_query, Book.objects.all())
                    if sach_list:
                        items = "".join(
                            f"<br>- <b>{b.title}</b> (còn {b.available} cuốn) — "
                            f"<a href='/books/{b.id}/' style='color:blue; font-weight:bold;'>Xem chi tiết</a>"
                            for b in sach_list
                        )
                        response = f"Mình tìm thấy {len(sach_list)} cuốn của tác giả '{author_query}':{items}"
                    else:
                        response = f"Mình tìm không thấy tác giả nào tên là '{author_query}' trong thư viện cả."

            elif intent == "tim_theo_the_loai":
                category_query = extract_category_query(msg)
                if is_query_too_short(category_query):
                    response = "Bạn muốn tìm thể loại nào? Hãy gõ tên thể loại cụ thể hơn nhé (ít nhất 2 ký tự)."
                else:
                    sach_list = find_books_by_category(category_query, Book.objects.all())
                    if sach_list:
                        items = "".join(
                            f"<br>- <b>{b.title}</b> ({b.author}, còn {b.available} cuốn) — "
                            f"<a href='/books/{b.id}/' style='color:blue; font-weight:bold;'>Xem chi tiết</a>"
                            for b in sach_list
                        )
                        response = f"Mình tìm thấy {len(sach_list)} cuốn thuộc thể loại '{category_query}':{items}"
                    else:
                        response = f"Mình tìm không thấy sách nào thuộc thể loại '{category_query}' trong thư viện cả."

            return JsonResponse({'reply': response, 'intent': intent})
    
    return JsonResponse({'reply': 'Method không được hỗ trợ'}, status=405)

# Signal tự động tạo Profile và Giỏ hàng khi User mới đăng ký
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Cart.objects.create(user=instance)

# Gán alias để urls.py gọi tên cũ api_chat_bot vẫn hoạt động bình thường
api_chat_bot = chat_view