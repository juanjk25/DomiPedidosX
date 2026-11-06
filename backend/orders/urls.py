from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    BranchListView,
    CategoryListView,
    CustomerListView,
    MeView,
    OrderListCreateView,
    CustomerOrderCancelView,
    OrderStatusView,
    ProductListView,
    RegisterView,
    CustomTokenObtainPairView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("customers/", CustomerListView.as_view(), name="customers"),
    path("branches/", BranchListView.as_view(), name="branches"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("products/", ProductListView.as_view(), name="products"),
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/cancel/", CustomerOrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/status/", OrderStatusView.as_view(), name="order-status"),
]