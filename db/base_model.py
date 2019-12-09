from django.db import models


class BaseModel(models.Model):
    ''' 模型抽象类 '''
    '''由于每个模型需要以下3个公用字段，所以采用基类形式'''
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    class Meta:
        # 表明它是一个抽象的基类类，不写会报错
        abstract = True
