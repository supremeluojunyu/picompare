# Generated manually to match existing database

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PhotoManagementGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='组名称')),
                ('code', models.SlugField(blank=True, default='', help_text='可选，英文简称', max_length=50, verbose_name='代码')),
                ('description', models.TextField(blank=True, verbose_name='说明')),
            ],
            options={
                'verbose_name': '照片管理组',
                'verbose_name_plural': '照片管理组',
            },
        ),
        migrations.CreateModel(
            name='PersonIdGroupAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_number', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='证件号/人员编号')),
                ('remark', models.CharField(blank=True, max_length=200, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'management_group',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='person_assignments',
                        to='photo_access.photomanagementgroup',
                        verbose_name='所属管理组',
                    ),
                ),
            ],
            options={
                'verbose_name': '人员编号与组对应',
                'verbose_name_plural': '人员编号与组对应',
            },
        ),
    ]
