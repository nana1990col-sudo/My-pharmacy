from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, verbose_name="وصف")

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "تصنيفات"

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المورد")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="الرصيد المستحق")

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "موردون"

    def __str__(self):
        return self.name

class Drug(models.Model):
    DRUG_FORMS = [
        ('Tablet', 'أقراص'),
        ('Syrup', 'شراب'),
        ('Injection', 'حقن'),
        ('Cream', 'كريم/مرهم'),
        ('Drops', 'قطرة'),
        ('Capsule', 'كبسولات'),
        ('Inhaler', 'بخاخ'),
        ('Suppository', 'تحاميل'),
        ('Other', 'أخرى'),
    ]

    trade_name = models.CharField(max_length=200, verbose_name="الاسم التجاري")
    scientific_name = models.CharField(max_length=200, blank=True, verbose_name="الاسم العلمي")
    barcode = models.CharField(max_length=100, unique=True, verbose_name="الباركود")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="التصنيف")
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name="الشركة المصنعة")
    form = models.CharField(max_length=50, choices=DRUG_FORMS, default='Tablet', verbose_name="الشكل الدوائي")
    
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الشراء")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر البيع")
    
    quantity = models.PositiveIntegerField(default=0, verbose_name="الكمية")
    min_stock_level = models.PositiveIntegerField(default=5, verbose_name="الحد الأدنى للمخزون")
    
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="رقم الوجبة (Batch)")
    expiry_date = models.DateField(verbose_name="تاريخ الانتهاء")
    entry_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإدخال")

    class Meta:
        verbose_name = "دواء"
        verbose_name_plural = "أدوية"
        ordering = ['trade_name']

    def __str__(self):
        return f"{self.trade_name} ({self.form})"

    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    def is_near_expiry(self):
        # 3 months warning
        three_months_away = timezone.now().date() + timezone.timedelta(days=90)
        return self.expiry_date <= three_months_away and not self.is_expired()

    def is_low_stock(self):
        return self.quantity <= self.min_stock_level

class Patient(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المريض")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")
    medical_history = models.TextField(blank=True, verbose_name="السجل الطبي")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مريض"
        verbose_name_plural = "مرضى"

    def __str__(self):
        return self.name

class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="المريض")
    doctor_name = models.CharField(max_length=200, blank=True, verbose_name="اسم الطبيب")
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الوصفة")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    is_dispensed = models.BooleanField(default=False, verbose_name="تم الصرف")

    class Meta:
        verbose_name = "وصفة طبية"
        verbose_name_plural = "وصفات طبية"

    def __str__(self):
        return f"وصفة {self.patient.name} - {self.date}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, related_name='items', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, verbose_name="الدواء")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")

    class Meta:
        verbose_name = "دواء في الوصفة"
        verbose_name_plural = "أدوية في الوصفات"

class SystemSettings(models.Model):
    pharmacy_name = models.CharField(max_length=200, default="صيدليتي الذكية", verbose_name="اسم الصيدلية")
    currency_unit = models.CharField(max_length=20, default="ج.م", verbose_name="الوحدة السعرية (العملة)")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="نسبة الضريبة (%)")
    address = models.TextField(blank=True, verbose_name="عنوان الصيدلية")
    phone = models.CharField(max_length=20, blank=True, verbose_name="هاتف الصيدلية")

    class Meta:
        verbose_name = "إعدادات النظام"
        verbose_name_plural = "إعدادات النظام"

    def __str__(self):
        return "إعدادات النظام"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'نقدي'),
        ('Card', 'بطاقة'),
        ('Credit', 'دين'),
    ]

    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="الكاشير")
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المريض")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ البيع")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="الإجمالي")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الخصم")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash', verbose_name="طريقة الدفع")
    
    class Meta:
        verbose_name = "عملية بيع"
        verbose_name_plural = "عمليات المبيعات"
        ordering = ['-date']

    def __str__(self):
        return f"فاتورة #{self.id} - {self.date.strftime('%Y-%m-%d %H:%M')}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, verbose_name="الدواء")
    quantity = models.PositiveIntegerField(default=1, verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="المجموع الفرعي")

    def save(self, *args, **kwargs):
        self.subtotal = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name="المورد")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, verbose_name="الدواء")
    quantity = models.PositiveIntegerField(verbose_name="الكمية المشتراة")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر التكلفة")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="التكلفة الإجمالية")
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الشراء")

    def save(self, *args, **kwargs):
        self.total_cost = Decimal(self.quantity) * self.unit_cost
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "عملية شراء"
        verbose_name_plural = "عمليات المشتريات"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'مدير'),
        ('Pharmacist', 'صيدلي'),
        ('Cashier', 'كاشير'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Cashier', verbose_name="الدور")
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")

    def __str__(self):
        return f"{self.user.username} - {self.role}"
