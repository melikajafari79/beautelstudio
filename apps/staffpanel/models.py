"""
مدل‌های این اپ:
  - StaffMember   : پروفایل هر پرسنل
  - StaffService  : مدل واسط پرسنل↔خدمت — امکان override مدت‌زمان و قیمت
  - StaffSchedule : برنامه‌ی کاری هفتگیِ تکرارشونده‌ی هر پرسنل
  - StaffLeave    : بازه‌های مرخصی/تعطیلی هر پرسنل

نکته‌ی معماری کلیدی: duration و قیمتِ Service فقط مقادیر «پایه/نمایشی»
هستند (طبق توضیح قبلی شما). مقدار واقعیِ استفاده‌شده در موتور رزرو باید
هرجا override پرسنل موجود بود از StaffService خوانده شود، وگرنه از خودِ
Service. این منطق در property های effective_duration/effective_price
از هم‌اکنون آماده شده تا موتور رزروِ آینده مجبور نباشد این if/else را
خودش بازنویسی کند.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django_jalali.db import models as jmodels  # جدید: فیلدهای تاریخ شمسی

from apps.services.models import Service


class StaffMember(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='staff_profile', verbose_name="حساب کاربری",
        help_text="در صورت خالی بودن، این پرسنل هنوز به پنل ورود ندارد (فقط پروفایل نمایشی است).",
    )

    full_name = models.CharField(max_length=150, verbose_name="نام و نام خانوادگی")
    slug = models.SlugField(
        max_length=170, unique=True, blank=True, allow_unicode=True,
        default='', verbose_name="اسلاگ (URL)",
    )
    job_title = models.CharField(max_length=150, blank=True, verbose_name="عنوان شغلی")
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")
    photo = models.ImageField(upload_to='staff/', blank=True, null=True, verbose_name="تصویر پرسنل")
    years_of_experience = models.PositiveIntegerField(blank=True, null=True, verbose_name="سابقه‌ی کار (سال)")

    # رابطه با خدمات از طریق مدل واسط StaffService (پایین همین فایل)
    services = models.ManyToManyField(
        Service, through='StaffService', related_name='staff_members', blank=True,
        verbose_name="خدمات قابل‌ارائه",
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    # جدید: مجوزهای پنل پرسنل — پرسنل مستقیماً توسط ادمین اضافه می‌شود و
    # ادمین همینجا مشخص می‌کند این پرسنل چه اختیاراتی در پنل خودش دارد.
    can_manage_own_appointments = models.BooleanField(
        default=False, verbose_name="مجوز لغو/ویرایش نوبت‌های خود",
        help_text="حتی با این مجوز، هر تغییر باید توسط مشتری تأیید شود؛ این فقط اجازه‌ی ثبتِ درخواستِ تغییر را می‌دهد.",
    )
    can_toggle_own_availability = models.BooleanField(
        default=False, verbose_name="مجوز فعال/غیرفعال‌کردن زمان‌های آزاد خود",
        help_text="امکان مسدودکردن موقت بازه‌های رزروْنشده‌ی برنامه‌ی کاری خودش (بدون نیاز به ثبت مرخصی کامل).",
    )
    can_upload_portfolio = models.BooleanField(default=False, verbose_name="مجوز آپلود نمونه‌کار")

    # تغییر: تاریخ شمسی به‌جای میلادی
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    # تغییر: جهت فعال‌شدن فیلترهای کوئری بر پایه‌ی تاریخ شمسی (مثل __jyear)
    objects = jmodels.jManager()

    class Meta:
        verbose_name = "پرسنل"
        verbose_name_plural = "پرسنل"
        ordering = ['order', 'full_name']

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(self.full_name, allow_unicode=True)
        slug = base_slug
        counter = 1
        while StaffMember.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug


class StaffService(models.Model):
    """
    مدل واسط پرسنل↔خدمت. اگر duration_override یا price_override خالی
    باشند، یعنی مقدار پایه‌ی خودِ Service معتبر است.
    """
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='staff_services', verbose_name="پرسنل")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='staff_links', verbose_name="خدمت")

    duration_override = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="مدت زمان اختصاصی (دقیقه)",
        help_text="اگر خالی باشد، مدت زمان پایه‌ی خودِ خدمت استفاده می‌شود.",
    )
    price_override = models.DecimalField(
        max_digits=10, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت اختصاصی (تومان)",
        help_text="اگر خالی باشد، قیمت داخلی پایه‌ی خودِ خدمت استفاده می‌شود.",
    )
    is_active = models.BooleanField(
        default=True, verbose_name="فعال",
        help_text="غیرفعال یعنی این پرسنل دیگر این خدمت را ارائه نمی‌دهد (بدون حذف تاریخچه).",
    )

    class Meta:
        verbose_name = "ارتباط پرسنل و خدمت"
        verbose_name_plural = "ارتباط‌های پرسنل و خدمات"
        constraints = [
            models.UniqueConstraint(fields=['staff', 'service'], name='unique_staff_service_pair'),
        ]

    def __str__(self):
        return f"{self.staff.full_name} — {self.service.name}"

    def clean(self):
        errors = {}
        if self.duration_override is not None and self.service_id:
            if not self.service.is_parallel and self.duration_override < 1:
                errors['duration_override'] = "برای خدمات غیرموازی، مدت زمان باید حداقل ۱ دقیقه باشد."
        if errors:
            raise ValidationError(errors)

    @property
    def effective_duration(self):
        """مدت‌زمانی که موتور رزرو باید واقعاً استفاده کند."""
        return self.duration_override if self.duration_override is not None else self.service.duration

    @property
    def effective_price(self):
        """قیمتی که موتور رزرو/فاکتور باید واقعاً استفاده کند."""
        return self.price_override if self.price_override is not None else self.service.final_price


class Weekday(models.IntegerChoices):
    """
    توجه مهم: هفته‌ی ایرانی از شنبه شروع می‌شود، برخلاف date.weekday()
    پایتون که دوشنبه=۰ است. هر جای دیگر پروژه (مثلاً موتور رزرو در آینده)
    که بخواهد date.weekday() پایتون را با این مدل مقایسه کند، باید از
    تابع python_weekday_to_salon_weekday() پایین استفاده کند؛ در غیر
    این صورت روزهای کاری به‌اشتباه محاسبه می‌شوند.
    """
    SATURDAY = 0, 'شنبه'
    SUNDAY = 1, 'یکشنبه'
    MONDAY = 2, 'دوشنبه'
    TUESDAY = 3, 'سه‌شنبه'
    WEDNESDAY = 4, 'چهارشنبه'
    THURSDAY = 5, 'پنجشنبه'
    FRIDAY = 6, 'جمعه'


def python_weekday_to_salon_weekday(python_weekday: int) -> int:
    """
    date.weekday() پایتون: دوشنبه=۰ ... یکشنبه=۶
    Weekday این پروژه:      شنبه=۰ ... جمعه=۶
    مثال استفاده (در موتور رزرو آینده):
        salon_day = python_weekday_to_salon_weekday(some_date.weekday())
    """
    return (python_weekday + 2) % 7


class StaffSchedule(models.Model):
    """
    یک ردیف = یک بازه‌ی زمانیِ کاری در یک روز هفته. برای شیفت‌های دوگانه
    (مثلاً صبح ۹-۱۳ و عصر ۱۶-۲۰)، دو ردیف جداگانه برای همان روز ثبت کنید.
    نبودِ هیچ ردیفی برای یک روز یعنی آن پرسنل آن روز اصلاً کاری نیست —
    نیازی به فیلد جداگانه‌ی «تعطیل» نیست.
    """
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='schedules', verbose_name="پرسنل")
    weekday = models.IntegerField(choices=Weekday.choices, verbose_name="روز هفته")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")

    class Meta:
        verbose_name = "برنامه‌ی کاری"
        verbose_name_plural = "برنامه‌های کاری"
        ordering = ['staff', 'weekday', 'start_time']

    def __str__(self):
        return f"{self.staff.full_name} — {self.get_weekday_display()} ({self.start_time}–{self.end_time})"

    def clean(self):
        errors = {}
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors['end_time'] = "ساعت پایان باید بعد از ساعت شروع باشد."
            else:
                # جلوگیری از دو بازه‌ی هم‌پوشان برای همان پرسنل در همان روز
                overlapping = StaffSchedule.objects.filter(
                    staff=self.staff, weekday=self.weekday,
                    start_time__lt=self.end_time, end_time__gt=self.start_time,
                ).exclude(pk=self.pk)
                if overlapping.exists():
                    errors['start_time'] = "این بازه با یک بازه‌ی کاری دیگر در همان روز تداخل دارد."
        if errors:
            raise ValidationError(errors)


class StaffLeave(models.Model):
    """بازه‌ی مرخصی/تعطیلی یک پرسنل — موتور رزرو باید این بازه‌ها را غیرقابل‌رزرو در نظر بگیرد."""
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='leaves', verbose_name="پرسنل")
    # تغییر: تاریخ شمسی به‌جای میلادی
    start_date = jmodels.jDateField(verbose_name="از تاریخ")
    end_date = jmodels.jDateField(verbose_name="تا تاریخ")
    reason = models.CharField(max_length=255, blank=True, verbose_name="دلیل (اختیاری)")

    objects = jmodels.jManager()

    class Meta:
        verbose_name = "مرخصی"
        verbose_name_plural = "مرخصی‌ها"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.staff.full_name}: {self.start_date} تا {self.end_date}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': "تاریخ پایان نباید قبل از تاریخ شروع باشد."})


class StaffTimeBlock(models.Model):
    """
    جدید: مسدودسازی موقتِ یک بازه‌ی زمانیِ مشخص در یک تاریخ خاص —
    نه یک روز کامل مثل StaffLeave، و نه بخشی از برنامه‌ی هفتگیِ
    تکرارشونده مثل StaffSchedule. برای زمانی که پرسنل (در صورت داشتن
    مجوز can_toggle_own_availability) می‌خواهد فقط یک بازه‌ی کوتاه در
    یک روز کاریِ عادی را غیرقابل‌رزرو کند (مثلاً یک قرار شخصی).

    توجه برای موتور رزروِ آینده: تشخیص «آزاد بودن» یک پرسنل باید هر سه
    منبع را بررسی کند: نبودِ ردیف در StaffSchedule برای آن روز هفته،
    قرارگرفتن تاریخ در بازه‌ی StaffLeave، و قرارگرفتن بازه در یک
    StaffTimeBlock فعال — نه فقط یکی از این سه.
    """
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='time_blocks', verbose_name="پرسنل")
    date = jmodels.jDateField(verbose_name="تاریخ")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    reason = models.CharField(max_length=255, blank=True, verbose_name="دلیل (اختیاری)")

    objects = jmodels.jManager()

    class Meta:
        verbose_name = "بازه‌ی مسدودشده"
        verbose_name_plural = "بازه‌های مسدودشده"
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.staff.full_name}: {self.date} ({self.start_time}–{self.end_time})"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': "ساعت پایان باید بعد از ساعت شروع باشد."})
