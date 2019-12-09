from cart import views
from django.urls import path

urlpatterns = [
    path('add/', views.CartAdd.as_view()),  # 加入购物车路由
    path('info/', views.CartInfo.as_view()),  # 购物车页面
    path('update/', views.CartUpdate.as_view()),  # 创建一个ajax 视图，改变购物车商品的数量
    path('delete/', views.CartDel.as_view()),  # 购物车商品删除

]
