"""
منطق تولید، ارسال و بررسیِ کد یکبار مصرف (OTP).
هم در فرآیند ثبت‌نام و هم در فرآیند «فراموشی رمز عبور» استفاده می‌شود؛
چون OTPRequest بر اساس شماره موبایل کار می‌کند نه کاربر، نیازی به فیلد
جداگانه برای «هدف» کد نیست.
"""
import random
from datetime import timedelta

from django.utils import timezone

from apps.notifications.services import send_sms

from .models import OTPRequest

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 3
OTP_RESEND_SECONDS = 60  # حداقل فاصله‌ی زمانی بین دو درخواست کد برای یک شماره


def _generate_otp_code() -> str:
    return f"{random.randint(0, 10**OTP_LENGTH - 1):0{OTP_LENGTH}d}"


def can_resend_otp(phone_number: str):
    """
    آیا اجازه‌ی ارسال کد جدید برای این شماره وجود دارد؟
    خروجی: (اجازه_داده_شد: bool, ثانیه‌های_باقی‌مانده: int)
    """
    last = OTPRequest.objects.filter(phone_number=phone_number).order_by("-created_at").first()
    if last is None:
        return True, 0

    elapsed = (timezone.now() - last.created_at).total_seconds()
    remaining = OTP_RESEND_SECONDS - elapsed
    if remaining > 0:
        return False, int(remaining) + 1
    return True, 0


def create_and_send_otp(phone_number: str):
    """
    یک کد تایید جدید می‌سازد و پیامک می‌کند.
    اگر هنوز مدت‌زمان محدودیت ارسال (cooldown) از درخواست قبلی نگذشته باشد،
    به‌جای ساخت/ارسال کد تکراری، (None, ثانیه‌های_باقی‌مانده) برمی‌گرداند
    تا view بتواند پیام مناسب نشان دهد (کد قبلی هنوز معتبر است).

    خروجی: (otp_request یا None, ثانیه‌های_باقی‌مانده)
    """
    allowed, remaining = can_resend_otp(phone_number)
    if not allowed:
        return None, remaining

    code = _generate_otp_code()
    otp = OTPRequest.objects.create(
        phone_number=phone_number,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    send_sms(
        phone_number,
        f"سالن زیبایی الی\nکد تایید شما: {code}\nاعتبار: {OTP_EXPIRY_MINUTES} دقیقه",
    )
    return otp, 0


def verify_otp(phone_number: str, code: str):
    """
    آخرین کد در انتظارِ این شماره را با کد وارد شده مقایسه می‌کند.
    خروجی: (موفق: bool, پیام_خطا در صورت ناموفق بودن یا None)
    """
    otp = (
        OTPRequest.objects.filter(phone_number=phone_number, status=OTPRequest.OTPStatus.PENDING)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        return False, "کد معتبری برای این شماره یافت نشد. لطفاً دوباره درخواست دهید."

    if otp.is_expired:
        otp.status = OTPRequest.OTPStatus.EXPIRED
        otp.save(update_fields=["status"])
        return False, "کد تایید منقضی شده است. لطفاً دوباره درخواست دهید."

    if not otp.can_verify():
        return False, "تعداد تلاش‌های مجاز برای این کد به پایان رسیده. لطفاً دوباره درخواست دهید."

    if otp.code != code:
        otp.attempt_count += 1
        if otp.attempt_count >= otp.max_attempts:
            otp.status = OTPRequest.OTPStatus.FAILED
        otp.save(update_fields=["attempt_count", "status"])
        return False, "کد وارد شده صحیح نیست."

    otp.status = OTPRequest.OTPStatus.VERIFIED
    otp.verified_at = timezone.now()
    otp.save(update_fields=["status", "verified_at"])
    return True, None
