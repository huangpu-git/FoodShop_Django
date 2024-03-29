# Generated by Django 2.2.7 on 2019-11-30 06:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('order_id', models.CharField(max_length=128, primary_key=True, serialize=False, verbose_name='订单ID')),
                ('pay_method', models.SmallIntegerField(choices=[(1, '货到付款'), (2, '微信支付'), (3, '支付宝'), (4, '银联支付')], default=3, verbose_name='支付方式')),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品总价')),
                ('transit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品运费')),
                ('order_status', models.SmallIntegerField(choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成')], default=1, verbose_name='商品状态')),
                ('trade_no', models.CharField(default='', max_length=128, verbose_name='支付编码')),
                ('addr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Address', verbose_name='地址')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.User', verbose_name='用户')),
            ],
            options={
                'verbose_name': '订单详情',
                'verbose_name_plural': '订单详情',
                'db_table': 'pr_order_info',
            },
        ),
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('count', models.IntegerField(default=1, verbose_name='商品数目')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品价格')),
                ('comment', models.CharField(default='', max_length=256, verbose_name='评论')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order.OrderInfo', verbose_name='订单')),
                ('sku', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.GoodsSKU', verbose_name='商品SKU')),
            ],
            options={
                'verbose_name': '订单商品',
                'verbose_name_plural': '订单商品',
                'db_table': 'pr_order_goods',
            },
        ),
    ]
