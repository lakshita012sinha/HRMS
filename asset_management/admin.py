from django.contrib import admin
from .models import Zone, AssetCategory, Asset, ZoneStock, StockMovement


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'zone_type', 'contact_person', 'is_active']
    list_filter = ['zone_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_code', 'name', 'category', 'unit', 'total_quantity', 'central_stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'asset_code']


@admin.register(ZoneStock)
class ZoneStockAdmin(admin.ModelAdmin):
    list_display = ['asset', 'zone', 'quantity', 'last_updated']
    list_filter = ['zone']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_number', 'movement_type', 'asset', 'quantity', 'from_zone', 'to_zone', 'status', 'movement_date']
    list_filter = ['movement_type', 'status']
    search_fields = ['movement_number', 'asset__name']
    readonly_fields = ['movement_number', 'created_at']
