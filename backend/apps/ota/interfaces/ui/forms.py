from django import forms
from apps.ota.infrastructure.orm_models import MobileApp, AppUpdate


class MobileAppForm(forms.ModelForm):
    class Meta:
        model = MobileApp
        fields = ["name", "package_name", "description", "icon"]


class AppUpdateForm(forms.ModelForm):
    class Meta:
        model = AppUpdate
        fields = ["version", "apk_file", "force_update", "changelog"]


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    is_staff = forms.BooleanField(required=False, initial=True, label="Staff (can access dashboard)")
    is_superuser = forms.BooleanField(required=False, label="Superuser (full access)")


class UserEditForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    is_staff = forms.BooleanField(required=False, label="Staff (can access dashboard)")
    is_superuser = forms.BooleanField(required=False, label="Superuser (full access)")
    is_active = forms.BooleanField(required=False, initial=True, label="Active")
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="New password",
        help_text="Leave blank to keep current password.",
    )
