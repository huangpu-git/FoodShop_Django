from datetime import datetime

import jsonpickle
from alipay import AliPay

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

# Create your views here.
from django_redis import get_redis_connection
import os
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from user.models import Address


class OrderPlace(View):
    '''提交订单页面显示'''

    def post(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return redirect('user/login')

        user = jsonpickle.loads(request.session.get('user'))

        # 接受数据
        sku_ids = request.POST.getlist('sku_ids')  # getlist  是获取一个列表的形式
        # 校验数据
        if not sku_ids:
            return redirect('/cart/info')
        # 连接redis
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []
        # 保存商品的总数量和总价格
        total_count = 0
        total_price = 0
        # 遍历sku_id获取用户的购买的商品信息
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户购买的商品数量
            count = con.hget(cart_key, sku_id)
            # 获取商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性count,保存商品的数量
            sku.count = int(count)
            # 动态给sku 增加一个属性amount,保存商品的小计
            sku.amount = amount
            # 追加列表
            skus.append(sku)
            # 累加计算商品的总件数与总数量
            total_count += int(count)
            total_price += amount

        # 运费：在实际开发中是一个子系统，在这里写死了
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收货地址
        address = Address.objects.filter(user=user)

        sku_ids = ','.join(sku_ids)  # 将列表形式的 [1,2] -> 1,2

        # 组织上下文
        context = {
            'skus': skus,
            'total_price': total_price,
            'total_count': total_count,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'address': address,
            'sku_ids': sku_ids,
        }

        # 返回应答
        return render(request, 'place_order.html', context)


class OrderCommit(View):
    '''订单的创建'''

    def post(self, request):
        # 判单用户是否登录
        if 'user' not in request.session:
            return JsonResponse({"res": 0, 'errmsg': '请先登录'})

        user = jsonpickle.loads(request.session.get('user'))

        # 接受数据
        addr_id = request.POST.get('addr_id')
        pay_method = int(request.POST.get('pay_method'))
        sku_ids = request.POST.get('sku_ids')

        # 校验数据
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '信息不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法订单支付方式'})

        # 检验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': "非法地址"})

        # 创建订单的核心业务
        # 订单ID：201912061613+用户ID
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数量和总金额
        total_count = 0
        total_price = 0

        # 向 order_info 表中添加数据
        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         pay_method=pay_method,
                                         total_price=total_price,
                                         transit_price=transit_price, )

        # 用户中有几个商品， 需要向 order_goods 表中添加几条记录
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 将字符串拆分成列表，进行遍历
        sku_ids = sku_ids.split(",")  # 1,2 -> [1,2]

        for sku_id in sku_ids:
            # 获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '此商品不存在'})

            # 获取redis中的商品数量
            count = con.hget(cart_key, sku_id)

            # 向order_goods 表中添加记录
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=count,
                price=sku.price)

            # 更新商品的库存与销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 累加计算商品的总数量和总价格
            amount = sku.price * int(count)
            total_count += int(count)
            total_price += amount

            # 更新订单表中的商品中的总价格和总数量
            order.total_price = total_price
            order.total_count = total_count
            order.save()

        # 清除用户购物车中对应的记录
        con.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})


class OrderPay(View):
    '''订单支付'''

    def post(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        user = jsonpickle.loads(request.session.get('user'))

        #  接受参数
        order_id = request.POST.get('order_id')

        # 校验order_id
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单ID'})

        # 校验订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 核心业务处理
        # pip install python-alipay-sdk
        # 初始化，调用Python.sdk链接支付宝

        # 私钥/公钥 路径
        private = os.path.join(os.path.dirname(__file__), 'app_private_key.pem')
        public = os.path.join(os.path.dirname(__file__), 'alipay_public_key.pem')
        alipay = AliPay(
            appid="2016101500695096",
            app_notify_url=None,  # 默认回调url
            alipay_public_key_string=open(public).read(),
            app_private_key_string=open(private).read(),

            # app_private_key_string=os.path.join(os.path.dirname(__file__), 'app_private_key.pem'),
            # app_public_key_path_string=os.path.join(os.path.dirname(__file__), 'alipay_public_key.pem'),

            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=False,  # 默认False
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_pay = order.total_count + order.transit_price  # 返回的是一个Decimal 格式的数据
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),  # 转成字符串格式
            subject="良食速运",
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class CheckPay(View):
    '''获取订单交易结果'''

    def post(self, request):
        # 判断用户是否登录
        if 'user' not in request.session:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        user = jsonpickle.loads(request.session.get('user'))

        #  接受参数
        order_id = request.POST.get('order_id')

        # 校验order_id
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单ID'})

        # 校验订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 核心业务处理
        # pip install python-alipay-sdk
        # 初始化，调用Python.sdk链接支付宝

        # 私钥/公钥 路径
        private = os.path.join(os.path.dirname(__file__), 'app_private_key.pem')
        public = os.path.join(os.path.dirname(__file__), 'alipay_public_key.pem')
        alipay = AliPay(
            appid="2016101500695096",
            app_notify_url=None,  # 默认回调url
            alipay_public_key_string=open(public).read(),
            app_private_key_string=open(private).read(),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=False,  # 默认False
        )
        while True:
            # 调用支付宝订单的查询接口
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')  # 网关返回码
            trade_status = response.get('trade_status')  # 交易状态
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 支付成功，TRADE_SUCCESS 交易成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.order_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功！'})

            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUY_PAY'):
                # 业务处理失败，可以等一会就成功
                #  等待买家付款
                import time
                time.sleep(3)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '交易失败'})


class OrderCommet(View):
    '''评论信息'''

    def get(self, request, order_id):
        # 判断是否登录
        if 'user' not in request.session:
            return redirect('/user/login')
        user = jsonpickle.loads(request.session.get('user'))

        # 校验订单数据
        if not order_id:
            return redirect('/user/order/1')

        # 校验订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return redirect('/user/oerder/1')

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品的信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)

        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.price * order_sku.count
            # 动态的给order_sku 增加属性 amount,保存商品小计
            order_sku.amount = amount

        # 动态给order增加属性order_skus,存在订单的商品信息
        order.order_skus = order_skus

        # 组织上下文
        context = {
            'order': order,
            'page': 'order'
        }

        return render(request, 'order_comment.html', context)

    def post(self, request, order_id):
        '''处理评论内容'''
        # 判断用户是否登录
        if 'user' not in request.session:
            return redirect('/user/login')
        user = jsonpickle.loads(request.session.get('user'))

        # 校验数据
        if not order_id:
            return redirect('/user/order/1')

        # 获取订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect('/user/order/1')

        # 获取评论数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get('sku_%d' % i)
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i)

            # 获取评论的商品信息
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                return redirect('/user/order/1')

            # 保存评论信息comment
            order_goods.comment = content
            order_goods.save()

        order.order_status = 5
        order.save()

        return redirect('/user/order/1')

