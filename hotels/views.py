from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Min
from datetime import date
from .models import Hotel, Room, Booking, Review
from .forms import RegisterForm, BookingForm, ReviewForm, HotelSearchForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def hotel_list(request):
    form = HotelSearchForm(request.GET)
    hotels = Hotel.objects.filter(is_active=True).annotate(min_price=Min('rooms__price_per_night'))

    if form.is_valid():
        q = form.cleaned_data.get('q')
        rating_min = form.cleaned_data.get('rating_min')
        price_max = form.cleaned_data.get('price_max')

        if q:
            hotels = hotels.filter(Q(name__icontains=q) | Q(address__icontains=q))
        if rating_min:
            hotels = hotels.filter(rating__gte=rating_min)
        if price_max:
            hotels = hotels.filter(rooms__price_per_night__lte=price_max).distinct()

    return render(request, 'hotels/hotel_list.html', {'hotels': hotels, 'form': form})


def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
    rooms = hotel.rooms.all()
    reviews = hotel.reviews.select_related('user').all()

    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, hotel=hotel).first()
    else:
        user_review = None

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.hotel = hotel
            review.save()
            messages.success(request, "تم إرسال تقييمك بنجاح")
            return redirect('hotel_detail', hotel_id=hotel.id)
    else:
        form = ReviewForm(instance=user_review)

    return render(request, 'hotels/hotel_detail.html', {
        'hotel': hotel, 'rooms': rooms, 'reviews': reviews,
        'form': form, 'user_review': user_review,
    })


def room_detail(request, hotel_id, room_id):
    hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
    room = get_object_or_404(Room, id=room_id, hotel=hotel)
    form = BookingForm()
    return render(request, 'hotels/room_detail.html', {'hotel': hotel, 'room': room, 'form': form})


@login_required
def create_booking(request, hotel_id, room_id):
    hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
    room = get_object_or_404(Room, id=room_id, hotel=hotel)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']

            if check_in <= date.today():
                messages.error(request, "تاريخ الوصول يجب أن يكون في المستقبل")
                return render(request, 'hotels/room_detail.html', {'hotel': hotel, 'room': room, 'form': form})

            nights = (check_out - check_in).days
            if nights < 1:
                messages.error(request, "يجب حجز ليلة واحدة على الأقل")
                return render(request, 'hotels/room_detail.html', {'hotel': hotel, 'room': room, 'form': form})

            overlapping = Booking.objects.filter(
                room=room, status__in=['pending', 'confirmed'],
                check_in__lt=check_out, check_out__gt=check_in,
            )
            if overlapping.exists():
                messages.error(request, "الغرفة غير متاحة في هذه التواريخ")
                return render(request, 'hotels/room_detail.html', {'hotel': hotel, 'room': room, 'form': form})

            total = room.price_per_night * nights
            Booking.objects.create(
                user=request.user, room=room,
                check_in=check_in, check_out=check_out, total_price=total,
            )
            messages.success(request, "🎉 تم تأكيد الحجز بنجاح!")
            return redirect('my_bookings')

    return render(request, 'hotels/room_detail.html', {'hotel': hotel, 'room': room, 'form': BookingForm()})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('room__hotel')
    return render(request, 'hotels/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "تم إلغاء الحجز")
    else:
        messages.error(request, "لا يمكن إلغاء هذا الحجز")
    return redirect('my_bookings')
