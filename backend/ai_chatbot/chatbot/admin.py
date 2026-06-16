# Register your models here.
# chatbot/admin.py

from django.contrib import admin
from .models import Book, Borrow, Favorite

admin.site.register(Book)
admin.site.register(Borrow)
admin.site.register(Favorite)