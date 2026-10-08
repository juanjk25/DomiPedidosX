from django.contrib import admin
from .models import Branch, Category, CustomerAddress, Order, OrderItem, Product, UserProfile
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product_name", "unit_price", "quantity"]
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "branch", "status", "total", "created_at"]
    list_filter = ["status", "branch", "created_at"]
    search_fields = ["customer__username", "customer__email", "delivery_address"]
    inlines = [OrderItemInline]
admin.site.register([Branch, Category, CustomerAddress, Product, UserProfile])
