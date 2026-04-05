from django.db import models


class SystemConfig(models.Model):
    key = models.CharField('配置键', max_length=100, unique=True)
    value = models.CharField('配置值', max_length=500)
    description = models.TextField('说明', blank=True)

    class Meta:
        verbose_name = '系统配置项'
        verbose_name_plural = '系统配置项'

    def __str__(self):
        return self.key
