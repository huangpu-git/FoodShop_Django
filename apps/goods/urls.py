from django.urls import path
from goods import views

urlpatterns = [
    path('index/', views.IndexView.as_view()),  # 首页
    path('detail/', views.DetailView.as_view()), # 商品详情页
    path('list/<type_id>/',views.ListView.as_view()), # 商品的列表
]
