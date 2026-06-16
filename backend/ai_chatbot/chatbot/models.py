from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Book(models.Model):

    CATEGORY_CHOICES = [
        ("tech", "Công nghệ"),
        ("fiction", "Văn học"),
        ("selfhelp", "Tự phát triển"),
        ("business", "Kinh doanh"),
    ]

    title = models.CharField(max_length=200)

    author = models.CharField(max_length=100)

    description = models.TextField()

    published_year = models.IntegerField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='tech'
    )

    quantity = models.IntegerField(default=0)

    available = models.IntegerField(default=0)

    image = models.ImageField(upload_to='image/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    borrow_date = models.DateField()

    due_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} ❤️ {self.book.title}"
