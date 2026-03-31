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
