from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'address', 'profession', 'education']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class UserLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, 
                                     initial=False, 
                                     widget=forms.CheckboxInput())

ProfileForm = ProfileUpdateForm