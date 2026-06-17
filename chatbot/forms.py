from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Book, Review


class RegisterForm(UserCreationForm):
    last_name = forms.CharField(label="Họ", required=True)
    first_name = forms.CharField(label="Tên", required=True)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ("username", "last_name", "first_name", "email")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.last_name = self.cleaned_data['last_name']
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

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

class AdminAddUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_staff = forms.BooleanField(required=False, label="Quyền quản trị")

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff')