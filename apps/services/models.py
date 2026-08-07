from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام دسته‌بندی")

    # تغییر: اسلاگ برای URL تمیز (مثلا /services/mo-va-zibaei/).
    # allow_unicode=True الزامی است چون اسم‌ها فارسی هستند؛ بدون آن
    # تابع پیش‌فرض slugify جنگو حروف فارسی را حذف می‌کند و اسلاگ خالی می‌شود.
    # default='' هم عمداً گذاشته شده: اگر بعداً روی دیتابیسی با داده‌ی از قبل
    # موجود migration بزنید، جنگو در حالت interactive یک مقدار پیش‌فرض
    # از شما می‌پرسد؛ این کار آن پرسش را حذف می‌کند.
    slug = models.SlugField(
        max_length=120, unique=True, blank=True, allow_unicode=True,
        default='', verbose_name="اسلاگ (URL)",
    )

    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    # تغییر: تصویر برای کارت‌های دسته‌بندی در صفحه‌ی اصلی/خدمات.
    # نیاز به تنظیم MEDIA_URL / MEDIA_ROOT در settings دارد — در مستند پیوست توضیح داده شده.
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="تصویر دسته‌بندی")

    # تغییر: امکان مرتب‌سازی دستی توسط مدیر سالن، بدون نیاز به تغییر کد.
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش",
                                         help_text="عدد کوچک‌تر، بالاتر نمایش داده می‌شود.")

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    # تغییر: افزودن تاریخ ایجاد/بروزرسانی — برای گزارش‌گیری مدیریتی (نیازمندی پروپوزال، بند ۸) لازم است.
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

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
    """
    QuerySet سفارشی تا منطق «فقط خدمات قابل‌نمایش عمومی» یک‌بار نوشته شود
    و هم در views.py این اپ و هم بعداً در اپ booking دوباره‌نویسی نشود.
    """
    def public(self):
        # select_related('category') از N+1 query جلوگیری می‌کند: بدون آن،
        # به‌ازای هر خدمت یک کوئری جداگانه برای گرفتن category اجرا می‌شود.
        return self.filter(is_active=True, category__is_active=True).select_related('category')


class Service(models.Model):
    category = models.ForeignKey(
        Category,
        # تغییر: CASCADE -> PROTECT.
        # با CASCADE، حذف تصادفی یک دسته‌بندی از پنل ادمین، همه‌ی خدمات آن
        # را هم بی‌صدا پاک می‌کرد. با PROTECT، جنگو تا وقتی خدمات این دسته
        # حذف/جابه‌جا نشده‌اند، اجازه‌ی حذف دسته‌بندی را نمی‌دهد.
        on_delete=models.PROTECT,
        related_name='services',
        verbose_name="دسته‌بندی",
    )

    name = models.CharField(max_length=150, verbose_name="نام خدمت")

    # تغییر: اسلاگ خدمت، با همان منطق یونیکد بالا.
    slug = models.SlugField(
        max_length=170, unique=True, blank=True, allow_unicode=True,
        default='', verbose_name="اسلاگ (URL)",
    )

    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    # تغییر: تصویر خدمت — برای سایت معرفی خدمات ضروری است.
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name="تصویر خدمت")

    # مدت زمان: می‌تواند صفر باشد فقط اگر is_parallel=True (اعتبارسنجی در clean() پایین)
    duration = models.PositiveIntegerField(
        default=0,
        help_text="مدت زمان به دقیقه. برای خدمات موازی (is_parallel) می‌تواند صفر باشد.",
        verbose_name="مدت زمان (دقیقه)",
    )

    base_price = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        validators=[MinValueValidator(0)],  # تغییر: جلوگیری از قیمت منفی
        verbose_name="قیمت پایه (تومان)",
    )

    # تغییر: قیمت تخفیف‌دار (اختیاری). اعتبارسنجی «کمتر از قیمت پایه» هم در
    # سطح فرم (clean) و هم در سطح دیتابیس (CheckConstraint پایین) اعمال شده.
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت با تخفیف (تومان)",
        help_text="در صورت خالی بودن، تخفیفی اعمال نمی‌شود.",
    )

    is_parallel = models.BooleanField(
        default=False,
        verbose_name="قابلیت انجام موازی",
        help_text="آیا این خدمت می‌تواند در بین کارهای دیگر و بدون اشغال ظرفیت زمانی انجام شود؟",
    )

    # تغییر: طبق پروپوزال («برخی خدمات نیازمند تأیید پرسنل هستند») —
    # موتور رزرو در آینده از این فیلد برای تصمیم‌گیری استفاده می‌کند.
    requires_staff_confirmation = models.BooleanField(
        default=False, verbose_name="نیاز به تأیید پرسنل",
    )

    # تغییر: طبق پروپوزال («امکان تعریف قوانین... دریافت بیعانه»).
    # قوانین پیچیده‌تر (مثل بیعانه فقط در روزهای خاص) به‌عمد اینجا پیاده
    # نشده — آن منطق باید در موتور قوانین رزروِ اپ booking باشد، نه اینجا؛
    # این دو فیلد فقط رفتار پیش‌فرض/ساده‌ی هر خدمت را نگه می‌دارند.
    requires_deposit = models.BooleanField(default=False, verbose_name="نیاز به بیعانه")
    deposit_amount = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="مبلغ بیعانه (تومان)",
        help_text="فقط زمانی که «نیاز به بیعانه» فعال باشد استفاده می‌شود.",
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    objects = ServiceQuerySet.as_manager()

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"
        ordering = ['category__order', 'order', 'name']
        constraints = [
            # تغییر: تضمین سخت‌گیرانه در سطح دیتابیس که مستقل از هر باگ
            # احتمالی در کد پایتون، اجازه نمی‌دهد discount_price >= base_price ذخیره شود.
            models.CheckConstraint(
                condition=(
                    models.Q(discount_price__isnull=True)
                    | models.Q(discount_price__lt=models.F('base_price'))
                ),
                name='service_discount_price_less_than_base_price',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def clean(self):
        """
        توجه مهم: clean() به‌طور خودکار روی .save() یا.objects.create()
        صدا زده نمی‌شود — فقط وقتی از طریق ModelForm (از جمله پنل ادمین)
        ذخیره کنید اجرا می‌شود. اگر جایی در کد (مثلاً در booking engine
        آینده) مستقیماً Service(...).save() صدا زدید، باید قبلش
        service.full_clean() را دستی صدا بزنید، وگرنه این اعتبارسنجی‌ها
        دور زده می‌شوند (constraint دیتابیس بالا همچنان جلوی discount_price
        اشتباه را می‌گیرد، ولی خطای duration/deposit را نمی‌گیرد).
        """
        errors = {}
        if not self.is_parallel and self.duration < 1:
            errors['duration'] = "برای خدمات غیرموازی، مدت زمان باید حداقل ۱ دقیقه باشد."
        if self.requires_deposit and not self.deposit_amount:
            errors['deposit_amount'] = "چون «نیاز به بیعانه» فعال است، باید مبلغ بیعانه را وارد کنید."
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
        """قیمتی که باید به مشتری نمایش داده شود: تخفیف‌دار در صورت وجود، وگرنه پایه."""
        return self.discount_price if self.discount_price is not None else self.base_price
