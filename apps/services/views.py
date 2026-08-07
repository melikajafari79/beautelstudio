from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Category, Service


class ServiceListView(ListView):
    """
    صفحه‌ی «خدمات سالن». سه سناریو را همزمان پوشش می‌دهد:
      ۱) نمایش همه‌ی خدمات فعال
      ۲) فیلتر بر اساس دسته‌بندی: /services/?category=<slug>
      ۳) جستجوی متنی در نام و توضیحات: /services/?q=...
    """
    model = Service
    template_name = 'services/service_list.html'
    context_object_name = 'services'
    paginate_by = 12

    def get_queryset(self):
        queryset = Service.objects.public()  # از ServiceQuerySet در models.py

        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')

        # افزوده شد: querystring فیلترهای فعال (بدون پارامتر page) برای
        # این‌که لینک‌های صفحه‌بندی در قالب، جستجو/فیلتر فعلی را حفظ کنند.
        # مثال: کاربر با q=کوتاهی به صفحه‌ی ۲ می‌رود بدون این‌که فیلترش پاک شود.
        params = self.request.GET.copy()
        params.pop('page', None)
        context['querystring'] = params.urlencode()

        return context


class ServiceDetailView(DetailView):
    """صفحه‌ی جزئیات یک خدمت مشخص، بر اساس اسلاگ."""
    model = Service
    template_name = 'services/service_detail.html'
    context_object_name = 'service'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # فقط خدمات قابل‌نمایش عمومی؛ در غیر این صورت DetailView خودش
        # به‌صورت خودکار خطای 404 مناسب برمی‌گرداند (نیازی به get_object_or_404 نیست).
        return Service.objects.public()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # افزوده شد: چند خدمت دیگر از همان دسته‌بندی، برای بخش «خدمات مرتبط».
        # exclude(pk=...) خودِ خدمت جاری را از لیست حذف می‌کند.
        context['related_services'] = (
            Service.objects.public()
            .filter(category=self.object.category)
            .exclude(pk=self.object.pk)[:4]
        )

        return context
