
from .models import Book


def get_all_books():
    return Book.objects.all()

def get_book_by_id(book_id):
    return Book.objects.filter(id=book_id).first()

def get_books_by_category(category):
    return Book.objects.filter(category=category)

def get_books_by_availability(is_available):
    return Book.objects.filter(available=is_available)

def search_books_by_title(title):
    return Book.objects.filter(title__icontains=title)