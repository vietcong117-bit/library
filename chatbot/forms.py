from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Book, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'published_year', 'category', 'quantity', 'available', 'price', 'image']


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.NumberInput(attrs={'type': 'number', 'min': 1, 'max': 5}))

    class Meta:
        model = Review
        fields = ['rating', 'comment']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
