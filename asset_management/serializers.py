from rest_framework import serializers
from django.db import transaction
from .models import Zone, AssetCategory, Asset, ZoneStock, StockMovement


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'name', 'code', 'zone_type', 'address', 'city', 'state',
                  'contact_person', 'contact_number', 'is_active', 'created_at']


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = ['id', 'name', 'description', 'created_at']


class AssetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    item_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ['id', 'name', 'asset_code', 'category', 'category_name', 'description',
                  'unit', 'item_type', 'min_stock_level', 'item_image', 'item_image_url',
                  'total_quantity', 'central_stock', 'is_active', 'created_at']
        read_only_fields = ['asset_code', 'created_at']

    def get_item_image_url(self, obj):
        if obj.item_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.item_image.url)
            return obj.item_image.url
        return None

    def create(self, validated_data):
        # Auto-generate asset_code
        last = Asset.objects.order_by('id').last()
        next_id = (last.id + 1) if last else 1
        validated_data['asset_code'] = f"AST{str(next_id).zfill(5)}"
        # central_stock starts equal to total_quantity on creation
        validated_data.setdefault('central_stock', validated_data.get('total_quantity', 0))
        return super().create(validated_data)


class ZoneStockSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = ZoneStock
        fields = ['id', 'asset', 'asset_name', 'asset_code', 'zone', 'zone_name', 'quantity', 'last_updated']


class StockMovementSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    from_zone_name = serializers.CharField(source='from_zone.name', read_only=True)
    to_zone_name = serializers.CharField(source='to_zone.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.user_id', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'movement_number', 'movement_type', 'asset', 'asset_name',
            'quantity', 'from_zone', 'from_zone_name', 'to_zone', 'to_zone_name',
            'status', 'remarks', 'movement_date', 'received_date',
            'created_by', 'created_by_name', 'approved_by', 'created_at'
        ]
        read_only_fields = ['movement_number', 'created_by', 'created_at']

    def validate(self, attrs):
        movement_type = attrs.get('movement_type')
        asset = attrs.get('asset')
        quantity = attrs.get('quantity', 0)

        if movement_type == 'DISPATCH':
            if asset.central_stock < quantity:
                raise serializers.ValidationError(
                    f"Insufficient central stock. Available: {asset.central_stock}, Requested: {quantity}"
                )
            if not attrs.get('to_zone'):
                raise serializers.ValidationError("Dispatch requires a destination zone.")

        elif movement_type == 'RETURN':
            if not attrs.get('from_zone'):
                raise serializers.ValidationError("Return requires a source zone.")
            zone_stock = ZoneStock.objects.filter(asset=asset, zone=attrs['from_zone']).first()
            if not zone_stock or zone_stock.quantity < quantity:
                available = zone_stock.quantity if zone_stock else 0
                raise serializers.ValidationError(
                    f"Insufficient zone stock for return. Available at zone: {available}, Requested: {quantity}"
                )

        elif movement_type == 'TRANSFER':
            if not attrs.get('from_zone') or not attrs.get('to_zone'):
                raise serializers.ValidationError("Transfer requires both source and destination zones.")
            zone_stock = ZoneStock.objects.filter(asset=asset, zone=attrs['from_zone']).first()
            if not zone_stock or zone_stock.quantity < quantity:
                available = zone_stock.quantity if zone_stock else 0
                raise serializers.ValidationError(
                    f"Insufficient stock at source zone. Available: {available}, Requested: {quantity}"
                )

        elif movement_type == 'PROCUREMENT':
            if not attrs.get('to_zone'):
                raise serializers.ValidationError("Procurement requires a destination zone (use Central).")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        movement_type = validated_data['movement_type']
        asset = validated_data['asset']
        quantity = validated_data['quantity']
        from_zone = validated_data.get('from_zone')
        to_zone = validated_data.get('to_zone')

        movement = super().create(validated_data)

        # Update stock levels immediately on creation (status = DISPATCHED for simplicity)
        # For PROCUREMENT and DISPATCH, update right away
        if movement_type == 'PROCUREMENT':
            asset.total_quantity += quantity
            asset.central_stock += quantity
            asset.save()

        elif movement_type == 'DISPATCH':
            asset.central_stock -= quantity
            asset.save()
            zone_stock, _ = ZoneStock.objects.get_or_create(asset=asset, zone=to_zone)
            zone_stock.quantity += quantity
            zone_stock.save()

        elif movement_type == 'RETURN':
            zone_stock = ZoneStock.objects.get(asset=asset, zone=from_zone)
            zone_stock.quantity -= quantity
            zone_stock.save()
            asset.central_stock += quantity
            asset.save()

        elif movement_type == 'TRANSFER':
            from_stock = ZoneStock.objects.get(asset=asset, zone=from_zone)
            from_stock.quantity -= quantity
            from_stock.save()
            to_stock, _ = ZoneStock.objects.get_or_create(asset=asset, zone=to_zone)
            to_stock.quantity += quantity
            to_stock.save()

        return movement


class PurchaseSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.asset_code', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)

    class Meta:
        model = None  # set below
        fields = ['id', 'purchase_number', 'supplier', 'office', 'office_name',
                  'item', 'item_name', 'item_code', 'quantity', 'price_per_unit',
                  'purchase_date', 'remark', 'created_at']
        read_only_fields = ['created_at']

    def __init__(self, *args, **kwargs):
        from .models import Purchase
        self.Meta.model = Purchase
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        from .models import Purchase
        # Update item central stock
        item = validated_data['item']
        item.central_stock += validated_data['quantity']
        item.total_quantity += validated_data['quantity']
        item.save()
        return Purchase.objects.create(**validated_data)


class ItemIssueSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.asset_code', read_only=True)
    item_type = serializers.CharField(source='item.item_type', read_only=True)
    office_name = serializers.CharField(source='office.name', read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = ['id', 'office', 'office_name', 'employee', 'employee_name',
                  'item', 'item_name', 'item_code', 'item_type', 'quantity', 'issue_date',
                  'returnable', 'remark', 'created_at']
        read_only_fields = ['created_at']

    def __init__(self, *args, **kwargs):
        from .models import ItemIssue
        self.Meta.model = ItemIssue
        super().__init__(*args, **kwargs)

    def get_employee_name(self, obj):
        if obj.employee:
            return f"{obj.employee.first_name} {obj.employee.last_name}".strip() or obj.employee.user_id
        return '-'
