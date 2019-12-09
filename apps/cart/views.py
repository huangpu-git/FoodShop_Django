import jsonpickle
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU


# Create your views here.


class CartAdd(View):
    '''加入购物车'''

    def post(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        user = jsonpickle.loads(request.session.get('user'))

        #  获取数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加购物车记录
        con = get_redis_connection('default')  # 连接redis
        cart_key = 'cart_%d' % user.id

        # 先尝试获取sku_id 的值
        # 如果sku_id 存在，要进行商品数量的累加的操作
        # 如果sku_id 不存在，返回None
        cart_count = con.hget(cart_key, sku_id)
        if cart_count:
            # 存在,进行累加操作
            count += int(cart_count)

        # 校验库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存不足'})

        # 添加购物车记录
        con.hset(cart_key, sku_id, count)

        # 计算用户购物车商品的数目
        total_count = con.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


class CartInfo(View):
    '''购物车页面'''

    def get(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return redirect('/user/login')
        user = jsonpickle.loads(request.session.get('user'))

        # 获取用户购物车中的商品信息
        con = get_redis_connection('default')  # 连接redis
        cart_key = 'cart_%d' % user.id
        # {'商品ID'：'商品的数量'}
        cart_dict = con.hgetall(cart_key)

        skus = []
        # 保存用户购物车中的商品总数和价格
        total_count = 0
        total_price = 0

        # 遍历获取商品信息
        for sku_id, count in cart_dict.items():
            # 根据商品ID，获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取商品的数量
            count = int(count)
            amount = sku.price * count
            # 动态给sku对象增加个属性amcount,保存商品的小计
            sku.amount = amount
            # 动态给sku对象增加个属性 count ,保存商品的数量
            sku.count = count
            # 添加
            skus.append(sku)

            # 累加计算商品的总数量和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {
            'total_count': total_count,
            'total_price': total_price,
            'skus': skus,
        }

        return render(request, 'cart.html', context)


class CartUpdate(View):
    '''购物车记录更新'''

    def post(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        user = jsonpickle.loads(request.session.get('user'))

        # 获取数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品的数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 1, 'errmsg': '商品数量有误'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 校验库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 业务处理：更新购物车记录
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        con.hset(cart_key, sku_id, count)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '更新成功'})


class CartDel(View):
    '''购物车记录删除'''

    def post(self, request):
        if 'user' not in request.session:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        user = jsonpickle.loads(request.session.get('user'))

        # 接受数据
        sku_id = request.POST.get('sku_id')

        # 校验数据
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品ID'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 业务处理：删除购物车记录
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 删除 hdel redis 中的数据
        con.hdel(cart_key, sku_id)

        # 返回应答
        return JsonResponse({'res': 3, 'message': '删除成功'})
