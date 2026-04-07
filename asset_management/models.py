from django.db import models
from django.conf import settings


class Zone(models.Model):
    """Represents central unit or any field zone/branch"""
    ZONE_TYPE_CHOICES = [
        ('CENTRAL', 'Central Unit'),
        ('ZONE', 'Zone'),
    ]
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    zone_type = models.CharField(max_length=10, choices=ZONE_TYPE_CHOICES, default='ZONE')
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_zone_type_display()})"

    class Meta:
        db_table = 'asset_zones'


class AssetCategory(models.Model):
    """Category of assets e.g. IT Equipment, Furniture, Vehicle"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'asset_categories'


class Asset(models.Model):
    """Master asset/item definition"""
    UNIT_CHOICES = [
        ('PCS', 'Pieces'),
        ('NOS', 'Numbers'),
        ('SET', 'Set'),
        ('KG', 'Kilogram'),
        ('LTR', 'Litre'),
        ('MTR', 'Metre'),
    ]
    name = models.CharField(max_length=200)
    asset_code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='PCS')
    total_quantity = models.PositiveIntegerField(default=0, help_text="Total quantity ever procured")
    central_stock = models.PositiveIntegerField(default=0, help_text="Current stock at central unit")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset_code} - {self.name}"

    class Meta:
        db_table = 'assets'


class ZoneStock(models.Model):
    """Current stock of each asset at each zone"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='zone_stocks')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='zone_stocks')
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_zone_stocks'
        unique_together = ('asset', 'zone')

    def __str__(self):
        return f"{self.asset.name} @ {self.zone.name}: {self.quantity}"


class StockMovement(models.Model):
    """Every stock movement — dispatch from central or return to central"""
    MOVEMENT_TYPE_CHOICES = [
        ('DISPATCH', 'Dispatch (Central → Zone)'),
        ('RETURN', 'Return (Zone → Central)'),
        ('TRANSFER', 'Transfer (Zone → Zone)'),
        ('PROCUREMENT', 'Procurement (Added to Central)'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DISPATCHED', 'Dispatched'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    movement_number = models.CharField(max_length=30, unique=True, editable=False)
    movement_type = models.CharField(max_length=15, choices=MOVEMENT_TYPE_CHOICES)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='movements')
    quantity = models.PositiveIntegerField()
    from_zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)
    movement_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_movements')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate movement number
        if not self.movement_number:
            last = StockMovement.objects.order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.movement_number = f"MOV{str(next_id).zfill(6)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.movement_number} | {self.get_movement_type_display()} | {self.asset.name} x{self.quantity}"

    class Meta:
        db_table = 'asset_stock_movements'
        ordering = ['-created_at']
