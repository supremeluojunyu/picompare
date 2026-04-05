from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.forms import AdminAuthenticationForm
from captcha.fields import CaptchaField

from .models import User


class AdminLoginFormWithCaptcha(AdminAuthenticationForm):
    captcha = CaptchaField(label='验证码')

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = '用户名'
        self.fields['password'].label = '密码'


admin.site.login_form = AdminLoginFormWithCaptcha


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'photo_scope_group', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'photo_scope_group')
    search_fields = ('username', 'email', 'department')

    fieldsets = UserAdmin.fieldsets + (
        ('本校信息', {'fields': ('role', 'department')}),
        ('照片权限', {'fields': ('photo_scope_group',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('本校信息', {'fields': ('role', 'department')}),
        ('照片权限', {'fields': ('photo_scope_group',)}),
    )

    autocomplete_fields = ('photo_scope_group',)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and 'photo_scope_group' not in ro:
            ro.append('photo_scope_group')
        return ro
