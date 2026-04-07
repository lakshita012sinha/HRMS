from django.urls import path
from .views import (
    ZoneListCreateView, ZoneDetailView,
    AssetCategoryListCreateView, AssetCategoryDetailView,
    AssetListCreateView, AssetDetailView,
    ZoneStockListView,
    StockMovementListCreateView, StockMovementDetailView,
    AssetDashboardView,
)

app_name = 'asset_management'

urlpatterns = [
    # Dashboard
    path('dashboard/', AssetDashboardView.as_view(), name='dashboard'),

    # Zones
    path('zones/', ZoneListCreateView.as_view(), name='zone-list'),
    path('zones/<int:pk>/', ZoneDetailView.as_view(), name='zone-detail'),

    # Categories
    path('categories/', AssetCategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', AssetCategoryDetailView.as_view(), name='category-detail'),

    # Assets
    path('assets/', AssetListCreateView.as_view(), name='asset-list'),
    path('assets/<int:pk>/', AssetDetailView.as_view(), name='asset-detail'),

    # Zone stock (read-only, filterable by ?zone=<id> or ?asset=<id>)
    path('stock/', ZoneStockListView.as_view(), name='zone-stock'),

    # Movements
    path('movements/', StockMovementListCreateView.as_view(), name='movement-list'),
    path('movements/<int:pk>/', StockMovementDetailView.as_view(), name='movement-detail'),
]
