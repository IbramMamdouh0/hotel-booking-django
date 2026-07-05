from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class Hotel(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم الفندق")
    description = models.TextField(verbose_name="الوصف")
    address = models.CharField(max_length=300, verbose_name="العنوان")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    website = models.URLField(blank=True, verbose_name="الموقع الإلكتروني")
    image = models.URLField(blank=True, verbose_name="رابط الصورة")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3, verbose_name="التقييم"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "فندق"
        verbose_name_plural = "الفنادق"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def avg_rating(self):
        result = self.reviews.aggregate(avg=Avg('rating'))
        return round(result['avg'], 1) if result['avg'] else self.rating

    def reviews_count(self):
        return self.reviews.count()


class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'غرفة مفردة'),
        ('double', 'غرفة مزدوجة'),
        ('suite', 'جناح'),
        ('deluxe', 'ديلوكس'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name="الفندق")
    room_number = models.CharField(max_length=10, verbose_name="رقم الغرفة")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, verbose_name="نوع الغرفة")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر لليلة")
    capacity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="السعة (عدد الأشخاص)")
    description = models.TextField(blank=True, verbose_name="الوصف")
    is_available = models.BooleanField(default=True, verbose_name="متاحة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "غرفة"
        verbose_name_plural = "الغرف"
        ordering = ['room_number']

    def __str__(self):
        return f"{self.hotel.name} - غرفة {self.room_number} ({self.get_room_type_display()})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('cancelled', 'ملغي'),
        ('completed', 'مكتمل'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name="المستخدم")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="الغرفة")
    check_in = models.DateField(verbose_name="تاريخ الوصول")
    check_out = models.DateField(verbose_name="تاريخ المغادرة")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر الإجمالي")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', verbose_name="الحالة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ['-created_at']

    def __str__(self):
        return f"حجز {self.user.username} - {self.room}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="المستخدم")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews', verbose_name="الفندق")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="التقييم")
    comment = models.TextField(verbose_name="التعليق")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        ordering = ['-created_at']
        unique_together = ['user', 'hotel']

    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} ({self.rating}⭐)"
