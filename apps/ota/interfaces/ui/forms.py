from django import forms
from apps.ota.infrastructure.orm_models import MobileApp, AppUpdate

class MobileAppForm(forms.ModelForm):
    class Meta:
        model = MobileApp
        fields = ["name", "package_name", "description"]

class AppUpdateForm(forms.ModelForm):
    class Meta:
        model = AppUpdate
        fields = ["version", "apk_file", "force_update", "changelog"]
