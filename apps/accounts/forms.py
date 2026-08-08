from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.utils import to_english_digits

from .models import ReferralSource, User, phone_validator

# کلاس‌های Tailwind مشترک بین همه‌ی ورودی‌های متنی/تاریخ/رمز عبور فرم‌های
# این اپ، تا ظاهر «صفحه ثبت‌نام» و «صفحه ورود» دقیقاً با بقیه‌ی سایت
# (مثلاً کادر جستجوی صفحه‌ی خدمات) یکدست بماند.
TEXT_INPUT_CLASSES = (
    "w-full h-12 px-4 rounded-xl border border-amethyst-200 "
    "focus:outline-none focus:ring-2 focus:ring-amethyst-400 text-stone-700"
)
SELECT_CLASSES = TEXT_INPUT_CLASSES + " bg-white"


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="نام",
        max_length=150,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        max_length=150,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "family-name"}),
    )
    birth_date = forms.DateField(
        label="تاریخ تولد",
        widget=forms.DateInput(attrs={"class": TEXT_INPUT_CLASSES, "type": "date"}),
    )
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": TEXT_INPUT_CLASSES,
                "inputmode": "numeric",
                "placeholder": "09xxxxxxxxx",
                "autocomplete": "tel",
                "dir": "ltr",
            }
        ),
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="تکرار رمز عبور",
        widget=forms.PasswordInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "new-password"}),
    )
    referral_source = forms.ModelChoiceField(
        label="شیوه‌ی آشنایی با ما",
        queryset=ReferralSource.objects.none(),  # در __init__ پر می‌شود
        required=False,
        empty_label="ترجیح می‌دهم نگویم",
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Queryset را در زمان اجرای فرم (نه زمان import ماژول) می‌سازیم؛
        # وگرنه در حالتی که دیتابیس هنوز migrate نشده (مثلاً هنگام اجرای
        # manage.py collectstatic) بارگذاری این فایل خطا می‌دهد.
        self.fields["referral_source"].queryset = ReferralSource.objects.filter(
            is_active=True
        ).order_by("sort_order", "title")

    def clean_phone_number(self):
        phone = to_english_digits(self.cleaned_data["phone_number"]).strip()
        if not phone_validator.regex.match(phone):
            raise ValidationError(phone_validator.message)
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("کاربری با این شماره موبایل قبلاً ثبت‌نام کرده است.")
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date and birth_date > timezone.now().date():
            raise ValidationError("تاریخ تولد نمی‌تواند در آینده باشد.")
        return birth_date

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "رمز عبور و تکرار آن یکسان نیستند.")

        if password:
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned_data


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="کد تایید",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": TEXT_INPUT_CLASSES + " text-center text-2xl tracking-[0.5em]",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "placeholder": "------",
                "dir": "ltr",
            }
        ),
    )

    def clean_code(self):
        code = to_english_digits(self.cleaned_data["code"]).strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("کد تایید باید دقیقاً ۶ رقم باشد.")
        return code


class LoginForm(forms.Form):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": TEXT_INPUT_CLASSES,
                "inputmode": "numeric",
                "placeholder": "09xxxxxxxxx",
                "autocomplete": "tel",
                "dir": "ltr",
            }
        ),
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "current-password"}),
    )

    def clean_phone_number(self):
        phone = to_english_digits(self.cleaned_data["phone_number"]).strip()
        if not phone_validator.regex.match(phone):
            raise ValidationError(phone_validator.message)
        return phone


class ForgotPasswordForm(forms.Form):
    phone_number = forms.CharField(
        label="شماره موبایل",
        max_length=11,
        widget=forms.TextInput(
            attrs={
                "class": TEXT_INPUT_CLASSES,
                "inputmode": "numeric",
                "placeholder": "09xxxxxxxxx",
                "autocomplete": "tel",
                "dir": "ltr",
            }
        ),
    )

    def clean_phone_number(self):
        phone = to_english_digits(self.cleaned_data["phone_number"]).strip()
        if not phone_validator.regex.match(phone):
            raise ValidationError(phone_validator.message)
        if not User.objects.filter(phone_number=phone).exists():
            raise ValidationError("کاربری با این شماره موبایل یافت نشد.")
        return phone


class ProfileEditForm(forms.Form):
    """
    فرم صفحه‌ی «ویرایش اطلاعات» که بعد از تایید کد یکبار‌مصرفِ فراموشی
    رمز عبور نمایش داده می‌شود: هم اطلاعات پروفایل و هم رمز عبور جدید
    یک‌جا گرفته می‌شود.
    """
    first_name = forms.CharField(
        label="نام",
        max_length=150,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASSES}),
    )
    last_name = forms.CharField(
        label="نام خانوادگی",
        max_length=150,
        widget=forms.TextInput(attrs={"class": TEXT_INPUT_CLASSES}),
    )
    birth_date = forms.DateField(
        label="تاریخ تولد",
        widget=forms.DateInput(attrs={"class": TEXT_INPUT_CLASSES, "type": "date"}),
    )
    referral_source = forms.ModelChoiceField(
        label="شیوه‌ی آشنایی با ما",
        queryset=ReferralSource.objects.none(),
        required=False,
        empty_label="ترجیح می‌دهم نگویم",
        widget=forms.Select(attrs={"class": SELECT_CLASSES}),
    )
    new_password = forms.CharField(
        label="رمز عبور جدید",
        widget=forms.PasswordInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "new-password"}),
    )
    new_password_confirm = forms.CharField(
        label="تکرار رمز عبور جدید",
        widget=forms.PasswordInput(attrs={"class": TEXT_INPUT_CLASSES, "autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["referral_source"].queryset = ReferralSource.objects.filter(
            is_active=True
        ).order_by("sort_order", "title")

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date and birth_date > timezone.now().date():
            raise ValidationError("تاریخ تولد نمی‌تواند در آینده باشد.")
        return birth_date

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        password_confirm = cleaned_data.get("new_password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("new_password_confirm", "رمز عبور و تکرار آن یکسان نیستند.")

        if password:
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                self.add_error("new_password", exc)

        return cleaned_data
