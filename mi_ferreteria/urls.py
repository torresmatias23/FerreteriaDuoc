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
    path('', views.home, name='home'),
    path('productos/', views.productos, name='productos'),
    path('producto/<str:producto_id>/', views.detalle_producto, name='detalle_producto'),
    
    # Usuario
    path('Registro/', registrar_usuario, name="registro"),
    path('login/', login_usuario, name="login"),
    path('logout/', views.logout_usuario, name='logout'),
    path('recuperar_contrasena/', views.recuperar_contrasena, name='recuperar_contrasena'),
    
    # Navegación general
    path('contacto/', views.contacto, name='contacto'),
    path('nosotros/', views.nosotros, name='nosotros'),
    
    # Carrito y pedidos
    path('carrito/', views.carrito, name='carrito'),
    path('checkout/', views.checkout, name='checkout'),
    path('pagos/', views.pagos, name='pagos'),
    path('pedidos/', views.pedidos, name='pedidos'),
    
    # Admin y gestión
    path('dashboard_admin/', views.dashboard_admin, name='dashboard_admin'),
    path('ordenes_bodega/', views.ordenes_bodega, name='ordenes_bodega'),
    path('reportes/', views.reportes, name='reportes'),
    path('subir/', views.subir_producto, name='subir_producto'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path("usuarios/editar/", views.editar_usuario, name="editar_usuario"),
    path("usuarios/eliminar/", views.eliminar_usuario, name="eliminar_usuario"),
 
    path('perfil/', views.perfil, name='perfil'),
]
