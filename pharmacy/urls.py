from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('drugs/', views.drug_list, name='drug_list'),
    path('drugs/add/', views.drug_add, name='drug_add'),
    path('drugs/edit/<int:pk>/', views.drug_edit, name='drug_edit'),
    
    # POS
    path('pos/', views.pos_view, name='pos_view'),
    path('api/search-drug/', views.search_drug_ajax, name='search_drug_ajax'),
    path('api/process-sale/', views.process_sale_ajax, name='process_sale_ajax'),
    
    # Reports
    path('reports/', views.reports_view, name='reports_view'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    
    # Purchases (Stock In)
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    
    # Patients & Prescriptions
    path('patients/', views.patient_list, name='patient_list'),
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/add/', views.prescription_add, name='prescription_add'),
]
