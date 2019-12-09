from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.RegisterView.as_view()),  # 注册
    path('login/', views.LoginView.as_view()),  # 注册
    path('login_out/', views.LoginOutView.as_view()),  # 注册
    path('active/<token>', views.ActiveView.as_view()),  # 邮件激活
    path('', views.UserInfo.as_view()),  # 用户中心-个人信息
    path('order/<num>', views.UserOrder.as_view()),  # 用户中心-全部订单
    path('address/', views.UserAddress.as_view()),  # 用户中心-收货地址
    path('code_user/', views.CodeUser.as_view()),  # 用户名验证
    path('code_email/', views.CodeEmail.as_view()),  # 验证邮箱

]
