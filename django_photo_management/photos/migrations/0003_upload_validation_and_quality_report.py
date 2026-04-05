from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('photos', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadValidationConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_file_size_mb', models.PositiveSmallIntegerField(default=5, verbose_name='单文件最大 MB')),
                ('min_width', models.PositiveIntegerField(default=100, verbose_name='最小宽度（像素）')),
                ('min_height', models.PositiveIntegerField(default=100, verbose_name='最小高度（像素）')),
                ('max_width', models.PositiveIntegerField(default=4096, verbose_name='最大宽度（像素）')),
                ('max_height', models.PositiveIntegerField(default=4096, verbose_name='最大高度（像素）')),
                ('enable_clarity_check', models.BooleanField(default=True, verbose_name='启用清晰度校验')),
                ('clarity_threshold', models.PositiveIntegerField(default=100, verbose_name='清晰度阈值（拉普拉斯方差）')),
                ('background_color_rules', models.JSONField(default=list, verbose_name='背景色规则')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '上传照片校验规则',
                'verbose_name_plural': '上传照片校验规则',
            },
        ),
        migrations.CreateModel(
            name='UploadQualityReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'uploader',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='upload_quality_reports',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': '上传质量问题报告',
                'verbose_name_plural': '上传质量问题报告',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UploadQualityFailureItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_number', models.CharField(max_length=50, verbose_name='人员编号')),
                ('preview_image', models.BinaryField(verbose_name='问题照片预览')),
                ('issues', models.JSONField(default=list, verbose_name='问题列表')),
                (
                    'report',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='items',
                        to='photos.uploadqualityreport',
                    ),
                ),
            ],
            options={
                'verbose_name': '上传失败条目',
                'verbose_name_plural': '上传失败条目',
                'ordering': ['id'],
            },
        ),
    ]
