"""
لایه‌ی ارسال پیامک.

⚠️ توجه مهم:
هیچ سرویس‌دهنده‌ی پیامکی واقعی هنوز در requirements پروژه نصب/تنظیم نشده
(نگاه کنید به requirements/base.txt). به همین دلیل تابع send_sms در حالت
DEBUG=True فقط پیام را در کنسول/لاگ سرور چاپ می‌کند تا کل فرآیند ثبت‌نام/
ورود به‌صورت کامل و بدون نیاز به سرویس پیامکی واقعی، قابل تست باشد.

پیش از انتقال سایت به حالت production، باید بدنه‌ی این تابع را با فراخوانی
API واقعی سرویس‌دهنده‌ی پیامکی‌تان (مثلاً کاوه‌نگار، ملی‌پیامک، ippanel و ...)
جایگزین کنید. چون تمام کدهای دیگر (ثبت‌نام، ورود، فراموشی رمز) فقط با همین
یک تابع کار می‌کنند، تغییر این بخش هیچ اثری روی بقیه‌ی سیستم نمی‌گذارد.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number: str, message: str) -> bool:
    """
    ارسال پیامک به یک شماره موبایل.
    خروجی: True اگر پیامک (یا در حالت توسعه، چاپ آن) با موفقیت انجام شد.
    """
    if settings.DEBUG:
        # حالت توسعه: به‌جای تماس با یک سرویس پیامکی واقعی و پولی،
        # پیام را در ترمینال چاپ می‌کنیم تا بتوانید کد تایید را ببینید.
        print(f"\n[پیامک شبیه‌سازی‌شده -> {phone_number}]\n{message}\n")
        logger.info("SMS (console backend) to %s: %s", phone_number, message)
        return True

    # TODO: قبل از انتقال به سرور اصلی، این بخش را با سرویس پیامکی واقعی
    # جایگزین کنید. نمونه (کاوه‌نگار):
    #
    #   from kavenegar import KavenegarAPI
    #   api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
    #   api.sms_send({'receptor': phone_number, 'message': message})
    #
    logger.warning(
        "هیچ سرویس‌دهنده‌ی پیامکی واقعی تنظیم نشده؛ پیامک به %s ارسال نشد.",
        phone_number,
    )
    return False
