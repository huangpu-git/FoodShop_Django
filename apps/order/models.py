from django.db import models
from db.base_model import BaseModel


# Create your models here.

class OrderInfo(BaseModel):
    '''订单信息模型类'''
    # 创建一个支付方式字典 作为以后判断用
    PAY_METHOD = {
        1: '货到付款',
        2: '微信支付',
        3: '支付宝',
        4: '银联支付'
    }

    PAY_METHOD_CHOICES = (
        (1, '货到付款'),
        (2, '微信支付'),
        (3, '支付宝'),
        (4, '银联支付'),
    )

    # 创建一个状态类，方便以后做判断用
    ORDER_STATUS = {
        1: '待支付',
        2: '代发货',
        3: '待收货',
        4: '待评价',
        5: '已完成'

    }
    ORDER_STATUS_CHOICES = (
        (1, '待支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成'),

    )

    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单ID')
    user = models.ForeignKey('user.User', verbose_name='用户', on_delete=models.CASCADE)
    addr = models.ForeignKey('user.Address', verbose_name='地址', on_delete=models.CASCADE)
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, verbose_name='支付方式', default=3)
    total_count = models.IntegerField(default=1,  verbose_name='商品数量')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品运费')
    order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='商品状态')
    trade_no = models.CharField(max_length=128, default='', verbose_name='支付编码')

    class Meta:
        db_table = 'pr_order_info'
        verbose_name = '订单详情'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_id


class OrderGoods(BaseModel):
    '''订单商品模型类'''
    order = models.ForeignKey('OrderInfo', verbose_name='订单', on_delete=models.CASCADE)
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name='商品数目')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    comment = models.CharField(max_length=256, default='', verbose_name='评论')

    class Meta:
        db_table = 'pr_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.comment

