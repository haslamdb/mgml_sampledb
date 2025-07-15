# Generated manually to enforce parent relationships

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sampletracking', '0005_alter_aliquot_parent_barcode_alter_extract_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aliquot',
            name='parent_barcode',
            field=models.ForeignKey(help_text='The crude sample this aliquot was derived from', on_delete=django.db.models.deletion.PROTECT, related_name='aliquots', to='sampletracking.crudesample', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='extract',
            name='parent',
            field=models.ForeignKey(help_text='The aliquot this extract was derived from', on_delete=django.db.models.deletion.PROTECT, related_name='extracts', to='sampletracking.aliquot', to_field='barcode'),
        ),
        migrations.AlterField(
            model_name='sequencelibrary',
            name='parent',
            field=models.ForeignKey(help_text='The extract this library was derived from', on_delete=django.db.models.deletion.PROTECT, related_name='libraries', to='sampletracking.extract'),
        ),
    ]