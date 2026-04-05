from django.db import models


class PhotoManagementGroup(models.Model):
    name = models.CharField('组名称', max_length=100, unique=True)
    code = models.SlugField('代码', max_length=50, blank=True, default='', help_text='可选，英文简称')
    description = models.TextField('说明', blank=True)

    class Meta:
        verbose_name = '照片管理组'
        verbose_name_plural = '照片管理组'

    def __str__(self):
        return self.name


class PersonIdGroupAssignment(models.Model):
    person_number = models.CharField('证件号/人员编号', max_length=50, unique=True, db_index=True)
    management_group = models.ForeignKey(
        PhotoManagementGroup,
        on_delete=models.PROTECT,
        related_name='person_assignments',
        verbose_name='所属管理组',
    )
    remark = models.CharField('备注', max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '人员编号与组对应'
        verbose_name_plural = '人员编号与组对应'

    def __str__(self):
        return f'{self.person_number} → {self.management_group.name}'
