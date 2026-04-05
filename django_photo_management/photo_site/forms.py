from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField


class SiteLoginForm(AuthenticationForm):
    captcha = CaptchaField(label='验证码')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = '用户名'
        self.fields['password'].label = '密码'
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'current-password'})
