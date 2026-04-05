import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .oracle_secret import encrypt_oracle_password_for_storage, is_stored_password_encrypted


class UploadValidationConfig(models.Model):
    max_file_size_mb = models.PositiveSmallIntegerField('单文件最大 MB', default=5)
    min_width = models.PositiveIntegerField('最小宽度（像素）', default=100)
    min_height = models.PositiveIntegerField('最小高度（像素）', default=100)
    max_width = models.PositiveIntegerField('最大宽度（像素）', default=4096)
    max_height = models.PositiveIntegerField('最大高度（像素）', default=4096)
    enable_clarity_check = models.BooleanField('启用清晰度校验', default=True)
    clarity_threshold = models.PositiveIntegerField('清晰度阈值（拉普拉斯方差）', default=100)
    background_color_rules = models.JSONField(
        '背景色规则',
        default=list,
        help_text='与 settings 中 BACKGROUND_ALLOWED_COLORS 相同结构，例如 [{"r_min":200,"r_max":255,"g_min":200,"g_max":255,"b_min":200,"b_max":255}]',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '上传照片校验规则'
        verbose_name_plural = '上传照片校验规则'

    def __str__(self):
        return f'上传规则（更新于 {self.updated_at:%Y-%m-%d %H:%M}）'


def _oracle_identifier(value, field_name: str) -> str:
    v = (value or '').strip()
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', v):
        raise ValidationError({field_name: '仅允许字母、数字、下划线，且不能以数字开头'})
    return v.upper()


class OraclePhotoSyncConfig(models.Model):
    """Oracle 照片同步（仅一条配置；由超级管理员维护）。"""

    enabled = models.BooleanField('启用 Oracle 同步', default=False)
    uploader_must_opt_in = models.BooleanField(
        '上传时需手动勾选才写入 Oracle',
        default=True,
        help_text='勾选：上传页显示选项，仅勾选时写入。取消勾选：每次本系统入库成功后自动写入 Oracle。',
    )
    default_opt_in_checked = models.BooleanField('上传页选项默认勾选', default=False)

    host = models.CharField('主机地址', max_length=255, blank=True)
    port = models.PositiveIntegerField('端口', default=1521)
    service_name = models.CharField('服务名 / Service Name', max_length=200, blank=True)
    username = models.CharField('用户名', max_length=128, blank=True)
    password = models.CharField(
        '密码（加密存储）',
        max_length=512,
        blank=True,
        help_text='以 Fernet 密文保存。超级管理员可在「秘钥配置」页（/superuser/crypto/）管理密钥与导出备份；亦可设置环境变量 ORACLE_SYNC_FERNET_KEY。未配置独立密钥时由 SECRET_KEY 派生。',
    )

    table_schema = models.CharField(
        '表所在 Schema（可空）',
        max_length=128,
        blank=True,
        help_text='可空，表示使用连接用户的默认方案。',
    )
    table_name = models.CharField('表名', max_length=128, blank=True)
    person_key_column = models.CharField(
        '人员键字段名',
        max_length=128,
        blank=True,
        help_text='与上传文件名中人员编号对应的列（如学号、证件号），用于 WHERE 条件。',
    )
    photo_blob_column = models.CharField(
        '照片 BLOB 字段名',
        max_length=128,
        blank=True,
        help_text='写入照片二进制数据的列（BLOB 或 RAW 等可接受二进制类型）。',
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Oracle 照片同步配置'
        verbose_name_plural = 'Oracle 照片同步配置'

    def __str__(self):
        return f'Oracle 同步（{"开" if self.enabled else "关"} · {self.host or "未配置主机"}）'

    def save(self, *args, **kwargs):
        p = self.password or ''
        if p.strip() and not is_stored_password_encrypted(p):
            self.password = encrypt_oracle_password_for_storage(p)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not self.enabled:
            return
        errors = {}
        if not (self.host or '').strip():
            errors['host'] = '启用同步时主机地址不能为空'
        if not (self.service_name or '').strip():
            errors['service_name'] = '启用同步时服务名不能为空'
        if not (self.username or '').strip():
            errors['username'] = '启用同步时用户名不能为空'
        if not (self.password or '').strip():
            errors['password'] = '启用同步时密码不能为空'
        if not (self.table_name or '').strip():
            errors['table_name'] = '启用同步时表名不能为空'
        if not (self.person_key_column or '').strip():
            errors['person_key_column'] = '启用同步时人员键字段名不能为空'
        if not (self.photo_blob_column or '').strip():
            errors['photo_blob_column'] = '启用同步时照片 BLOB 字段名不能为空'
        if errors:
            raise ValidationError(errors)
        _oracle_identifier(self.table_name, 'table_name')
        _oracle_identifier(self.person_key_column, 'person_key_column')
        _oracle_identifier(self.photo_blob_column, 'photo_blob_column')
        if (self.table_schema or '').strip():
            _oracle_identifier(self.table_schema, 'table_schema')


class SuperuserCryptoSettings(models.Model):
    """单例（pk=1）：超级管理员在前端维护的 Oracle Fernet 密钥；环境变量 ORACLE_SYNC_FERNET_KEY 优先。"""

    oracle_sync_fernet_key = models.CharField(
        'Oracle Fernet 密钥',
        max_length=128,
        blank=True,
        default='',
        help_text='用于解密 Oracle 同步配置中的数据库密码；留空则使用 Django SECRET_KEY 派生密钥。',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '超级管理员密钥配置'
        verbose_name_plural = '超级管理员密钥配置'

    def __str__(self):
        return '密钥配置（前端）'


class UploadQualityReport(models.Model):
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='upload_quality_reports',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '上传质量问题报告'
        verbose_name_plural = '上传质量问题报告'


class UploadQualityFailureItem(models.Model):
    report = models.ForeignKey(UploadQualityReport, on_delete=models.CASCADE, related_name='items')
    person_number = models.CharField('人员编号', max_length=50)
    preview_image = models.BinaryField('问题照片预览')
    issues = models.JSONField('问题列表', default=list)

    class Meta:
        ordering = ['id']
        verbose_name = '上传失败条目'
        verbose_name_plural = '上传失败条目'


class UploadBatch(models.Model):
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='上传人',
    )
    start_time = models.DateTimeField('开始时间', auto_now_add=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    total_count = models.IntegerField('总数量', default=0)
    success_count = models.IntegerField('成功数量', default=0)
    fail_count = models.IntegerField('失败数量', default=0)
    status = models.CharField('状态', max_length=20, default='processing')
    retry_count = models.IntegerField('重试次数', default=0)
    max_retries = models.IntegerField('最大重试次数', default=3)
    last_error = models.TextField('最后错误信息', blank=True)

    class Meta:
        verbose_name = '上传批次'
        verbose_name_plural = '上传批次'
        ordering = ('-start_time',)


class PersonPhoto(models.Model):
    person_number = models.CharField('人员编号', max_length=50, db_index=True)
    photo_blob = models.BinaryField('照片数据')
    file_path = models.CharField('文件路径', max_length=500)
    upload_time = models.DateTimeField('上传时间', auto_now_add=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='上传人',
    )
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='上传批次',
    )
    similarity_score = models.FloatField('人脸相似度', null=True, blank=True)
    is_adjusted = models.BooleanField('是否经自动调整', default=False)
    adjust_details = models.JSONField('调整详情', default=dict)
    status = models.CharField('状态', max_length=20, default='confirmed')

    class Meta:
        verbose_name = '人员照片'
        verbose_name_plural = '人员照片'
        ordering = ('-upload_time',)


class PendingConfirmation(models.Model):
    original_image = models.BinaryField('原图')
    adjusted_image = models.BinaryField('调整后图像')
    person_number = models.CharField('人员编号', max_length=50)
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        verbose_name='上传批次',
    )
    adjust_reason = models.CharField('调整原因', max_length=200)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    confirmed = models.BooleanField('已确认', default=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='确认人',
    )

    class Meta:
        verbose_name = '待确认照片'
        verbose_name_plural = '待确认照片'
        ordering = ('-created_at',)
