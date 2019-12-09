from django.db import models
from db.base_model import BaseModel


# Create your models here.
# 用户/用户表
class User(BaseModel):
    '''用户模型类'''
    username = models.CharField(max_length=30, verbose_name='用户名')
    password = models.CharField(max_length=30, verbose_name='密码')
    email = models.CharField(max_length=30, verbose_name='邮箱')
    is_active = models.SmallIntegerField(default=0, verbose_name='激活标识')

    class Meta:
        db_table = 'pr_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


# 用户模块/地址表
class Address(BaseModel):
    '''地址类型类'''
    user = models.ForeignKey('User', verbose_name='所属账户',on_delete=models.CASCADE)
    receiver = models.CharField(max_length=30, verbose_name='收件人')
    addr = models.CharField(max_length=30, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否确认')

    class Meta:
        db_table = 'pr_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
