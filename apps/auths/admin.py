from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.auths.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.auths.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    """CustomUser model admin configuration class"""

    model = CustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("email",)
    list_display = (
        "user_identity",
        "active_status",
        "staff_status",
        "posts_count",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    readonly_fields = ("last_login",)

    fieldsets = (
        (
            "Personal information",
            {
                "classes": ("tab",),
                "fields": ("email", "first_name", "last_name", "password"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": ("last_login",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Personal information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")

    @display(description="User", header=True)
    def user_identity(self, obj: CustomUser) -> tuple[str, str, str]:
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return f"{obj.first_name} {obj.last_name}", obj.email, initials

    @display(
        description="Active",
        label={
            True: "success",
            False: "danger",
        },
    )
    def active_status(self, obj: CustomUser) -> tuple[bool, str]:
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(
        description="Staff",
        label={
            True: "info",
            False: "warning",
        },
    )
    def staff_status(self, obj: CustomUser) -> tuple[bool, str]:
        return obj.is_staff, "Staff" if obj.is_staff else "Regular user"

    def get_queryset(self, request: HttpRequest) -> QuerySet[CustomUser]:
        queryset = super().get_queryset(request)
        return queryset.annotate(post_count=Count("post", distinct=True))

    @display(description="Posts", ordering="post_count")
    def posts_count(self, obj: CustomUser) -> int:
        return obj.post_count

    actions = ("activate_users", "deactivate_users")

    @admin.action(description="Activate selected users")
    def activate_users(
        self, request: HttpRequest, queryset: QuerySet[CustomUser]
    ) -> None:
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(
        self, request: HttpRequest, queryset: QuerySet[CustomUser]
    ) -> None:
        queryset.update(is_active=False)


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Use Unfold for the built-in groups admin."""

    pass
