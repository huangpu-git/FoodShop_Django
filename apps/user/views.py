import math
import re

import jsonpickle
from FoodShop import settings
from celery_tasks.tasks import send_register_active_email
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired

# Create your views here.
from order.models import OrderInfo, OrderGoods
from user.models import User, Address


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # form 表单提交的数据
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据 是否填写完整
        if not all([user_name, pwd, email]):
            return render(request, 'register.html', {'errmsg': "数据填写有误"})

        if cpwd != pwd:
            return render(request, 'register.html', {'errmsg': '两次输入的密码不一致！'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请勾选'})

        # 数据插入数据库
        try:
            user = User.objects.create(username=user_name, password=pwd, email=email)
        except User.DoesNotExist:
            return redirect('/user/register/')  # 重定向

        # 发送激活邮件，包含激活链接：http://localhost:8000/user/active/xxxx
        # 激活链接中需要包含用户身份信息，并且要把身份信息进行加密处理

        serializer = Serializer(settings.SECRET_KEY, 3600)  # 设置秘钥，设置有效时间
        info = {'user_id': user.id}  # 设置加密数据
        token = serializer.dumps(info)  # 加密数据
        token = token.decode('utf8')  # 用utf8 编码方式解决 bytes 格式问题

        # 发邮件
        '''
        subject = '欢迎注册良食速运'  # 主题
        message = ''  # 邮件的正文
        sender = settings.EMAIL_FROM  # 发件人（此平台）
        receiver = [email]  # 收件人
        html_message = '<h1>%s,欢迎您成为良食速运的注册会员</h1>请点击下面链接激活您的账户<br/>' \
                       '<a href="http://192.168.47.132:8000/user/active/%s">http://192.168.47.132:8000/user/active/%s</a>' % (
                           user_name, token, token)

        send_mail(subject, message, sender, receiver, html_message=html_message)
        '''
        # 改用celery 来处理异步处理邮件消息队列
        send_register_active_email(email, user_name, token)
        return redirect('/user/login')


class LoginView(View):
    '''登录'''

    def get(self, request):
        # 判断cookie 是否存在
        if 'username' in request.COOKIES and 'password' in request.COOKIES:
            username = request.COOKIES['username']
            password = request.COOKIES['password']
            checked = 'checked'  # 表示点选了记住密码

        else:
            username = ''
            password = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'password': password, 'checked': checked})

    def post(self, request):
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 校验数据
        # 如果数据为空
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整!'})

        # 如果不为空，去数据库查询登录数据
        try:
            user = User.objects.get(username=username, password=password)
        except User.DoesNotExist:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误！'})
        # 确定激活状态
        if user.is_active == False:
            return render(request, 'login.html', {'errmsg': '账号未激活！'})
        # 设置 session
        request.session['user'] = jsonpickle.dumps(user)
        res = redirect('/index/')

        # 判断是否记住用户名和密码，即 是否勾选了记住密码
        if remember == 'on':
            res.set_cookie('username', username, max_age=7200)
            res.set_cookie('password', password, max_age=7200)
        else:
            res.delete_cookie('username')
            res.delete_cookie('password')

        return res


class LoginOutView(View):
    '''退出登录'''

    def get(self, request):
        # 删除session
        del request.session['user']
        # request.session.flush()  # 将所有的session 都清空，不建议使用

        return redirect('/user/login/')


class ActiveView(View):
    def get(self, request, token):
        '''进行用户激活'''
        # 获取需要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)  # 设置秘钥，设置有效时间
        try:
            info = serializer.loads(token)
            user_id = info['user_id']
            user = User.objects.get(id=user_id)  # 取出这条数据
            user.is_active = 1  # 将 激活标识设置为 1
            user.save()  # 保存
        except SignatureExpired as e:
            '''设置激活时间已过期'''
            return HttpResponse("激活时间已过期")

        return redirect('/user/login/')


class CodeUser(View):
    '''数据库用户名验证'''

    def get(self, request):
        username = request.GET.get('username')
        # 从数据库中筛选出用户名
        user = User.objects.filter(username=username)
        flag = False
        passwd = ''
        # user 是一个列表集合 得遍历出里面的对象
        if user:
            flag = True
            for u in user:
                passwd = u.password
        return JsonResponse({'flag': flag, 'passwd': passwd})  # 返回 flag 到html


