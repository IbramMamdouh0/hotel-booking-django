from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class BookingForm(forms.Form):
    check_in = forms.DateField(
        label="تاريخ الوصول",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    check_out = forms.DateField(
        label="تاريخ المغادرة",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError("تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول")
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {'rating': 'التقييم', 'comment': 'التعليق'}
        widgets = {
            'rating': forms.NumberInput(attrs={'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'class': 'star-range'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'اكتب رأيك عن الفندق...'}),
        }


class HotelSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={'placeholder': 'ابحث عن فندق أو مدينة...', 'class': 'search-input'})
    )
    rating_min = forms.IntegerField(
        required=False, label="أقل تقييم",
        widget=forms.NumberInput(attrs={'type': 'range', 'min': 1, 'max': 5, 'step': 1, 'class': 'filter-range'})
    )
    price_max = forms.DecimalField(
        required=False, label="أقصى سعر",
        widget=forms.NumberInput(attrs={'placeholder': 'السعر الأقصى', 'class': 'form-input', 'min': 0})
    )
