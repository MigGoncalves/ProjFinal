# Generated by Django 5.1.7 on 2025-06-14 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0004_instanciasimulador_seed'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilizador',
            name='nome',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
