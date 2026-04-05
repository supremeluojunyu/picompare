from django.db import migrations


def encrypt_legacy_oracle_passwords(apps, schema_editor):
    OraclePhotoSyncConfig = apps.get_model('photos', 'OraclePhotoSyncConfig')
    from photos.oracle_secret import encrypt_oracle_password_for_storage, is_stored_password_encrypted

    for row in OraclePhotoSyncConfig.objects.all().iterator():
        p = (row.password or '').strip()
        if not p or is_stored_password_encrypted(p):
            continue
        OraclePhotoSyncConfig.objects.filter(pk=row.pk).update(
            password=encrypt_oracle_password_for_storage(p)
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0006_oracle_password_encrypted_storage'),
    ]

    operations = [
        migrations.RunPython(encrypt_legacy_oracle_passwords, noop_reverse),
    ]
