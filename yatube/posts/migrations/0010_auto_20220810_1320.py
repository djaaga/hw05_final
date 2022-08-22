# Generated by Django 2.2.16 on 2022-08-10 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_auto_20220801_1223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(blank=True, help_text='Укажите адрес для страницы задачи. Используйте только латиницу, цифры, дефисы и знаки подчёркивания', max_length=200, unique=True, verbose_name='Адрес для страницы с задачей'),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(default='Значение по-умолчанию', help_text='Дайте короткое название задаче', max_length=200, verbose_name='Заголовок'),
        ),
    ]
