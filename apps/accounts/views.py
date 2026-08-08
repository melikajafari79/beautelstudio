from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from .forms import (
    ForgotPasswordForm,
    LoginForm,
    OTPVerifyForm,
    ProfileEditForm,
    RegisterForm,
)
from .models import User
from .services import create_and_send_otp, verify_otp

# کلیدهای سشن؛ به‌صورت ثابت (constant) تعریف شده‌اند تا در همه‌ی
# view های این فایل دقیقاً یک‌جور نوشته شوند و اشتباه تایپی رخ ندهد.
SESSION_PENDING_REGISTRATION = "pending_registration"
SESSION_RESET_PHONE = "password_reset_phone"
SESSION_RESET_VERIFIED = "password_reset_verified"


# ============================================================
# ثبت‌نام (دو مرحله‌ای: فرم اطلاعات -> تایید پیامکی)
# ============================================================

class RegisterView(FormView):
    """
    مرحله‌ی اول ثبت‌نام.
    نکته‌ی مهم: در این مرحله هیچ رکوردی در جدول کاربران ساخته نمی‌شود.
    اطلاعات فقط در سشن نگه داشته می‌شود تا در VerifyRegisterView و بعد از
    تایید موفق کد پیامکی، کاربر واقعاً در دیتابیس ساخته شود. این یعنی اگر
    کسی شماره موبایل دیگری را (اشتباهی یا عمداً) وارد کند ولی کد را نداشته
    باشد، هیچ کاربر نیمه‌کاره‌ای در سیستم باقی نمی‌ماند.
    """
    form_class = RegisterForm
    template_name = "accounts/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        phone_number = data["phone_number"]

        self.request.session[SESSION_PENDING_REGISTRATION] = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "birth_date": data["birth_date"].isoformat(),
            "phone_number": phone_number,
            # رمز عبور همین الان هش می‌شود؛ حتی به‌صورت موقت هم رمز خام
            # در سشن ذخیره نمی‌شود.
            "password_hash": make_password(data["password"]),
            "referral_source_id": data["referral_source"].id if data["referral_source"] else None,
        }

        otp, wait_seconds = create_and_send_otp(phone_number)
        if otp is None:
            messages.info(
                self.request,
                f"یک کد تایید معتبر از قبل برای این شماره ارسال شده. "
                f"اگر پیامک را دریافت نکردید، {wait_seconds} ثانیه‌ی دیگر می‌توانید دوباره درخواست دهید.",
            )
        else:
            messages.success(self.request, f"کد تایید به شماره {phone_number} پیامک شد.")

        return redirect("accounts:verify_register")


class VerifyRegisterView(FormView):
    """مرحله‌ی دوم ثبت‌نام: وارد کردن کد پیامکی و ساخت واقعی کاربر."""
    form_class = OTPVerifyForm
    template_name = "accounts/verify_otp.html"

    def dispatch(self, request, *args, **kwargs):
        if SESSION_PENDING_REGISTRATION not in request.session:
            return redirect("accounts:register")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pending = self.request.session[SESSION_PENDING_REGISTRATION]
        context.update(
            {
                "phone_number": pending["phone_number"],
                "page_title": "تایید شماره موبایل",
                "resend_url": reverse("accounts:resend_register_otp"),
                "back_url": reverse("accounts:register"),
            }
        )
        return context

    def form_valid(self, form):
        pending = self.request.session[SESSION_PENDING_REGISTRATION]
        ok, error = verify_otp(pending["phone_number"], form.cleaned_data["code"])
        if not ok:
            form.add_error("code", error)
            return self.form_invalid(form)

        user = User.objects.create(
            username=pending["phone_number"],
            first_name=pending["first_name"],
            last_name=pending["last_name"],
            birth_date=date.fromisoformat(pending["birth_date"]),
            phone_number=pending["phone_number"],
            password=pending["password_hash"],
            is_phone_verified=True,
            referral_source_id=pending["referral_source_id"],
        )

        del self.request.session[SESSION_PENDING_REGISTRATION]

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "ثبت‌نام شما با موفقیت انجام شد؛ خوش آمدید!")
        return redirect("core:home")


class ResendRegisterOTPView(View):
    """
    ارسال مجدد کد ثبت‌نام. عمداً فقط POST را قبول می‌کند (نه GET)، چون
    مرورگرها/ربات‌ها گاهی لینک‌های GET را پیش‌بارگذاری می‌کنند و ارسال
    پیامک، برخلاف نمایش یک صفحه، هزینه‌ی واقعی دارد.
    """

    def post(self, request, *args, **kwargs):
        pending = request.session.get(SESSION_PENDING_REGISTRATION)
        if not pending:
            return redirect("accounts:register")

        otp, wait_seconds = create_and_send_otp(pending["phone_number"])
        if otp is None:
            messages.warning(request, f"لطفاً {wait_seconds} ثانیه صبر کنید و دوباره تلاش کنید.")
        else:
            messages.success(request, "کد تایید دوباره پیامک شد.")
        return redirect("accounts:verify_register")


# ============================================================
# ورود / خروج
# ============================================================

