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
from .models import Book, Borrow, Favorite

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
def get_filtered_books(category=None, available=None, sort=None):
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