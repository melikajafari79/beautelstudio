"""
ابزارهای کمکیِ عمومی که بین چند اپ مشترک است.
"""

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ENGLISH_DIGITS = "0123456789"

_DIGIT_TRANSLATION_TABLE = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _ENGLISH_DIGITS + _ENGLISH_DIGITS,
)


def to_english_digits(value):
    """
    ارقام فارسی (۰-۹) و عربی (٠-٩) که با صفحه‌کلید فارسی گوشی تایپ می‌شوند
    را به ارقام انگلیسی استاندارد (0-9) تبدیل می‌کند.

    بدون این تابع، اعتبارسنجی شماره موبایل و کد پیامکی برای کاربرانی که
    روی گوشی‌شان صفحه‌کلید فارسی دارند (اکثریت کاربران) شکست می‌خورد،
    چون مثلاً "۰۹۱۲۳۴۵۶۷۸۹" با الگوی ^09\\d{9}$ مطابقت ندارد.
    """
    if value is None:
        return value
    return str(value).translate(_DIGIT_TRANSLATION_TABLE)
