from django.db import models

class Truyen(models.Model):
    ten_truyen = models.CharField(max_length=200)
    tac_gia = models.CharField(max_length=100)
    anh_bia = models.ImageField(upload_to='bia_truyen/', blank=True, null=True)
    
    the_loai = models.CharField(max_length=100, blank=True, null=True)
    
    so_luong = models.IntegerField(default=1) 
    
    tom_tat = models.TextField(blank=True, null=True) 
    
    def __str__(self):
        return self.ten_truyen