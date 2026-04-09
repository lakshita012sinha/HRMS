from django.urls import path
from .views import (
    ZoneListCreateView, ZoneDetailView,
    AssetCategoryListCreateView, AssetCategoryDetailView,
    AssetListCreateView, AssetDetailView,
    ZoneStockListView,
    StockMovementListCreateView, StockMovementDetailView,
    AssetDashboardView,
    PurchaseListCreateView, PurchaseDetailView,
    ItemIssueListCreateView, ItemIssueDetailView,
)

urlpatterns = [
    path('dashboard/', AssetDashboardView.as_view(), name='dashboard'),
    path('zones/', ZoneListCreateView.as_view(), name='zone-list'),
    path('zones/<int:pk>/', ZoneDetailView.as_view(), name='zone-detail'),
    path('categories/', AssetCategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', AssetCategoryDetailView.as_view(), name='category-detail'),
    path('assets/', AssetListCreateView.as_view(), name='asset-list'),
    path('assets/<int:pk>/', AssetDetailView.as_view(), name='asset-detail'),
    path('stock/', ZoneStockListView.as_view(), name='zone-stock'),
    path('movements/', StockMovementListCreateView.as_view(), name='movement-list'),
    path('movements/<int:pk>/', StockMovementDetailView.as_view(), name='movement-detail'),
    path('purchases/', PurchaseListCreateView.as_view(), name='purchase-list'),
    path('purchases/<int:pk>/', PurchaseDetailView.as_view(), name='purchase-detail'),
    path('issues/', ItemIssueListCreateView.as_view(), name='issue-list'),
    path('issues/<int:pk>/', ItemIssueDetailView.as_view(), name='issue-detail'),
]
