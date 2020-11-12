# Generated by Django 3.1.3 on 2020-11-12 13:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='KanbanLabelColor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, unique=True)),
                ('hex_value', models.CharField(max_length=7, null=True, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='kanbanitemlabel',
            name='color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organizer.kanbanlabelcolor'),
        ),
    ]
