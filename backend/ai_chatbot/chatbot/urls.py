# Tương tự như việc gom các Endpoint của một Controller cụ thể trong Spring Boot
from django.urls import path
from . import views

urlpatterns = [
    # Cấu hình các "Route" (Endpoints) điều hướng đến các View hàm xử lý
    path("", views.dashboard),
    path("books/", views.books, name="books"),
    path("books/<int:book_id>/", views.book_details, name="book_detail"),
    path("books/<int:book_id>/borrow/", views.book_borrow, name="book_borrow"),
    path("books/<int:book_id>/favorite/", views.book_favorite, name="book_favorite"),
    path("books/search/", views.book_search, name="book_search"),
    path("borrowed/", views.borrowed, name="borrowed"),
    path("favorites/", views.favorites, name="favorites"),
]
