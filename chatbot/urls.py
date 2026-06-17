# Tương tự như việc gom các Endpoint của một Controller cụ thể trong Spring Boot
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Cấu hình các "Route" (Endpoints) điều hướng đến các View hàm xử lý
    path("", views.dashboard, name='dashboard'),
    path("accounts/register/", views.register_view, name='register'),
    path("accounts/login/", views.login_view, name='login'),
    path("accounts/logout/", views.logout_view, name='logout'),
    path("accounts/profile/", views.profile_view, name='profile'),
    path("accounts/profile/edit/", views.profile_edit, name='profile_edit'),
    path("accounts/password/change/", views.change_password, name='change_password'),

    # Cart
    path("cart/", views.cart_view, name='cart'),
    path("cart/add/<int:book_id>/", views.add_to_cart, name='add_to_cart'),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name='remove_from_cart'),
    path("cart/update/<int:item_id>/", views.update_cart_item, name='update_cart_item'),
    path("checkout/", views.checkout, name='checkout'),
    path("orders/", views.order_history, name='order_history'),

    # Admin user management
    path("staff/users/", views.admin_user_list, name='admin_user_list'),
    path("staff/users/<int:user_id>/edit/", views.admin_user_edit, name='admin_user_edit'),
    path("staff/users/<int:user_id>/delete/", views.admin_user_delete, name='admin_user_delete'),

    # Admin book management (web UI for staff)
    path("staff/books/", views.admin_book_list, name='admin_book_list'),
    path("staff/books/add/", views.admin_book_add, name='admin_book_add'),
    path("staff/books/<int:book_id>/edit/", views.admin_book_edit, name='admin_book_edit'),
    path("staff/books/<int:book_id>/delete/", views.admin_book_delete, name='admin_book_delete'),
    path("staff/reports/", views.admin_reports, name='admin_reports'),
    path("staff/borrow-requests/", views.admin_borrow_requests, name='admin_borrow_requests'),
    path('staff/borrows/', views.admin_borrow_requests, name='admin_borrow_requests'),
    path('staff/borrows/<int:borrow_id>/approve/', views.admin_approve_borrow, name='admin_approve_borrow'),
    path('staff/borrows/<int:borrow_id>/reject/', views.admin_reject_borrow, name='admin_reject_borrow'),

    path("books/", views.books, name="books"),
    path("books/<int:book_id>/", views.book_details, name="book_detail"),
    path("books/<int:book_id>/borrow/", views.book_borrow, name="book_borrow"),
    path("books/<int:book_id>/favorite/", views.book_favorite, name="book_favorite"),
    path("books/<int:book_id>/review/", views.add_review, name="add_review"),
    path("books/search/", views.book_search, name="book_search"),
    path("borrowed/", views.borrowed, name="borrowed"),
    path("favorites/", views.favorites, name="favorites"),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    path('api/chat/', views.api_chat_bot, name='api_chat_bot'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
