from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='用户',
    )
    action = models.CharField('操作', max_length=200)
    details = models.JSONField('详情', default=dict)
    ip_address = models.GenericIPAddressField('IP 地址', null=True)
    timestamp = models.DateTimeField('时间', auto_now_add=True)

    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'
        ordering = ('-timestamp',)
