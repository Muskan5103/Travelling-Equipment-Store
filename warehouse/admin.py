from django.contrib import admin
from .models import WarehouseStock, StockIn, StockOut
from .models import Warehouse, Section, Rack, ProductLocation
from .models import  ReturnDamage
from .models import StockTransfer

admin.site.register(WarehouseStock)
admin.site.register(StockIn)
admin.site.register(StockOut)
admin.site.register(ReturnDamage)
admin.site.register(Warehouse)
admin.site.register(Section)
admin.site.register(Rack)
admin.site.register(ProductLocation)

admin.site.register(StockTransfer)
