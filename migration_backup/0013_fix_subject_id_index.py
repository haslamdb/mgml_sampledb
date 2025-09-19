# Generated manually to fix index issue

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0012_rename_your_id_to_subject_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update the field definition
        migrations.AlterField(
            model_name='crudesample',
            name='subject_id',
            field=models.CharField(help_text='Identifier provided by the submitter', max_length=50, verbose_name='Subject ID'),
        ),
        migrations.AlterField(
            model_name='historicalcrudesample',
            name='subject_id',
            field=models.CharField(help_text='Identifier provided by the submitter', max_length=50, verbose_name='Subject ID'),
        ),
    ]