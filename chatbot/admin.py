# Register your models here.
# chatbot/admin.py

from django.contrib import admin
from .models import Book, Borrow, Favorite, Order, OrderItem, Review

admin.site.register(Book)
admin.site.register(Borrow)
admin.site.register(Favorite)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)