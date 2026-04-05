from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from photo_site.forms import SiteLoginForm
from photo_site.views import DashboardView, PendingPageView, SuperuserCryptoPageView, UploadPageView
from photos.report_views import UploadQualityReportView

admin.site.site_header = '昆明学院教务处学生照片采集系统'
admin.site.site_title = '昆明学院教务处学生照片采集系统'
admin.site.index_title = '数据与系统管理'


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path(
        'login/',
        LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=SiteLoginForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('captcha/', include('captcha.urls')),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/photos/', include('photos.urls')),
    path('api/configs/', include('configs.urls')),
    path('upload/', UploadPageView.as_view(), name='upload_page'),
    path(
        'upload/quality-report/<int:pk>/',
        UploadQualityReportView.as_view(),
        name='upload_quality_report',
    ),
    path('pending/', PendingPageView.as_view(), name='pending_page'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('superuser/crypto/', SuperuserCryptoPageView.as_view(), name='superuser_crypto_page'),
    path('health/', csrf_exempt(health_check)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
