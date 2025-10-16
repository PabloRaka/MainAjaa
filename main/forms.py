# main/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 

# Definisikan kelas CSS Tailwind untuk semua input agar konsisten
input_classes = "w-full bg-gray-800 border border-gray-700 rounded-md py-2 px-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors"

class CustomUserCreationForm(UserCreationForm):
    # Kita definisikan ulang field di sini untuk kontrol penuh
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': input_classes, 'placeholder': 'contoh@email.com'})
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email") # Kita tentukan urutannya

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tambahkan kelas CSS ke field yang diwarisi dari UserCreationForm
        self.fields['username'].widget.attrs.update({'class': input_classes, 'placeholder': 'Pilih username unik'})
        self.fields['password2'].widget.attrs.update({'class': input_classes})
        self.fields['password1'].widget.attrs.update({'class': input_classes})

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tambahkan kelas CSS ke field username dan password
        self.fields['username'].widget.attrs.update(
            {'class': input_classes, 'placeholder': 'Masukkan username Anda'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': input_classes, 'placeholder': 'Masukkan password'}
        )