class CodeEmail(View):
    '''数据库邮箱验证'''

    def get(self, request):
        email = request.GET.get('email')
        user = User.objects.filter(email=email)
        flag = False
        if user:
            flag = True
        return JsonResponse({'flag': flag})


class UserInfo(View):
    '''用户中心-个人信息'''

    def get(self, request):
        # 用 session 判断是否登录，没有登录跳转到登录页面
        if 'user' not in request.session:
            return redirect('/user/login/')

        # 获取个人信息
        # 获取用户的默认收货地址
        user = jsonpickle.loads(request.session.get('user'))

        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        '''
            1、获取用户历史浏览记录, 储存到 redis 中，从redis 中获取
            2、储存格式是列表的形式，保存一条数据，不像 hash 那样需要拆分字符串影响效率
            3、在插入数据的时候，是从列表左侧插入 最新的浏览记录
        '''
        con = get_redis_connection('default')  # 连接redis 数据库
        history_key = 'history_%d' % user.id  # 设置数据格式

        # 获取用户最新浏览的 5个商品 id
        # lrange 从左边取值，从小标0开始拿到 4，共计5个
        # 返回列表
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询到用户浏览的商品具体的信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li
        }

        return render(request, 'user_center_info.html', context)


class UserOrder(View):
    '''用户中心-全部订单'''

    def get(self, request, num):
        # 用 session 判断是否登录，没有登录跳转到登录页面
        if 'user' not in request.session:
            return redirect('/user/login/')

        # 获取用户订单信息
        user = jsonpickle.loads(request.session.get('user'))
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历所有订单信息
        for order in orders:
            # 获取订单对应的订单商品信息
            order_skus = OrderGoods.objects.filter(order=order)

            # 遍历所有订单商品的信息
            for order_sku in order_skus:
                # 计算商品的小计
                amount = order_sku.price * order_sku.count
                order_sku.amount = amount

            # 动态给order添加属性，保存订单商品的信息
            order.order_skus = order_skus
            # 动态给order 添加属性，存在的订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 分页
        page_orders = Paginator(orders, 1)  # 每页显示两条数据
        num = int(num)

        try:
            page_list = page_orders.page(num)  # 展示第 num 页的数据，即 所有的商品的sku
        except PageNotAnInteger:
            page_list = page_orders.page(1)  # 如果num 不是一个 integer 则取第一页
        except EmptyPage:
            page_list = page_orders.page(page_orders.num_pages)  # num_pages 总的分页数  如果超过最大页数则跳到最后一页

        # 设置页码
        start = num - math.ceil(4 / 2)
        if start < 1:
            start = 1

        end = start + 3
        if end > page_orders.num_pages:
            end = page_orders.num_pages

        if end <= 4:
            start = 1
        else:
            start = end - 3

        page_num = range(start, end + 1)  # 显示start 到 end+1 页

        # 组织上下文
        context = {
            'orders': page_list,
            'num': num,
            'page_num': page_num,
            'page': 'order',
        }

        return render(request, 'user_center_order.html', context)


class UserAddress(View):
    '''用户中心-收货地址'''

    def get(self, request):
        # 用 session 判断是否登录，没有登录跳转到登录页面
        if 'user' not in request.session:
            return redirect('/user/login/')

        # 获取用户默认收货地址
        user = jsonpickle.loads(request.session.get('user'))

        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            # 不存在默认地址
            address = None
        # 组织上下文
        context = {
            'page': 'address',
            'address': address
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        # 接受数据
        receiver = request.POST.get('receiver', '')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, zip_code, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号码格式错误'})

        # 获取session
        if 'user' not in request.session:
            return redirect('/user/login/')

        user = jsonpickle.loads(request.session.get('user'))

        # 添加地址
        # 如果当前用户已经存在默认地址，添加的地址不作为默认收货地址，否则作为默认地址
        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        # 如果存在默认收货地址
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        try:
            Address.objects.create(receiver=receiver, addr=addr, zip_code=zip_code, phone=phone, user=user,
                                   is_default=is_default)
        except Address.DoesNotExist:
            return render(request, 'user_center_site.html', {'errmsg': '添加失败'})

        return redirect('/user/address/')
