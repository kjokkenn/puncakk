# Generated by Django 4.1.4 on 2024-05-17 13:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0039_transaksigudang_detailspkdisplay'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='penyesuaian',
            name='TanggalAkhir',
        ),
    ]
