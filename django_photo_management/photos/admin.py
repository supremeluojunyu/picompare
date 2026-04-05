from django import forms
from django.contrib import admin

from .models import (
    OraclePhotoSyncConfig,
    PendingConfirmation,
    PersonPhoto,
    UploadBatch,
    UploadQualityFailureItem,
    UploadQualityReport,
    UploadValidationConfig,
)


def _is_superuser(request):
    u = getattr(request, 'user', None)
    return bool(u and u.is_active and u.is_superuser)


class OraclePhotoSyncConfigForm(forms.ModelForm):
    class Meta:
        model = OraclePhotoSyncConfig
        fields = '__all__'
        widgets = {
            'password': forms.PasswordInput(
                render_value=False,
                attrs={'autocomplete': 'new-password', 'placeholder': '留空表示不修改已保存密码'},
            ),
        }

    def clean_password(self):
        pwd = self.cleaned_data.get('password')
        if (pwd or '').strip():
            return pwd
        if self.instance.pk:
            return self.instance.password or ''
        return ''


@admin.register(OraclePhotoSyncConfig)
class OraclePhotoSyncConfigAdmin(admin.ModelAdmin):
    form = OraclePhotoSyncConfigForm
    list_display = ('id', 'enabled', 'host', 'table_name', 'updated_at')
    fieldsets = (
        ('同步策略', {'fields': ('enabled', 'uploader_must_opt_in', 'default_opt_in_checked')}),
        (
            'Oracle 连接',
            {'fields': ('host', 'port', 'service_name', 'username', 'password')},
        ),
        (
            '目标表与字段',
            {'fields': ('table_schema', 'table_name', 'person_key_column', 'photo_blob_column')},
        ),
    )

    def has_module_permission(self, request):
        return _is_superuser(request)

    def has_view_permission(self, request, obj=None):
        return _is_superuser(request)

    def has_add_permission(self, request):
        if not _is_superuser(request):
            return False
        return not OraclePhotoSyncConfig.objects.exists()

    def has_change_permission(self, request, obj=None):
        return _is_superuser(request)

    def has_delete_permission(self, request, obj=None):
        return _is_superuser(request)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(UploadValidationConfig)
class UploadValidationConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'max_file_size_mb', 'updated_at')


class UploadQualityFailureItemInline(admin.TabularInline):
    model = UploadQualityFailureItem
    extra = 0
    readonly_fields = ('person_number', 'issues')


@admin.register(UploadQualityReport)
class UploadQualityReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploader', 'created_at')
    inlines = [UploadQualityFailureItemInline]


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploader', 'status', 'total_count', 'start_time')


@admin.register(PersonPhoto)
class PersonPhotoAdmin(admin.ModelAdmin):
    list_display = ('person_number', 'upload_time', 'uploader', 'batch')
    search_fields = ('person_number',)


@admin.register(PendingConfirmation)
class PendingConfirmationAdmin(admin.ModelAdmin):
    list_display = ('person_number', 'confirmed', 'created_at')
