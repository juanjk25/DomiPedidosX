from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    BranchListView,
    CustomerListView,
    SedeHorarioView,
    MeView,
    OrderListCreateView,
    CustomerOrderCancelView,
    OrderStatusView,
    RegisterView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TeamMemberStatusView,
    TeamMemberListCreateView,
    TeamMemberAuditListView,
    CustomTokenObtainPairView,
    
)
from .kitchen_views import KitchenOrderQueueView
from .order_status_views import OrderStatusUpdateView

from .catalog_views import (
    PublicCategoryListView,
    PublicProductListView,
    ManagedProductListView,
    ManagedProductDetailView,
    ManagedCategoryListView,
    ManagedBranchListView,
    ManagedCategoryDetailView,
)
from .inventory_views import (
    ManagedInventoryListCreateView,
    ManagedInventoryDetailView,
    ManagedInventoryDisableView,
)

urlpatterns = [
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login-no-slash"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("usuarios/", RegisterView.as_view(), name="customer-register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/password-change/", PasswordChangeView.as_view(), name="password-change"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("me/", MeView.as_view(), name="me"),
    path("customers/", CustomerListView.as_view(), name="customers"),
    path("branches/", BranchListView.as_view(), name="branches"),
    path("branches/<int:pk>/horario/", SedeHorarioView.as_view(), name="branch-schedule"),
    path("categories/", PublicCategoryListView.as_view(), name="categories"),
    path("products/", PublicProductListView.as_view(), name="products"),
    path("management/branches/", ManagedBranchListView.as_view(), name="managed-branches"),
    path("management/categories/", ManagedCategoryListView.as_view(), name="managed-categories"),
    path("management/categories/<int:pk>/", ManagedCategoryDetailView.as_view(), name="managed-category"),
    path("management/products/", ManagedProductListView.as_view(), name="managed-products"),
    path("management/products/<int:pk>/", ManagedProductDetailView.as_view(), name="managed-product"),
    path("management/inventory/", ManagedInventoryListCreateView.as_view(), name="managed-inventory"),
    path("management/inventory/<int:pk>/", ManagedInventoryDetailView.as_view(), name="managed-inventory-detail"),
    path("management/inventory/<int:pk>/disable/", ManagedInventoryDisableView.as_view(), name="managed-inventory-disable"),
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("pedidos/cocina/", KitchenOrderQueueView.as_view(), name="kitchen-order-queue"),
    path("pedidos/<int:pk>/estado/", OrderStatusUpdateView.as_view(), name="order-status-update"),
    path("orders/<int:pk>/cancel/", CustomerOrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:pk>/status/", OrderStatusView.as_view(), name="order-status"),
    path("team-members/", TeamMemberListCreateView.as_view(), name="team-members"),
    path("team-members/<int:pk>/status/", TeamMemberStatusView.as_view(), name="team-member-status"),
    path("team-members/audit/", TeamMemberAuditListView.as_view(), name="team-member-audit"),
]