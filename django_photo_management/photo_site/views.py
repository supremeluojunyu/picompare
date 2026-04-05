from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView

from photos.oracle_sync import oracle_sync_template_context

from .mixins import SiteLoginRequiredMixin


class SuperuserCryptoPageView(SiteLoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'superuser_crypto.html'

    def test_func(self):
        u = self.request.user
        return bool(u.is_active and u.is_superuser)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseForbidden('仅超级管理员可访问秘钥配置与备份。')
        return super().handle_no_permission()


class DashboardView(SiteLoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'


class PendingPageView(SiteLoginRequiredMixin, TemplateView):
    template_name = 'pending_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(oracle_sync_template_context())
        return ctx


class UploadPageView(SiteLoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'upload_folder.html'

    def test_func(self):
        u = self.request.user
        if not u.is_active:
            return False
        if u.is_superuser:
            return True
        return getattr(u, 'role', None) in ('admin', 'secretary')

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseForbidden(
                '当前账号无权使用批量上传页面，请使用超级管理员、管理员或教学秘书账号。'
            )
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(oracle_sync_template_context())
        return ctx
