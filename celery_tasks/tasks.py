# 在系统环境变量中添加该模块到 （settings.py） 中

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'FoodShop.settings'

# 放到celery服务器上时添加的代码
import django

django.setup()

from celery import Celery
from FoodShop import settings
from django.core.mail import send_mail

# 1.指定broker(消息中间人)和backend(结果存储)
# redis没有密码
broker = 'redis://127.0.0.1:6379/9'
backend = 'redis://127.0.0.1:6379/8'
# 如果有密码
# broker = 'redis://:123456@127.0.0.1:6379/9'
# backend = 'redis://:123456@127.0.0.1:6379/8'

# 创建一个Celery 类的实例对象
app = Celery('celery_tasks.tasks', broker=broker, backend=backend)


# 定义任务函数
@app.task()
def send_register_active_email(to_email, user_name, token):
    subject = '欢迎注册良食速运'  # 主题
    message = ''  # 邮件的正文
    sender = settings.EMAIL_FROM  # 发件人（此平台）
    receiver = [to_email]  # 收件人
    html_message = '<h1>%s,欢迎您成为良食速运的注册会员</h1>请点击下面链接激活您的账户<br/>' \
                   '<a href="http://192.168.47.132:8000/user/active/%s">http://192.168.47.132:8000/user/active/%s</a>' % (
                       user_name, token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)

    '''
    在控制台启动监听命令：
        celery -A celery_tasks.tasks worker -l info -P eventlet
        
    '''