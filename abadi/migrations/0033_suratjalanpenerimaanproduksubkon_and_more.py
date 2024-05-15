# Generated by Django 4.1.4 on 2024-05-11 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('abadi', '0032_rename_kodeartikel_detailspkdisplay_kodedisplay'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuratJalanPenerimaanProdukSubkon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSuratJalan', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='SuratJalanPengirimanBahanBakuSubkon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('NoSuratJalan', models.CharField(max_length=255)),
                ('Tanggal', models.DateField()),
            ],
        ),
        migrations.RenameField(
            model_name='transaksisubkon',
            old_name='IDTransaksiSubkon',
            new_name='IDTransaksiProdukSubkon',
        ),
        migrations.CreateModel(
            name='TransaksiBahanBakuSubkon',
            fields=[
                ('IDTransaksiBahanBakuSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Tanggal', models.DateField()),
                ('Keterangan', models.CharField(max_length=225)),
                ('IDKodeBahanBaku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.bahanbakusubkon')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSuratJalanPengirimanBahanBakuSubkon',
            fields=[
                ('IDDetailSJPengirimanSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('KodeDisplay', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.display')),
                ('NoSuratJalan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.suratjalanpengirimanbahanbakusubkon')),
            ],
        ),
        migrations.CreateModel(
            name='DetailSuratJalanPenerimaanProdukSubkon',
            fields=[
                ('IDDetailSJPengirimanSubkon', models.AutoField(primary_key=True, serialize=False)),
                ('Jumlah', models.IntegerField()),
                ('Keterangan', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('KodeDisplay', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.display')),
                ('NoSuratJalan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='abadi.suratjalanpengirimanbahanbakusubkon')),
            ],
        ),
    ]