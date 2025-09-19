# Generated manually to rename your_id to subject_id

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0011_crudesample_barcode_override_used_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='crudesample',
            old_name='your_id',
            new_name='subject_id',
        ),
        migrations.RenameField(
            model_name='historicalcrudesample',
            old_name='your_id',
            new_name='subject_id',
        ),
    ]