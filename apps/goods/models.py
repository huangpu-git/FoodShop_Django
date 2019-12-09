from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


# Create your models here.
# 创建商品类别
class GoodsType(BaseModel):
    '''商品种类模型类'''
    name = models.CharField(max_length=30, verbose_name='种类名称')
    logo = models.CharField(max_length=30, verbose_name='标识')
    image = models.ImageField(upload_to='goods_type', verbose_name='商品种类名称')

    class Meta:
        db_table = 'pr_goods_type'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Goods(BaseModel):
    '''商品SPU模型类,SPU 是标准产品单位，如 iPhone x'''
    name = models.CharField(max_length=30, verbose_name='商品的SPU表')
    # 富文本类型：带有格式的文体 tinymce 富文本编辑器
    detail = HTMLField(blank=True, verbose_name='商品详情')

    class Meta:
        db_table = 'pr_goods'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSKU(BaseModel):
    '''商品的SKU表，SKU 商品的库存量单位 SPU 有多个SKU  如：iphone x 有 64G/128G 、有红色，白色等'''
    # 商品的状态，上架、下架
    status_choices = (
        (0, '上线'),
        (1, '下线')
    )
    type = models.ForeignKey('GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    goods = models.ForeignKey('Goods', verbose_name='商品的SPU', on_delete=models.CASCADE)
    name = models.CharField(max_length=30, verbose_name='商品名称')
    desc = models.CharField(max_length=256, verbose_name='商品的简介')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    unite = models.CharField(max_length=30, verbose_name='商品单位')
    image = models.ImageField(upload_to='goods_sku', verbose_name='商品图片')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    status = models.SmallIntegerField(default=1, choices=status_choices, verbose_name='状态')

    class Meta:
        db_table = 'pr_goods_sku'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsImage(BaseModel):
    '''商品图片模型类'''
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='goods_image', verbose_name='图片路径')

    class Meta:
        db_table = 'pr_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.name


class IndexGoodsBanner(BaseModel):
    '''首页轮播商品展示模型类'''
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='index_banner', verbose_name='图片')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'pr_index_banner'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.name


class IndexpromotionBanner(BaseModel):
    '''首页促销活动模型类'''
    name = models.CharField(max_length=30, verbose_name='活动名称')
    image = models.ImageField(upload_to='promo_banner', verbose_name='活动图片')
    url = models.URLField(verbose_name='活动链接')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    class Meta:
        db_table = 'pr_index_promotion'
        verbose_name = '主页促销活动表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class IndexTypeGoodsBanner(BaseModel):
    '''首页分类商品展示模型类'''
    DISPLAY_TYPE_CHOICES = (
        (0, '标题'),
        (1, '图片'),
    )

    type = models.ForeignKey('GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='商品展示标识')
    index = models.SmallIntegerField(default=0, verbose_name="展示顺序")

    class Meta:
        db_table = 'pr_index_type_goods'
        verbose_name = '首页分类商品展示表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.name
