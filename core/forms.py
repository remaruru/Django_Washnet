import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'phone_number', 'address')

    def __init__(self, *args, **kwargs):
        # Extract the user requesting the form creation for RBAC verification
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Remove ADMIN from the available choices
        if 'role' in self.fields:
            self.fields['role'].choices = [
                choice for choice in User.RoleChoices.choices 
                if choice[0] != User.RoleChoices.ADMIN
            ]
        
        # Globally inject the standard `.clay-input` system styles across default widgets
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'clay-input'})

    def clean_password2(self):
        """Enforce password strength rules on both the admin add-user form and all UserCreationForm subclasses."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        # Let Django's built-in matching check run first
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")

        if password1:
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password1):
                raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
            if not re.search(r'[a-z]', password1):
                raise ValidationError("Password must contain at least one lowercase letter (a-z).")
            if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'"\\|,.<>/?`~]', password1):
                raise ValidationError("Password must contain at least one symbol (e.g. ! @ # $ % ^ & *).")

        return password2

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == User.RoleChoices.ADMIN:
            raise ValidationError("Creating an Admin account from this dashboard is not permitted.")
        return role

    def save(self, commit=True):
        # Extract the new user instance but halt saving instantly to ensure security defaults
        user = super().save(commit=False)
        
        # Ensure new spawned accounts never gain admin privileges
        user.is_staff = False
        user.is_superuser = False
            
        if commit:
            user.save()
        return user
