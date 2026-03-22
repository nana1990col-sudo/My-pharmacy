from django.contrib import admin
from .models import Category, Supplier, Drug, Patient, Prescription, Sale, SaleItem, Purchase, UserProfile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'balance')

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'barcode', 'category', 'form', 'sell_price', 'quantity', 'expiry_date')
    search_fields = ('trade_name', 'barcode', 'scientific_name')
    list_filter = ('category', 'form', 'manufacturer')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor_name', 'date', 'is_dispensed')

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'patient', 'date', 'total_amount', 'payment_method')
    inlines = [SaleItemInline]

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'drug', 'quantity', 'unit_cost', 'total_cost', 'date')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
