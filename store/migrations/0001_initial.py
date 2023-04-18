# Generated by Django 4.1.7 on 2023-03-04 15:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Наименование категории')),
                ('image', models.ImageField(blank=True, null=True, upload_to='categories/', verbose_name='Изображения')),
                ('slug', models.SlugField(null=True, unique=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='store.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Наименование продукта')),
                ('price', models.FloatField(verbose_name='Цена')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('quantity', models.IntegerField(default=0, verbose_name='Количество на складе')),
                ('description', models.TextField(default='Здесь скоро будит описание', verbose_name='Описание товара')),
                ('slug', models.SlugField(null=True, unique=True)),
                ('size', models.IntegerField(default=30, verbose_name='Размер в мм')),
                ('color', models.CharField(default='Серебро', max_length=30, verbose_name='Цвет/Материал')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
            },
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/', verbose_name='Изображения')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='store.product')),
            ],
            options={
                'verbose_name': 'Изображение',
                'verbose_name_plural': 'Изображения товаров',
            },
        ),
    ]
