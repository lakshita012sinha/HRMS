from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum
from .models import Zone, AssetCategory, Asset, ZoneStock, StockMovement
from .serializers import (
    ZoneSerializer, AssetCategorySerializer, AssetSerializer,
    ZoneStockSerializer, StockMovementSerializer
)


class IsHROrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role and \
               request.user.role.name in ['HR', 'ADMIN']


# ── Zones ──────────────────────────────────────────────────────────────────────

class ZoneListCreateView(generics.ListCreateAPIView):
    queryset = Zone.objects.filter(is_active=True)
    serializer_class = ZoneSerializer
    permission_classes = [IsHROrAdmin]


class ZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsHROrAdmin]


# ── Asset Categories ───────────────────────────────────────────────────────────

class AssetCategoryListCreateView(generics.ListCreateAPIView):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsHROrAdmin]


class AssetCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsHROrAdmin]


# ── Assets ─────────────────────────────────────────────────────────────────────

class AssetListCreateView(generics.ListCreateAPIView):
    queryset = Asset.objects.filter(is_active=True).select_related('category')
    serializer_class = AssetSerializer
    permission_classes = [IsHROrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsHROrAdmin]


# ── Zone Stock ─────────────────────────────────────────────────────────────────

class ZoneStockListView(generics.ListAPIView):
    """View current stock across all zones for all assets"""
    serializer_class = ZoneStockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ZoneStock.objects.select_related('asset', 'zone')
        zone_id = self.request.query_params.get('zone')
        asset_id = self.request.query_params.get('asset')
        if zone_id:
            qs = qs.filter(zone_id=zone_id)
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        return qs


# ── Stock Movements ────────────────────────────────────────────────────────────

class StockMovementListCreateView(generics.ListCreateAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [IsHROrAdmin]

    def get_queryset(self):
        qs = StockMovement.objects.select_related('asset', 'from_zone', 'to_zone', 'created_by')
        movement_type = self.request.query_params.get('type')
        asset_id = self.request.query_params.get('asset')
        zone_id = self.request.query_params.get('zone')
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        if zone_id:
            qs = qs.filter(from_zone_id=zone_id) | qs.filter(to_zone_id=zone_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class StockMovementDetailView(generics.RetrieveAPIView):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]


# ── Dashboard / Summary ────────────────────────────────────────────────────────

class AssetDashboardView(APIView):
    """Summary: total assets, central stock, zone-wise distribution"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_assets = Asset.objects.filter(is_active=True).count()
        total_central_stock = Asset.objects.filter(is_active=True).aggregate(
            total=Sum('central_stock')
        )['total'] or 0

        zone_summary = []
        for zone in Zone.objects.filter(is_active=True):
            stocks = ZoneStock.objects.filter(zone=zone).select_related('asset')
            zone_summary.append({
                'zone_id': zone.id,
                'zone_name': zone.name,
                'zone_type': zone.zone_type,
                'items': [
                    {
                        'asset_id': s.asset.id,
                        'asset_name': s.asset.name,
                        'asset_code': s.asset.asset_code,
                        'quantity': s.quantity,
                        'unit': s.asset.unit,
                    }
                    for s in stocks if s.quantity > 0
                ],
                'total_items': stocks.aggregate(t=Sum('quantity'))['t'] or 0,
            })

        recent_movements = StockMovementSerializer(
            StockMovement.objects.order_by('-created_at')[:10],
            many=True
        ).data

        return Response({
            'total_assets': total_assets,
            'total_central_stock': total_central_stock,
            'zone_summary': zone_summary,
            'recent_movements': recent_movements,
        })


# ── Purchases ──────────────────────────────────────────────────────────────────

class PurchaseListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsHROrAdmin]

    def get_serializer_class(self):
        from .serializers import PurchaseSerializer
        return PurchaseSerializer

    def get_queryset(self):
        from .models import Purchase
        return Purchase.objects.select_related('item', 'office').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PurchaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHROrAdmin]

    def get_serializer_class(self):
        from .serializers import PurchaseSerializer
        return PurchaseSerializer

    def get_queryset(self):
        from .models import Purchase
        return Purchase.objects.all()


class ItemIssueListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsHROrAdmin]

    def get_serializer_class(self):
        from .serializers import ItemIssueSerializer
        return ItemIssueSerializer

    def get_queryset(self):
        from .models import ItemIssue
        qs = ItemIssue.objects.select_related('item', 'office', 'employee')
        office = self.request.query_params.get('office')
        employee = self.request.query_params.get('employee')
        if office: qs = qs.filter(office_id=office)
        if employee: qs = qs.filter(employee_id=employee)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ItemIssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHROrAdmin]

    def get_serializer_class(self):
        from .serializers import ItemIssueSerializer
        return ItemIssueSerializer

    def get_queryset(self):
        from .models import ItemIssue
        return ItemIssue.objects.all()
