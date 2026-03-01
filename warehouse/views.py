from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import WarehouseStock, StockIn, StockOut
from store.models import Product
from store.models import ProductVariant






from django.contrib.admin.views.decorators import staff_member_required

from django.shortcuts import render
from store.models import ProductVariant
from django.db.models import F









from django.db.models import Sum, F

@staff_member_required(login_url='/admin/login/')
def warehouse_dashboard(request):

    total_warehouses = Warehouse.objects.count()
    total_sections = Section.objects.count()
    total_racks = Rack.objects.count()
    total_products = Product.objects.count()

    total_stock = ProductVariant.objects.aggregate(
        total=Sum('stock')
    )['total'] or 0

    # Low Stock
    low_stock_products = ProductVariant.objects.filter(
        stock__lte=F('product__minimum_stock'),
        stock__gt=0
    ).count()

    # Out of Stock
    out_of_stock_count = ProductVariant.objects.filter(
        stock=0
    ).count()

    variants = (
        ProductVariant.objects
        .select_related("product", "product__category", "product__supplier")
        .order_by("product__name")
    )

    context = {
        "total_warehouses": total_warehouses,
        "total_sections": total_sections,
        "total_racks": total_racks,
        "total_products": total_products,
        "total_stock": total_stock,
        "low_stock_products": low_stock_products,
        "out_of_stock_count": out_of_stock_count,
        "variants": variants
    }

    return render(request, "warehouse/dashboard.html", context)

from .models import StockTransaction
# from store.models import ProductVariant
@staff_member_required(login_url='/admin/login/')
def stock_in(request):
    products = Product.objects.all()

    if request.method == 'POST':
        product_id = request.POST['product']
        qty = int(request.POST['quantity'])

        stock, created = WarehouseStock.objects.get_or_create(
            product_id=product_id,
            defaults={'quantity': 0}
        )
        stock.quantity += qty
        stock.save()

        # Update variant stock (source of truth)
        variant = ProductVariant.objects.filter(product_id=product_id).first()
        if variant:
            variant.stock += qty
            variant.save()

        StockTransaction.objects.create(
    product_variant=variant,
    quantity=qty,
    transaction_type='IN',
    user=request.user
)

        return redirect('warehouse_dashboard')

    return render(request, 'warehouse/stock_in.html', {'products': products})

from django.shortcuts import get_object_or_404
from .models import OutwardStock, StockTransaction
from store.models import ProductVariant



@staff_member_required(login_url="/admin/login/")
def outward_stock_create(request):

    if request.method == "POST":
        variant_id = request.POST.get("variant")
        qty = int(request.POST.get("quantity"))

        variant = get_object_or_404(ProductVariant, id=variant_id)

        OutwardStock.objects.create(
            variant=variant,
            quantity_issued=qty,
            destination="customer"  # if required
        )

        return redirect("outward_stock_list")

    variants = ProductVariant.objects.all()

    return render(request, "warehouse/outward_stock_form.html", {
        "variants": variants
    })

from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required(login_url="/admin/login/")
def outward_stock_delete(request, pk):
    outward = get_object_or_404(OutwardStock, pk=pk)

    if request.method == "POST":
        # 🔄 Restore stock
        variant = outward.variant
        variant.stock += outward.quantity_issued
        variant.save()

        # 🗑 Delete record
        outward.delete()

        return redirect("outward_stock")

    return redirect("outward_stock")

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from .forms import InwardStockForm

from store.models import OrderItem

@staff_member_required(login_url="/admin/login/")
def outward_stock_create(request):

    if request.method == "POST":
        variant_id = request.POST.get("variant")
        order_item_id = request.POST.get("order_item")
        qty = int(request.POST.get("quantity"))

        variant = get_object_or_404(ProductVariant, id=variant_id)
        order_item = get_object_or_404(OrderItem, id=order_item_id)

        if variant.stock < qty:
            return render(request, "warehouse/outward_stock_form.html", {
                "error": "Not enough stock available!"
            })

        variant.stock -= qty
        variant.save()

        OutwardStock.objects.create(
            variant=variant,
            order_item=order_item,   # ✅ REQUIRED
            quantity_issued=qty,
            destination="customer"
        )

        return redirect("outward_stock")

    variants = ProductVariant.objects.all()
    order_items = OrderItem.objects.all()

    return render(request, "warehouse/outward_stock_form.html", {
        "variants": variants,
        "order_items": order_items
    })


