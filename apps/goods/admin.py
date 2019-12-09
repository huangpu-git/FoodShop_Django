from django.contrib import admin
from django.core.cache import cache
from goods.models import GoodsType, GoodsSKU, Goods, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, \
    IndexpromotionBanner

'''
 注册admin后台模型类

'''


# Register your models here.

# 缓存数据增加到后台
class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # 新增或者调用表中数据时调用
        super().save_model(request, obj, form, change)
        # 清除首页的缓存数据
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        # 删除表中数据时调用
        super().delete_model(request, obj)
        # 清除首页的缓存数据
        cache.delete('index_page_data')


admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(GoodsSKU, BaseModelAdmin)
admin.site.register(Goods, BaseModelAdmin)
admin.site.register(GoodsImage, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexTypeGoodsBanner, BaseModelAdmin)
admin.site.register(IndexpromotionBanner, BaseModelAdmin)
