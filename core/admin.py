"""
Django Admin Configuration for Core App
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django import forms
from .models import User


class UserCreationForm(forms.ModelForm):
    """Form for creating new users in admin"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('phone', 'username', 'user_type')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """Form for updating users in admin"""
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model
    """
    form = UserChangeForm
    add_form = UserCreationForm
    
    # Fields to display in the user list
    list_display = ('phone', 'username', 'user_type', 'assigned_sector', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    
    # Search functionality
    search_fields = ('phone', 'username', 'national_id', 'email')
    ordering = ('-created_at',)
    
    # Fieldsets for viewing/editing existing users
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('username', 'email', 'national_id', 'user_type', 'assigned_sector')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    # Fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'username', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    filter_horizontal = ()


# Register the User model with the custom admin
admin.site.register(User, UserAdmin)

# Unregister Group model since we're not using it
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass