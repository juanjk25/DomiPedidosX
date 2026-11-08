from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SedeListView, 
    ClienteListView, 
    ClientePedidoCancelView, 
    MeView, 
    PedidoListCreateView, 
    PedidoStatusView, 
    ProductoListView, 
    RegisterView,
    CustomTokenObtainPairView
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    
    # Rutas eliminadas: addresses/ y categories/ (ya no existen en los modelos)
    
    path("customers/", ClienteListView.as_view(), name="customers"),
    path("branches/", SedeListView.as_view(), name="branches"),
    path("products/", ProductoListView.as_view(), name="products"),
    
    path("orders/", PedidoListCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/cancel/", ClientePedidoCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/status/", PedidoStatusView.as_view(), name="order-status"),
    
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]