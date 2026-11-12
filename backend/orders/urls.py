from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    BranchListView,
    SedeHorarioView,
    CategoryListView,
    CustomerListView,
    MeView,
    OrderListCreateView,
    CustomerOrderCancelView,
    OrderStatusView,
    ProductListView,
    RegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TeamMemberStatusView,
    CustomTokenObtainPairView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("usuarios/", RegisterView.as_view(), name="customer-register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("me/", MeView.as_view(), name="me"),
    path("customers/", CustomerListView.as_view(), name="customers"),
    path("branches/", BranchListView.as_view(), name="branches"),
    path("branches/<int:pk>/horario/", SedeHorarioView.as_view(), name="branch-schedule"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("products/", ProductListView.as_view(), name="products"),
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("orders/<int:pk>/cancel/", CustomerOrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/status/", OrderStatusView.as_view(), name="order-status"),
    path("team-members/<int:pk>/status/", TeamMemberStatusView.as_view(), name="team-member-status"),
]