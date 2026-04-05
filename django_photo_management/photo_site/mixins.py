from django.contrib.auth.mixins import LoginRequiredMixin


class SiteLoginRequiredMixin(LoginRequiredMixin):
    login_url = '/login/'
