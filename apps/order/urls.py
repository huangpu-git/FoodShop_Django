from django.urls import path
from order import views

urlpatterns = [
    path('place/', views.OrderPlace.as_view()),  # 订单页
    path('commit/', views.OrderCommit.as_view()),  # 创建订单
    path('pay/', views.OrderPay.as_view()),  # 支付订单
    path('checkpay/', views.CheckPay.as_view()),  # 获取订单交易结果
    path('comment/<order_id>', views.OrderCommet.as_view()),  # 评价信息

]
