from unfold.forms import UserChangeForm
from unfold.widgets import UnfoldAdminPasswordWidget

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from apps.auths.models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=UnfoldAdminPasswordWidget,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=UnfoldAdminPasswordWidget,
    )

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")

    def clean_password2(self) -> str:
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")

        return password2

    def save(self, commit: bool = True) -> CustomUser:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            self.save_m2m()

        return user


class CustomUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(
        help_text="Raw passwords are not stored. Use the password change form to set a new password."
    )

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
