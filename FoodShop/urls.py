"""FoodShop URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from FoodShop.settings import MEDIA_ROOT
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),  # 从服务器读取文件
    path('tinymce/', include('tinymce.urls')),  # 配置富文本编辑器路由
    path('search/', include('haystack.urls')),  # 全文检索框架
    path('', include('goods.urls'))
]
