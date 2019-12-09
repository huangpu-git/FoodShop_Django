import math

from django.core.cache import cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect
from django.views import View
import jsonpickle

# Create your views here.
from django_redis import get_redis_connection
from goods.models import GoodsType, IndexGoodsBanner, IndexpromotionBanner, IndexTypeGoodsBanner, GoodsSKU, GoodsImage
from order.models import OrderGoods


class IndexView(View):
    def get(self, request):

        context = cache.get('index_page_data')
        # 判断缓存是否存在
        if context is None:
            # 获取商品的种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品展示信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销商品信息
            promotion_Banners = IndexpromotionBanner.objects.order_by('index')

            # 获取首页分类商品展示信息
            for type in types:
                # 获取首页分类商品的图片信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取首页分类商品的文字信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片信息与文字信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            # 组织上下文
            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_Banners': promotion_Banners
            }
        print("***")
        # 设置缓存，设置缓存为了多数用户都来访问，都调用数据库，加重数据的负担
        cache.set('index_page_data', context, 3600)  # index_page_data 是起的名字，context 缓存的内容，3600秒

        cart_count = 0
        # 获取session 中的user
        if 'user' in request.session:
            user = jsonpickle.loads(request.session.get('user'))
            con = get_redis_connection('default')  # 连接redis数据库
            cart_key = 'cart_%d' % user.id  # 用user表中的id 作为标记 表示一条记录
            cart_count = con.hlen(cart_key)  # 用 hlen 来获取redis 中 hash字段的数量


        # 更新上下文
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


class DetailView(View):
    '''商品详情页'''

    def get(self, request):
        # 获取当前商品ID
        goods_id = request.GET.get('goods_id')

        # 查询商品信息
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect('/index/')

        # 获取商品的种类信息
        types = GoodsType.objects.all()

        # 获取新品信息, exclude 是去除自己的这一商品
        new_skus = GoodsSKU.objects.filter(type=sku.type).exclude(id=sku.id).order_by('create_time')[:2]

        # 获取同一SPU规格的商品
        same_sku_spu = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)

        # 获取同一商品的其他图片
        sku_other_img = GoodsImage.objects.filter(sku=sku.id)

        # 获取商品的评论信息
        sku_order = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取购物车的数目
        cart_count = 0
        if 'user' in request.session:
            user = jsonpickle.loads(request.session.get('user'))
            con = get_redis_connection('default')  # 连接redis
            cart_key = 'cart_%d' % user.id  # 数据存储格式
            cart_count = con.hlen(cart_key)  # 获取字段的数目 即 购物车的数量

            '''
                添加用户的历史浏览记录
            '''
            history_key = 'history_%d' % user.id  # 设置一个数据格式

            # 移除列表中的goods_id 重复的元素
            con.lrem(history_key, 0, goods_id)  # lrem（key_name,count,values） 移除列表中与参数VALUES值相等的元素

            # 把 goods_id 插入到列表的左侧
            con.lpush(history_key, goods_id)  # lpush 将一个或者多值插入到列表头部

            # 只保留用户浏览记录的 5条数据
            con.ltrim(history_key, 0, 4)  # ltrim 对一个列表进行修剪 start ,end

        # 组织上下文
        context = {
            'sku': sku,
            'types': types,
            'new_skus': new_skus,
            'same_sku_spu': same_sku_spu,
            'sku_other_img': sku_other_img,
            'cart_count': cart_count,
            'sku_order': sku_order,
        }

        return render(request, 'detail.html', context)


class ListView(View):
    '''商品列表'''

    def get(self, request, type_id):
        # 获取种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect('/index/')

        # 获取商品的所有分类信息
        types = GoodsType.objects.all()

        # 按排序方式，获取商品分类信息
        sort = request.GET.get('sort')

        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')

        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')

        else:
            sort == 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('id')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中的商品的数目
        # 判断是否登录
        cart_count = 0
        if 'user' in request.session:
            user = jsonpickle.loads(request.session.get('user'))
            con = get_redis_connection('default')
            '''
                购物车是如何将商品加入的到cart_key ??
            '''
            cart_key = 'cart_%d' % user.id
            cart_count = con.hlen(cart_key)

        # 分页
        page_skus = Paginator(skus, 2)  # 每页显示两条数据

        num = request.GET.get('num', 1)  # 获取到 当前页面的页数 'num' 默认设置为1
        num = int(num)

        try:
            page_list = page_skus.page(num)  # 展示第 num 页的数据，即 所有的商品的sku
        except PageNotAnInteger:
            page_list = page_skus.page(1)  # 如果num 不是一个 integer 则取第一页
        except EmptyPage:
            page_list = page_skus.page(page_skus.num_pages)  # num_pages 总的分页数  如果超过最大页数则跳到最后一页

        # 设置页码
        start = num - math.ceil(4 / 2)
        if start < 1:
            start = 1

        end = start + 3
        if end > page_skus.num_pages:
            end = page_skus.num_pages

        if end <= 4:
            start = 1
        else:
            start = end - 3

        page_num = range(start, end + 1)  # 显示start 到 end+1 页

        # 组织上下文
        context = {
            'type': type,
            'types': types,
            'skus': page_list,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
            'page_num': page_num,
            'num': num
        }

        return render(request, 'list.html', context)
