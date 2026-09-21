from django.contrib import admin
from .models import Hotel, Room, Booking, Review


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ['user', 'rating', 'comment']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'avg_rating', 'reviews_count', 'is_active']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'address']
    ordering = ['-created_at']
    inlines = [RoomInline, ReviewInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'room_number', 'room_type', 'price_per_night', 'capacity', 'is_available']
    list_filter = ['room_type', 'is_available', 'hotel']
    search_fields = ['room_number', 'hotel__name']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'check_in', 'check_out', 'total_price', 'status']
    list_filter = ['status', 'check_in', 'check_out']
    search_fields = ['user__username', 'room__hotel__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'hotel', 'rating', 'created_at']
    list_filter = ['rating', 'hotel']
    search_fields = ['user__username', 'hotel__name', 'comment']
