# Generated migration: add last_build_number to MobileApp and backfill from existing AppUpdate rows
from django.db import migrations, models


def backfill_last_build_number(apps, schema_editor):
    MobileApp = apps.get_model('ota', 'MobileApp')
    AppUpdate = apps.get_model('ota', 'AppUpdate')
    # For each app, compute max build_number and set last_build_number to that value (or 0)
    for app in MobileApp.objects.all():
        max_bn = (
            AppUpdate.objects.filter(app_id=app.pk)
            .aggregate(models.Max('build_number'))
            .get('build_number__max')
        )
        if max_bn is None:
            max_bn = 0
        app.last_build_number = max_bn
        app.save(update_fields=['last_build_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('ota', '0003_add_public_id_and_backfill'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileapp',
            name='last_build_number',
            field=models.IntegerField(default=0, help_text='Last allocated build number for this app (used for atomic allocation).'),
        ),
        migrations.RunPython(backfill_last_build_number, reverse_code=migrations.RunPython.noop),
    ]
