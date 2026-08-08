"""
نسخه‌ی به‌روزشده: سیستم قیمت‌گذاری بازنویسی شد. تغییرات با کامنت
«# تغییر:» یا «# جدید:» مشخص شده‌اند؛ بقیه‌ی مدل بدون تغییر باقی مانده.
"""
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django_jalali.db import models as jmodels  # جدید: فیلدهای تاریخ شمسی


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(
        max_length=120, unique=True, blank=True, allow_unicode=True,
        default='', verbose_name="اسلاگ (URL)",
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="تصویر دسته‌بندی")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش",
                                         help_text="عدد کوچک‌تر، بالاتر نمایش داده می‌شود.")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    # تغییر: تاریخ شمسی به‌جای میلادی
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    # تغییر: جهت فعال‌شدن فیلترهای کوئری بر پایه‌ی تاریخ شمسی (مثل __jyear)
    objects = jmodels.jManager()

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(self.name, allow_unicode=True)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug


class ServiceQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_active=True, category__is_active=True).select_related('category')


class Service(models.Model):
    # جدید: دو حالت نمایش قیمت که مدیر سالن از پنل ادمین انتخاب می‌کند.
    PRICE_MODE_SINGLE = 'single'
    PRICE_MODE_RANGE = 'range'
    PRICE_MODE_CHOICES = [
        (PRICE_MODE_SINGLE, 'قیمت واحد'),
        (PRICE_MODE_RANGE, 'محدوده قیمت (از - تا)'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='services', verbose_name="دسته‌بندی",
    )

    name = models.CharField(max_length=150, verbose_name="نام خدمت")
    slug = models.SlugField(
        max_length=170, unique=True, blank=True, allow_unicode=True,
        default='', verbose_name="اسلاگ (URL)",
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name="تصویر خدمت")

    duration = models.PositiveIntegerField(
        default=0,
        help_text=(
            "مدت زمان پایه به دقیقه، فقط برای نمایش تخمینی در سایت عمومی. "
            "زمان واقعیِ رزرو بعداً از مقدار اختصاصی هر پرسنل (در مدل واسط پرسنل↔خدمت) خوانده می‌شود."
        ),
        verbose_name="مدت زمان پایه (دقیقه)",
    )

    # ---------- قیمت داخلی/واقعی: همیشه پر است، مبنای محاسبات واقعی سیستم ----------
    base_price = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت پایه (تومان)",
        help_text="قیمت واقعی که مبنای محاسبات سیستم (رزرو/فاکتور) است؛ لزوماً همان چیزی نیست که در سایت نمایش داده می‌شود.",
    )
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت با تخفیف (تومان)",
        help_text="فقط زمانی معنا دارد که «نحوه‌ی نمایش قیمت» روی «قیمت واحد» باشد.",
    )

    # ---------- جدید: کنترل نمایش عمومی قیمت — کاملاً مستقل از قیمت داخلی بالا ----------
    show_price = models.BooleanField(
        default=True, verbose_name="نمایش قیمت در سایت",
        help_text="اگر خاموش باشد، به‌جای قیمت، پیامی مثل «برای اطلاع از قیمت تماس بگیرید» نمایش داده می‌شود.",
    )
    price_display_mode = models.CharField(
        max_length=10, choices=PRICE_MODE_CHOICES, default=PRICE_MODE_SINGLE,
        verbose_name="نحوه‌ی نمایش قیمت",
    )
    price_min = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="حداقل قیمت نمایشی (تومان)",
        help_text="فقط در حالت «محدوده قیمت» استفاده می‌شود.",
    )
    price_max = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="حداکثر قیمت نمایشی (تومان)",
        help_text="فقط در حالت «محدوده قیمت» استفاده می‌شود.",
    )

    is_parallel = models.BooleanField(
        default=False, verbose_name="قابلیت انجام موازی",
        help_text="آیا این خدمت می‌تواند در بین کارهای دیگر و بدون اشغال ظرفیت زمانی انجام شود؟",
    )
    requires_staff_confirmation = models.BooleanField(default=False, verbose_name="نیاز به تأیید پرسنل")
    requires_deposit = models.BooleanField(default=False, verbose_name="نیاز به بیعانه")
    deposit_amount = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="مبلغ بیعانه (تومان)",
        help_text="فقط زمانی که «نیاز به بیعانه» فعال باشد استفاده می‌شود.",
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    # تغییر: تاریخ شمسی به‌جای میلادی. توجه: مدیریت (manager) این مدل
    # همچنان ServiceQuerySet.as_manager() است، نه jmodels.jManager() —
    # چون متد .public() حیاتی است و نباید از دست برود. یعنی روی این دو
    # فیلد، فیلترهای کوئری مخصوص شمسی (مثل created_at__jyear=...) در
    # دسترس نیستند، ولی مقداردهی/نمایش شمسی کاملاً درست کار می‌کند.
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    objects = ServiceQuerySet.as_manager()

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"
        ordering = ['category__order', 'order', 'name']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(discount_price__isnull=True)
                    | models.Q(discount_price__lt=models.F('base_price'))
                ),
                name='service_discount_price_less_than_base_price',
            ),
            # جدید: در سطح دیتابیس تضمین می‌کند که در حالت «محدوده قیمت»،
            # هر دو مقدار حداقل/حداکثر پر باشند و حداقل کمتر از حداکثر باشد.
            models.CheckConstraint(
                condition=(
                    models.Q(price_display_mode='single')
                    | (
                        models.Q(price_display_mode='range')
                        & models.Q(price_min__isnull=False)
                        & models.Q(price_max__isnull=False)
                        & models.Q(price_min__lt=models.F('price_max'))
                    )
                ),
                name='service_valid_price_range_when_range_mode',
            ),
            # جدید: جلوگیری از هم‌زمان‌بودن discount_price و حالت «محدوده قیمت»
            # (چون تخفیف روی یک محدوده معنای روشنی ندارد).
            models.CheckConstraint(
                condition=~(
                    models.Q(price_display_mode='range') & models.Q(discount_price__isnull=False)
                ),
                name='service_no_discount_price_in_range_mode',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def clean(self):
        errors = {}
        if not self.is_parallel and self.duration < 1:
            errors['duration'] = "برای خدمات غیرموازی، مدت زمان باید حداقل ۱ دقیقه باشد."
        if self.requires_deposit and not self.deposit_amount:
            errors['deposit_amount'] = "چون «نیاز به بیعانه» فعال است، باید مبلغ بیعانه را وارد کنید."

        # جدید: اعتبارسنجی دو حالت نمایش قیمت
        if self.price_display_mode == self.PRICE_MODE_RANGE:
            if self.price_min is None or self.price_max is None:
                errors['price_min'] = "برای «محدوده قیمت»، هر دو مقدار حداقل و حداکثر باید وارد شوند."
            elif self.price_min >= self.price_max:
                errors['price_max'] = "حداکثر قیمت باید بیشتر از حداقل قیمت باشد."
            if self.discount_price is not None:
                errors['discount_price'] = "در حالت «محدوده قیمت»، قیمت تخفیف‌دار کاربردی ندارد؛ این فیلد را خالی بگذارید."
        elif self.price_display_mode == self.PRICE_MODE_SINGLE:
            if self.price_min is not None or self.price_max is not None:
                errors['price_min'] = "چون نحوه‌ی نمایش «قیمت واحد» است، فیلدهای محدوده قیمت باید خالی بمانند."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(self.name, allow_unicode=True)
        slug = base_slug
        counter = 1
        while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug

    @property
    def final_price(self):
        """
        قیمت واقعی/داخلی (نه لزوماً آنچه در سایت نشان داده می‌شود).
        مبنای محاسبات آینده در رزرو/فاکتور.
        """
        return self.discount_price if self.discount_price is not None else self.base_price

    @property
    def public_price_display(self):
        """
        جدید: خروجی آماده برای قالب‌ها (templates)، تا منطق نمایش قیمت
        فقط یک‌بار اینجا نوشته شود و در هر سه قالب (لیست، جزئیات، کارت
        خدمات مرتبط) تکرار نشود.

        خروجی یکی از این سه حالت است:
          - None                                            → قیمت اصلاً نمایش داده نشود
          - {'mode': 'single', 'price': ..., 'discount_price': ...}
          - {'mode': 'range', 'min': ..., 'max': ...}

        توجه: قالب‌های فعلی (service_list.html و ...) هنوز از این متد
        استفاده نمی‌کنند و باید به‌روزرسانی شوند — در غیر این صورت
        همچنان فقط base_price/discount_price را بدون توجه به
        show_price/price_display_mode نمایش می‌دهند.
        """
        if not self.show_price:
            return None
        if self.price_display_mode == self.PRICE_MODE_RANGE:
            return {'mode': self.PRICE_MODE_RANGE, 'min': self.price_min, 'max': self.price_max}
        return {'mode': self.PRICE_MODE_SINGLE, 'price': self.base_price, 'discount_price': self.discount_price}
