"""
URL configuration for mi_ferreteria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from core import views
from core.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home, name='home'),
    path('productos/', views.productos, name='productos'),
    path('Registro/',registrar_usuario,name="registro"),
    path('login/',login_usuario,name="login"),
    path('logout/', views.logout_usuario, name='logout'),
    path('contacto/', views.contacto, name='contacto'),
    path('producto/<str:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('subir/', views.subir_producto, name='subir_producto'),
    path('dashboard_admin', views.dashboard_admin, name='dashboard_admin'),
]
