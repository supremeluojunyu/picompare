from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('secretary', '教学秘书'),
        ('user', '普通用户'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    photo_scope_group = models.ForeignKey(
        'photo_access.PhotoManagementGroup',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_users',
        verbose_name='照片数据管理组',
        help_text='非超级用户仅能操作本组已备案证件号的照片；由超级管理员指定。',
    )

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
