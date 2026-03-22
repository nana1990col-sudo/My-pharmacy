from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from .models import Drug, Category, Supplier, Patient, Prescription, Sale, SaleItem, Purchase, UserProfile
from .forms import DrugForm, CategoryForm, SupplierForm, PatientForm, PrescriptionForm, PurchaseForm
import json
from django.http import JsonResponse
from decimal import Decimal

def is_admin(user):
    return hasattr(user, 'profile') and user.profile.role == 'Admin'

def is_pharmacist(user):
    return hasattr(user, 'profile') and user.profile.role in ['Admin', 'Pharmacist']

@login_required
def dashboard(request):
    total_drugs = Drug.objects.count()
    low_stock_drugs = Drug.objects.filter(quantity__lte=F('min_stock_level'))
    expired_drugs = Drug.objects.filter(expiry_date__lt=timezone.now().date())
    near_expiry_drugs = Drug.objects.filter(
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=90),
        expiry_date__gte=timezone.now().date()
    )
    
    today_sales = Sale.objects.filter(date__date=timezone.now().date())
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'total_drugs': total_drugs,
        'low_stock_count': low_stock_drugs.count(),
        'expired_count': expired_drugs.count(),
        'near_expiry_count': near_expiry_drugs.count(),
        'today_revenue': today_revenue,
        'today_sales_count': today_sales.count(),
        'low_stock_drugs': low_stock_drugs[:5],
        'near_expiry_drugs': near_expiry_drugs[:5],
    }
    return render(request, 'pharmacy/dashboard.html', context)

# Drug Management
@login_required
@user_passes_test(is_pharmacist)
def drug_list(request):
    query = request.GET.get('q')
    if query:
        drugs = Drug.objects.filter(
            Q(trade_name__icontains=query) | 
            Q(scientific_name__icontains=query) | 
            Q(barcode__icontains=query)
        )
    else:
        drugs = Drug.objects.all()
    return render(request, 'pharmacy/drug_list.html', {'drugs': drugs})

@login_required
@user_passes_test(is_pharmacist)
def drug_add(request):
    if request.method == 'POST':
        form = DrugForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('drug_list')
    else:
        form = DrugForm()
    return render(request, 'pharmacy/drug_form.html', {'form': form, 'title': 'إضافة دواء جديد'})

@login_required
@user_passes_test(is_pharmacist)
def drug_edit(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    if request.method == 'POST':
        form = DrugForm(request.POST, instance=drug)
        if form.is_valid():
            form.save()
            return redirect('drug_list')
    else:
        form = DrugForm(instance=drug)
    return render(request, 'pharmacy/drug_form.html', {'form': form, 'title': 'تعديل دواء'})

# POS Views
@login_required
def pos_view(request):
    return render(request, 'pharmacy/pos.html')

@login_required
def search_drug_ajax(request):
    query = request.GET.get('q', '')
    drugs = Drug.objects.filter(
        Q(trade_name__icontains=query) | 
        Q(barcode=query)
    ).values('id', 'trade_name', 'sell_price', 'barcode', 'quantity', 'form')[:10]
    return JsonResponse(list(drugs), safe=False)

@login_required
def process_sale_ajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        items = data.get('items', [])
        discount = Decimal(data.get('discount', 0))
        payment_method = data.get('payment_method', 'Cash')
        
        if not items:
            return JsonResponse({'error': 'No items in sale'}, status=400)
            
        total_amount = 0
        sale = Sale.objects.create(
            cashier=request.user,
            discount=discount,
            payment_method=payment_method
        )
        
        for item in items:
            drug = get_object_or_404(Drug, id=item['id'])
            quantity = int(item['quantity'])
            
            if drug.quantity < quantity:
                sale.delete()
                return JsonResponse({'error': f'الكمية غير كافية لـ {drug.trade_name}'}, status=400)
            
            unit_price = drug.sell_price
            subtotal = unit_price * quantity
            total_amount += subtotal
            
            SaleItem.objects.create(
                sale=sale,
                drug=drug,
                quantity=quantity,
                unit_price=unit_price
            )
            
            drug.quantity -= quantity
            drug.save()
            
        sale.total_amount = total_amount - discount
        sale.save()
        
        return JsonResponse({'success': True, 'sale_id': sale.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Reports
@login_required
@user_passes_test(is_admin)
def reports_view(request):
    sales_by_day = Sale.objects.extra(select={'day': "date(date)"}).values('day').annotate(total=Sum('total_amount'), count=Count('id')).order_by('-day')
    
    top_selling = SaleItem.objects.values('drug__trade_name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:10]
    
    context = {
        'sales_by_day': sales_by_day,
        'top_selling': top_selling,
    }
    return render(request, 'pharmacy/reports.html', context)

# Supplier Management
@login_required
@user_passes_test(is_pharmacist)
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'pharmacy/supplier_list.html', {'suppliers': suppliers})

@login_required
@user_passes_test(is_pharmacist)
def supplier_add(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'pharmacy/generic_form.html', {'form': form, 'title': 'إضافة مورد جديد'})

# Purchase Management (Stock In)
@login_required
@user_passes_test(is_pharmacist)
def purchase_list(request):
    purchases = Purchase.objects.all().order_by('-date')
    return render(request, 'pharmacy/purchase_list.html', {'purchases': purchases})

@login_required
@user_passes_test(is_pharmacist)
def purchase_add(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            # Update drug quantity
            drug = purchase.drug
            drug.quantity += purchase.quantity
            drug.save()
            return redirect('purchase_list')
    else:
        form = PurchaseForm()
    return render(request, 'pharmacy/generic_form.html', {'form': form, 'title': 'تسجيل عملية شراء (توريد)'})

# Patient & Prescription Management
@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'pharmacy/patient_list.html', {'patients': patients})

@login_required
def prescription_list(request):
    prescriptions = Prescription.objects.all().order_by('-date')
    return render(request, 'pharmacy/prescription_list.html', {'prescriptions': prescriptions})

@login_required
def prescription_add(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('prescription_list')
    else:
        form = PrescriptionForm()
    return render(request, 'pharmacy/generic_form.html', {'form': form, 'title': 'إضافة وصفة طبية'})
