from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from . import excel_import
from .models import PersonIdGroupAssignment, PhotoManagementGroup


def _can_excel_bulk_import(user) -> bool:
    """超级用户、管理员或教学秘书可使用 Excel 批量导入。"""
    if not user.is_authenticated or not user.is_staff:
        return False
    if user.is_superuser:
        return True
    return getattr(user, 'role', None) in ('admin', 'secretary')


@admin.register(PhotoManagementGroup)
class PhotoManagementGroupAdmin(admin.ModelAdmin):
    change_list_template = 'admin/photo_access/photomanagementgroup/change_list.html'
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code')

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                'download-template/',
                self.admin_site.admin_view(self.download_template),
                name='%s_%s_download_template' % info,
            ),
            path(
                'import-xlsx/',
                self.admin_site.admin_view(self.import_xlsx),
                name='%s_%s_import_xlsx' % info,
            ),
        ]
        return custom + urls

    def download_template(self, request):
        if not self.has_view_permission(request):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        wb = excel_import.build_group_template_workbook()
        return excel_import.workbook_to_response(wb, '照片管理组导入模板.xlsx')

    def import_xlsx(self, request):
        if not _can_excel_bulk_import(request.user):
            messages.error(request, '仅超级管理员、管理员或教学秘书可从 Excel 批量导入管理组。')
            return redirect('admin:photo_access_photomanagementgroup_changelist')
        if not self.has_add_permission(request) or not self.has_change_permission(request):
            messages.error(request, '您没有本模型的添加或修改权限，无法导入。')
            return redirect('admin:photo_access_photomanagementgroup_changelist')
        if request.method != 'POST':
            return redirect('admin:photo_access_photomanagementgroup_changelist')
        f = request.FILES.get('excel_file')
        if not f:
            messages.error(request, '请选择 .xlsx 文件。')
            return redirect('admin:photo_access_photomanagementgroup_changelist')
        result = excel_import.import_groups_from_upload(f)
        if not result.get('ok') and result.get('error'):
            messages.error(request, result['error'])
        else:
            if result.get('errors'):
                for e in result['errors'][:30]:
                    messages.warning(request, e)
                if len(result['errors']) > 30:
                    messages.warning(request, f'另有 {len(result["errors"]) - 30} 条错误未显示。')
            messages.success(
                request,
                f'导入完成：新建 {result.get("created", 0)} 条，更新 {result.get("updated", 0)} 条。',
            )
        return redirect('admin:photo_access_photomanagementgroup_changelist')


@admin.register(PersonIdGroupAssignment)
class PersonIdGroupAssignmentAdmin(admin.ModelAdmin):
    change_list_template = 'admin/photo_access/personidgroupassignment/change_list.html'
    list_display = ('person_number', 'management_group', 'remark', 'updated_at')
    list_filter = ('management_group',)
    search_fields = ('person_number', 'remark')
    autocomplete_fields = ('management_group',)

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                'download-template/',
                self.admin_site.admin_view(self.download_template),
                name='%s_%s_download_template' % info,
            ),
            path(
                'import-xlsx/',
                self.admin_site.admin_view(self.import_xlsx),
                name='%s_%s_import_xlsx' % info,
            ),
        ]
        return custom + urls

    def download_template(self, request):
        if not self.has_view_permission(request):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        wb = excel_import.build_assignment_template_workbook()
        return excel_import.workbook_to_response(wb, '人员编号与组对应导入模板.xlsx')

    def import_xlsx(self, request):
        if not _can_excel_bulk_import(request.user):
            messages.error(request, '仅超级管理员、管理员或教学秘书可从 Excel 批量导入人员与组对应。')
            return redirect('admin:photo_access_personidgroupassignment_changelist')
        if not self.has_add_permission(request) or not self.has_change_permission(request):
            messages.error(request, '您没有本模型的添加或修改权限，无法导入。')
            return redirect('admin:photo_access_personidgroupassignment_changelist')
        if request.method != 'POST':
            return redirect('admin:photo_access_personidgroupassignment_changelist')
        f = request.FILES.get('excel_file')
        if not f:
            messages.error(request, '请选择 .xlsx 文件。')
            return redirect('admin:photo_access_personidgroupassignment_changelist')
        result = excel_import.import_assignments_from_upload(f)
        if not result.get('ok') and result.get('error'):
            messages.error(request, result['error'])
        else:
            if result.get('errors'):
                for e in result['errors'][:30]:
                    messages.warning(request, e)
                if len(result['errors']) > 30:
                    messages.warning(request, f'另有 {len(result["errors"]) - 30} 条错误未显示。')
            messages.success(
                request,
                f'导入完成：新建 {result.get("created", 0)} 条，更新 {result.get("updated", 0)} 条。',
            )
        return redirect('admin:photo_access_personidgroupassignment_changelist')