class LoginView(FormView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.GET.get("next", "")
        return context

    def form_valid(self, form):
        phone_number = form.cleaned_data["phone_number"]
        password = form.cleaned_data["password"]

        # چون در ثبت‌نام، username کاربر همان phone_number قرار داده شده،
        # ورود با شماره موبایل نیازی به Authentication Backend سفارشی ندارد؛
        # فقط باید مقدار phone_number را به‌عنوان username به authenticate بدهیم.
        user = authenticate(self.request, username=phone_number, password=password)
        if user is None:
            form.add_error(None, "شماره موبایل یا رمز عبور اشتباه است.")
            return self.form_invalid(form)

        login(self.request, user)
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        return redirect(next_url or "core:home")


class LogoutView(View):
    """فقط POST؛ خروج با یک لینک ساده‌ی GET از نظر امنیتی توصیه نمی‌شود."""

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "با موفقیت از حساب کاربری خارج شدید.")
        return redirect("core:home")


# ============================================================
# فراموشی رمز عبور (ارسال کد -> تایید کد -> صفحه‌ی ویرایش اطلاعات)
# ============================================================

class ForgotPasswordView(FormView):
    form_class = ForgotPasswordForm
    template_name = "accounts/forgot_password.html"

    def form_valid(self, form):
        phone_number = form.cleaned_data["phone_number"]

        self.request.session[SESSION_RESET_PHONE] = phone_number
        self.request.session[SESSION_RESET_VERIFIED] = False

        otp, wait_seconds = create_and_send_otp(phone_number)
        if otp is None:
            messages.info(
                self.request,
                f"یک کد یکبار مصرف معتبر از قبل برای این شماره ارسال شده. "
                f"اگر پیامک را دریافت نکردید، {wait_seconds} ثانیه‌ی دیگر می‌توانید دوباره درخواست دهید.",
            )
        else:
            messages.success(self.request, f"کد یکبار مصرف به شماره {phone_number} پیامک شد.")

        return redirect("accounts:verify_reset")


class VerifyResetOTPView(FormView):
    form_class = OTPVerifyForm
    template_name = "accounts/verify_otp.html"

    def dispatch(self, request, *args, **kwargs):
        if SESSION_RESET_PHONE not in request.session:
            return redirect("accounts:forgot_password")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "phone_number": self.request.session[SESSION_RESET_PHONE],
                "page_title": "تایید کد یکبار مصرف",
                "resend_url": reverse("accounts:resend_reset_otp"),
                "back_url": reverse("accounts:forgot_password"),
            }
        )
        return context

    def form_valid(self, form):
        phone_number = self.request.session[SESSION_RESET_PHONE]
        ok, error = verify_otp(phone_number, form.cleaned_data["code"])
        if not ok:
            form.add_error("code", error)
            return self.form_invalid(form)

        self.request.session[SESSION_RESET_VERIFIED] = True
        return redirect("accounts:edit_profile")


class ResendResetOTPView(View):
    def post(self, request, *args, **kwargs):
        phone_number = request.session.get(SESSION_RESET_PHONE)
        if not phone_number:
            return redirect("accounts:forgot_password")

        otp, wait_seconds = create_and_send_otp(phone_number)
        if otp is None:
            messages.warning(request, f"لطفاً {wait_seconds} ثانیه صبر کنید و دوباره تلاش کنید.")
        else:
            messages.success(request, "کد یکبار مصرف دوباره پیامک شد.")
        return redirect("accounts:verify_reset")


class EditProfileView(FormView):
    """
    صفحه‌ی «ویرایش اطلاعات» که طبق درخواست، مقصد نهاییِ فرآیند فراموشی
    رمز عبور است. فقط زمانی قابل‌دسترسی است که کاربر مرحله‌ی قبل (تایید
    کد یکبار مصرف) را با موفقیت پشت سر گذاشته باشد — دسترسی مستقیم با آدرس
    این صفحه بدون طی آن مراحل، به فرم فراموشی رمز هدایت می‌شود.
    """
    form_class = ProfileEditForm
    template_name = "accounts/edit_profile.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get(SESSION_RESET_VERIFIED):
            return redirect("accounts:forgot_password")

        phone_number = request.session.get(SESSION_RESET_PHONE)
        self.target_user = User.objects.filter(phone_number=phone_number).first()
        if self.target_user is None:
            # حالت خیلی نادر: کاربر بین تایید کد و رسیدن به این صفحه حذف شده.
            request.session.pop(SESSION_RESET_PHONE, None)
            request.session.pop(SESSION_RESET_VERIFIED, None)
            return redirect("accounts:forgot_password")

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            "first_name": self.target_user.first_name,
            "last_name": self.target_user.last_name,
            "birth_date": self.target_user.birth_date,
            "referral_source": self.target_user.referral_source,
        }

    def form_valid(self, form):
        data = form.cleaned_data
        user = self.target_user
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.birth_date = data["birth_date"]
        user.referral_source = data["referral_source"]
        user.set_password(data["new_password"])
        user.save()

        self.request.session.pop(SESSION_RESET_PHONE, None)
        self.request.session.pop(SESSION_RESET_VERIFIED, None)

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, "اطلاعات و رمز عبور شما با موفقیت به‌روزرسانی شد.")
        return redirect("core:home")
