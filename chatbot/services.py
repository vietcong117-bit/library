# Tùy mấy bạn đánh giá là hữu ích không thì tùy,
# Do t nghĩ là chỉ gọi không thì có thể gộp selector.py vào luôn
# Nhưng t nghĩ nếu có xử lí thêm sau khi gọi nên tách riêng ra cho dễ quản lí
# còn nếu không thì thôi gộp vào luôn cũng được, tùy mấy bạn


from .selector import get_all_books
from .selector import get_book_by_id
from .selector import get_books_by_category
from .selector import get_books_by_availability
from . import selector
from django.db import transaction
from django.db.models import Q
from .models import Book, Borrow, Favorite
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
# Mượn sách
def borrow_book(user, book_id, days=14):
    try:
        with transaction.atomic():
            book = Book.objects.select_for_update().get(id=book_id)
            if book.available <= 0:
                return False, "No copies available"

            borrow_date = __import__('django.utils.timezone', fromlist=['now']).now().date()
            due_date = borrow_date + __import__('datetime').timedelta(days=days)

            Borrow.objects.create(user=user, book=book, borrow_date=borrow_date, due_date=due_date)

            book.available = max(0, book.available - 1)
            book.save()

            return True, "Borrow created"
    except Book.DoesNotExist:
        return False, "Book not found"

# Thêm/xóa khỏi yêu thích
def toggle_favorite(user, book_id):
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        return False, "Book not found"

    fav, created = Favorite.objects.get_or_create(user=user, book=book)
    if created:
        return True, "added"
    else:
        fav.delete()
        return False, "removed"

# Lấy danh sách mượn
def get_user_borrows(user):
    return Borrow.objects.filter(user=user).select_related('book')

# Lấy danh sách yêu thích
def get_user_favorites(user):
    return Favorite.objects.filter(user=user).select_related('book')

# Lấy danh sách tất cả sách
def list_books():
    return get_all_books()

# Lấy chi tiết một cuốn sách theo ID
def get_book_details(book_id):
    return get_book_by_id(book_id)

# Lấy sách theo thể loại
from django.db.models import Q
from .models import Book

def get_filtered_books(category=None, available=None, sort=None):
    qs = Book.objects.all()

    # 1. Lọc Thể loại (Chống lệch giữa tiếng Việt và key trong DB)
    if category and str(category).strip():
        cat_val = str(category).strip().lower()
        
        # Ánh xạ cả giá trị Tiếng Việt lẫn Tiếng Anh về đúng Key lưu trong Model
        cat_mapping = {
            'tech': 'tech',
            'công nghệ': 'tech',
            'fiction': 'fiction',
            'văn học': 'fiction',
            'selfhelp': 'selfhelp',
            'tự phát triển': 'selfhelp',
            'business': 'business',
            'kinh doanh': 'business',
        }
        
        target_cat = cat_mapping.get(cat_val, cat_val)
        qs = qs.filter(category__iexact=target_cat)

    # 2. Lọc Trạng thái (Còn sách / Hết sách)
    if available is not None and str(available).strip() != "":
        avail_val = str(available).strip().lower()
        if avail_val == 'true':
            qs = qs.filter(available__gt=0)
        elif avail_val == 'false':
            qs = qs.filter(available__lte=0)

    # 3. Sắp xếp (Khớp chính xác trường published_year trong models.py)
    sort_map = {
        'title': 'title',
        '-title': '-title',
        'author': 'author',
        '-author': '-author',
        'year': 'published_year',
        '-year': '-published_year',
        'available': 'available',
        '-available': '-available',
    }

    if sort in sort_map:
        qs = qs.order_by(sort_map[sort])

    return qs

# Tìm kiếm sách theo tiêu đề
def search_books_by_title(title, category=None, available=None, sort=None):
    if title:
        qs = selector.search_books_by_title(title)
    else:
        qs = get_all_books()

    if category:
        qs = qs.filter(category=category)

    if available is not None:
        if isinstance(available, str):
            available_bool = available.lower() == 'true'
        else:
            available_bool = bool(available)

        if available_bool:
            qs = qs.filter(available__gt=0)
        else:
            qs = qs.filter(available__lte=0)

    sort_map = {
        'title': 'title',
        '-title': '-title',
        'author': 'author',
        '-author': '-author',
        'year': 'published_year',
        '-year': '-published_year',
        'available': 'available',
        '-available': '-available',
    }

    if sort in sort_map:
        qs = qs.order_by(sort_map[sort])

    return qs
def process_due_date_reminders(days_before=2):
    """
    Quét các phiếu mượn sắp đến hạn (cách ngày hiện tại `days_before` ngày) hoặc quá hạn
    """
    today = timezone.now().date()
    
    target_due_date = today + timedelta(days=days_before)
    upcoming_borrows = Borrow.objects.filter(due_date=target_due_date, return_date__isnull=True).select_related('user', 'book')
    
    count_sent = 0
    for borrow in upcoming_borrows:
        if borrow.user.email:
            send_mail(
                subject='[Thư viện] Nhắc nhở hạn trả sách',
                message=f'Chào {borrow.user.username},\n\nCuốn sách "{borrow.book.title}" của bạn sẽ đến hạn trả vào ngày {borrow.due_date}. Vui lòng sắp xếp trả sách đúng hạn nhé!',
                from_email=None,
                recipient_list=[borrow.user.email],
                fail_silently=True,
            )
            count_sent += 1

    overdue_borrows = Borrow.objects.filter(due_date__lt=today, return_date__isnull=True).select_related('user', 'book')
    for borrow in overdue_borrows:
        if borrow.user.email:
            send_mail(
                subject='[Thư viện] Thông báo quá hạn trả sách',
                message=f'Chào {borrow.user.username},\n\nCuốn sách "{borrow.book.title}" của bạn đã quá hạn trả từ ngày {borrow.due_date}. Vui lòng mang trả sách sớm cho thư viện!',
                from_email=None,
                recipient_list=[borrow.user.email],
                fail_silently=True,
            )
            count_sent += 1

    return f"Đã gửi thành công {count_sent} thông báo (Sắp đến hạn: {days_before} ngày tới & Quá hạn)."