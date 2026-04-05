import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo_access', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='photo_scope_group',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='managed_users',
                to='photo_access.photomanagementgroup',
                verbose_name='照片数据管理组',
                help_text='非超级用户仅能操作本组已备案证件号的照片；由超级管理员指定。',
            ),
        ),
    ]
