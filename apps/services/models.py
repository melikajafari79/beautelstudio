from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return self.name


class Service(models.Model):
    # ارتباط چند-به-یک: هر دسته می‌تواند چندین خدمت داشته باشد
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services', verbose_name="دسته‌بندی")

    name = models.CharField(max_length=150, verbose_name="نام خدمت")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    # استفاده از عدد صحیح برای دقیقه، محاسبه زمان در تقویم را بسیار ساده‌تر می‌کند
    duration = models.PositiveIntegerField(help_text="مدت زمان به دقیقه", verbose_name="مدت زمان (دقیقه)")
    base_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="قیمت پایه (تومان)")

    # فلگ طلایی برای حل چالش رزروهای همزمان و مشاوره‌ها
    is_parallel = models.BooleanField(default=False,
                                      help_text="آیا این خدمت می‌تواند در بین کارهای دیگر و با زمان صفر انجام شود؟",
                                      verbose_name="قابلیت انجام موازی")

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "خدمت"
        verbose_name_plural = "خدمات"

    def __str__(self):
        return f"{self.name} ({self.category.name})"