@staff_member_required(login_url="/admin/login/")
def inward_stock(request):

    if request.method == "POST":
        form = InwardStockForm(request.POST)

        print("POST DATA:", request.POST)

        if form.is_valid():
            print("CLEANED DATA:", form.cleaned_data)
            form.save()
            return redirect("warehouse_dashboard")
        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = InwardStockForm()   # ✅ IMPORTANT LINE

    return render(request, "warehouse/inward_stock.html", {
        "form": form
    })


from .models import OutwardStock,InwardStock

@staff_member_required(login_url="/admin/login/")
def outward_stock_list(request):
    outward = OutwardStock.objects.select_related(
        "variant", "order_item"
    ).order_by("-issued_date")

    return render(request, "warehouse/outward_stock.html", {
        "outward_list": outward
    })


from django.shortcuts import render, redirect
from .models import Supplier
from .forms import SupplierForm

def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'supplier_list.html', {'suppliers': suppliers})


def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'add_supplier.html', {'form': form})


def delete_supplier(request, id):
    supplier = Supplier.objects.get(id=id)
    supplier.delete()
    return redirect('supplier_list')


from django.db.models import Sum, F
from django.utils.timezone import now
from datetime import timedelta



from django.db.models import Sum, F

def reports(request):

    # Fast moving products
    fast_moving = (
        StockOut.objects
        .values('variant__product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    # Dead stock
    sold_product_ids = (
        StockOut.objects
        .values_list('variant__product_id', flat=True)
    )

    dead_stock = Product.objects.exclude(id__in=sold_product_ids)

    # Total stock value (based on inward purchase)
    total_value = (
        InwardStock.objects
        .aggregate(
            total=Sum(F('quantity_received') * F('purchase_price'))
        )['total'] or 0
    )

    # Category-wise stock
    category_data = (
        WarehouseStock.objects
        .values('product__category__name')
        .annotate(total=Sum('quantity'))
    )

    context = {
        'fast_moving': fast_moving,
        'dead_stock': dead_stock,
        'total_value': total_value,
        'category_data': category_data,
    }

    return render(request, 'warehouse/reports.html', context)



from django.shortcuts import render, redirect
from .models import ReturnDamage
from .forms import ReturnDamageForm


def return_damage_list(request):
    records = ReturnDamage.objects.all().order_by('-date_reported')
    return render(request, 'return_damage/list.html', {'records': records})


def add_return_damage(request):
    if request.method == 'POST':
        form = ReturnDamageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('return_damage_list')
    else:
        form = ReturnDamageForm()

    return render(request, 'return_damage/add.html', {'form': form})


def update_action_status(request, pk):
    record = ReturnDamage.objects.get(id=pk)

    if request.method == 'POST':
        record.action_status = request.POST.get('action_status')
        record.save()
        return redirect('return_damage_list')

    return render(request, 'return_damage/update.html', {'record': record})

from .models import Warehouse, Section, Rack, ProductLocation

# def warehouse_list(request):
#     warehouses = Warehouse.objects.all()
#     return render(request, "warehouse/warehouse_list.html", {"warehouses": warehouses})
from django.db.models import Sum
from .models import Warehouse, ProductLocation

def warehouse_list(request):

    warehouses = Warehouse.objects.all()

    for warehouse in warehouses:
        total_products = ProductLocation.objects.filter(
            rack__section__warehouse=warehouse
        ).aggregate(total=Sum("quantity"))

        warehouse.total_products = total_products["total"] or 0

    return render(request, "warehouse/warehouse_list.html", {
        "warehouses": warehouses
    })


def section_list(request):
    sections = Section.objects.select_related("warehouse")
    return render(request, "warehouse/section_list.html", {"sections": sections})


def rack_list(request):
    racks = Rack.objects.select_related("section")
    return render(request, "warehouse/rack_list.html", {"racks": racks})


def product_location_list(request):
    locations = ProductLocation.objects.select_related("product", "rack")
    return render(request, "warehouse/product_location_list.html", {"locations": locations})

def product_location_create(request):
    if request.method == "POST":
        product_id = request.POST.get("product")
        rack_id = request.POST.get("rack")
        quantity = request.POST.get("quantity")

        product = get_object_or_404(Product, id=product_id)
        rack = get_object_or_404(Rack, id=rack_id)

        ProductLocation.objects.create(
            product=product,
            rack=rack,
            quantity=quantity
        )

        return redirect("product_location_list")

    products = Product.objects.all()
    racks = Rack.objects.select_related("section__warehouse").all()

    return render(request, "warehouse/product_location_form.html", {
        "products": products,
        "racks": racks
    })

def product_location_update(request, pk):
    location = get_object_or_404(ProductLocation, pk=pk)

    if request.method == "POST":
        location.product = get_object_or_404(Product, id=request.POST.get("product"))
        location.rack = get_object_or_404(Rack, id=request.POST.get("rack"))
        location.quantity = request.POST.get("quantity")
        location.save()

        return redirect("product_location_list")

    products = Product.objects.all()
    racks = Rack.objects.select_related("section__warehouse").all()

    return render(request, "warehouse/product_location_form.html", {
        "location": location,
        "products": products,
        "racks": racks
    })

def product_location_delete(request, pk):
    location = get_object_or_404(ProductLocation, pk=pk)

    if request.method == "POST":
        location.delete()
        return redirect("product_location_list")

    return redirect("product_location_list")

from django.shortcuts import render, redirect
from .models import Warehouse

def warehouse_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        location = request.POST.get("location")
        capacity = request.POST.get("capacity")

        Warehouse.objects.create(
            name=name,
            location=location,
            capacity=capacity
        )

        return redirect("warehouse_list")

    return render(request, "warehouse/warehouse_form.html")



from django.shortcuts import get_object_or_404

def warehouse_update(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == "POST":
        warehouse.name = request.POST.get("name")
        warehouse.location = request.POST.get("location")
        warehouse.capacity = request.POST.get("capacity")
        warehouse.save()

        return redirect("warehouse_list")

    return render(request, "warehouse/warehouse_form.html", {
        "warehouse": warehouse
    })



from django.shortcuts import get_object_or_404, redirect

def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == "POST":
        warehouse.delete()
        return redirect('warehouse_list')

    return redirect('warehouse_list')

def section_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        warehouse_id = request.POST.get("warehouse")

        from .models import Section, Warehouse
        warehouse = Warehouse.objects.get(id=warehouse_id)

        Section.objects.create(
            name=name,
            warehouse=warehouse
        )

        return redirect("section_list")

    from .models import Warehouse
    warehouses = Warehouse.objects.all()

    return render(request, "warehouse/section_form.html", {
        "warehouses": warehouses
    })

from django.shortcuts import get_object_or_404

def section_update(request, pk):
    from .models import Section, Warehouse

    section = get_object_or_404(Section, pk=pk)

    if request.method == "POST":
        section.name = request.POST.get("name")
        warehouse_id = request.POST.get("warehouse")
        section.warehouse = Warehouse.objects.get(id=warehouse_id)
        section.save()

        return redirect("section_list")

    warehouses = Warehouse.objects.all()

    return render(request, "warehouse/section_form.html", {
        "section": section,
        "warehouses": warehouses
    })


def section_delete(request, pk):
    from .models import Section

    section = get_object_or_404(Section, pk=pk)

    if request.method == "POST":
        section.delete()
        return redirect("section_list")

    return redirect("section_list")


def rack_create(request):
    if request.method == "POST":
        rack_number = request.POST.get("rack_number")
        section_id = request.POST.get("section")

        section = get_object_or_404(Section, id=section_id)

        Rack.objects.create(
            rack_number=rack_number,
            section=section
        )

        return redirect("rack_list")

    sections = Section.objects.select_related("warehouse").all()

    return render(request, "warehouse/rack_form.html", {
        "sections": sections
    })

def rack_update(request, pk):
    rack = get_object_or_404(Rack, pk=pk)

    if request.method == "POST":
        rack.rack_number = request.POST.get("rack_number")
        section_id = request.POST.get("section")
        rack.section = get_object_or_404(Section, id=section_id)
        rack.save()

        return redirect("rack_list")

    sections = Section.objects.select_related("warehouse").all()

    return render(request, "warehouse/rack_form.html", {
        "rack": rack,
        "sections": sections
    })

def rack_delete(request, pk):
    rack = get_object_or_404(Rack, pk=pk)

    if request.method == "POST":
        rack.delete()
        return redirect("rack_list")

    return redirect("rack_list")



from .models import StockTransaction

def stock_history(request):
    transactions = StockTransaction.objects.select_related(
        "product_variant", "user"
    ).order_by("-created_at")

    return render(request, "warehouse/stock_history.html", {
        "transactions": transactions
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StockTransfer, Rack
from store.models import ProductVariant

def transfer_stock(request):

    if request.method == "POST":
        variant_id = request.POST.get("variant")
        from_rack_id = request.POST.get("from_rack")
        to_rack_id = request.POST.get("to_rack")
        quantity = int(request.POST.get("quantity"))

        try:
            transfer = StockTransfer.objects.create(
                variant_id=variant_id,
                from_rack_id=from_rack_id,
                to_rack_id=to_rack_id,
                quantity=quantity
            )

            messages.success(request, "Stock moved successfully!")

        except Exception as e:
            messages.error(request, str(e))

        return redirect("transfer_stock")

    variants = ProductVariant.objects.all()
    racks = Rack.objects.all()

    return render(request, "warehouse/transfer_stock.html", {
        "variants": variants,
        "racks": racks
    })


from django.shortcuts import render
from django.db.models import Q
from store.models import ProductVariant
from .models import Warehouse, Section, Rack, ProductLocation


def stock_overview(request):

    locations = ProductLocation.objects.select_related(
        "product",
        "rack",
        "rack__section",
        "rack__section__warehouse"
    ).all()

    search = request.GET.get("search")
    warehouse_id = request.GET.get("warehouse")
    section_id = request.GET.get("section")
    rack_id = request.GET.get("rack")
    status = request.GET.get("status")

    # 🔎 Search by product name
    if search:
        locations = locations.filter(
            product__name__icontains=search
        )

    # 🏢 Filter by warehouse
    if warehouse_id:
        locations = locations.filter(
            rack__section__warehouse_id=warehouse_id
        )

    # 🏬 Filter by section
    if section_id:
        locations = locations.filter(
            rack__section_id=section_id
        )

    # 📦 Filter by rack
    if rack_id:
        locations = locations.filter(
            rack_id=rack_id
        )

    # 📊 Stock Status Filter
    if status:
        if status == "out":
            locations = locations.filter(quantity=0)
        elif status == "low":
            locations = locations.filter(quantity__lte=5, quantity__gt=0)
        elif status == "in":
            locations = locations.filter(quantity__gt=5)

    context = {
        "locations": locations,
        "warehouses": Warehouse.objects.all(),
        "sections": Section.objects.all(),
        "racks": Rack.objects.all(),
    }

    return render(request, "warehouse/stock_overview.html", context)


import openpyxl
from django.http import HttpResponse
from .models import ProductLocation


def export_stock_excel(request):

    locations = ProductLocation.objects.select_related(
        "product",
        "rack",
        "rack__section",
        "rack__section__warehouse"
    ).all()

    # Apply filters (same as stock_overview)
    search = request.GET.get("search")
    warehouse_id = request.GET.get("warehouse")

    if search:
        locations = locations.filter(product__name__icontains=search)

    if warehouse_id:
        locations = locations.filter(
            rack__section__warehouse_id=warehouse_id
        )

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stock Report"

    ws.append([
        "Product",
        "Warehouse",
        "Section",
        "Rack",
        "Quantity"
    ])

    for item in locations:
        ws.append([
            item.product.name,
            item.rack.section.warehouse.name,
            item.rack.section.name,
            item.rack.rack_number,
            item.quantity
        ])

    response = HttpResponse(
        content_type='application/ms-excel'
    )
    response['Content-Disposition'] = 'attachment; filename=stock_report.xlsx'

    wb.save(response)
    return response


def export_low_stock_excel(request):

    locations = ProductLocation.objects.filter(quantity__lte=5)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Low Stock Report"

    ws.append([
        "Product",
        "Warehouse",
        "Rack",
        "Quantity"
    ])

    for item in locations:
        ws.append([
            item.product.name,
            item.rack.section.warehouse.name,
            item.rack.rack_number,
            item.quantity
        ])

    response = HttpResponse(
        content_type='application/ms-excel'
    )
    response['Content-Disposition'] = 'attachment; filename=low_stock_report.xlsx'

    wb.save(response)
    return response

from reportlab.pdfgen import canvas


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def export_professional_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=professional_stock_report.pdf'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    data = [["Product", "Warehouse", "Rack", "Quantity"]]

    for item in ProductLocation.objects.all():
        data.append([
            item.product.name,
            item.rack.section.warehouse.name,
            item.rack.rack_number,
            item.quantity
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from store.models import ProductVariant
from .models import StockTransaction

@login_required
def scan_stock(request):

    # 🔒 Only staff allowed
    if not request.user.is_staff:
        return redirect("home")

    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        quantity = int(request.POST.get("quantity", 1))

        try:
            variant = ProductVariant.objects.get(id=variant_id)

            variant.stock += quantity
            variant.save()

            StockTransaction.objects.create(
                product_variant=variant,
                quantity=quantity,
                transaction_type="IN",
                user=request.user
            )

            messages.success(request, f"{variant.product.name} stock updated successfully!")

        except ProductVariant.DoesNotExist:
            messages.error(request, "Invalid QR Code!")

    return render(request, "warehouse/scan_stock.html")