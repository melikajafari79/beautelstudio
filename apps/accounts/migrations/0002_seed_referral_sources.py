"""
چند گزینه‌ی پیش‌فرض برای «شیوه‌ی آشنایی با ما» اضافه می‌کند.
بدون این migration، فیلد اختیاری referral_source در فرم ثبت‌نام همیشه
خالی می‌ماند چون هیچ ReferralSource ای در دیتابیس وجود نخواهد داشت.
مدیر سالن می‌تواند بعداً از پنل ادمین، گزینه‌های بیشتری اضافه/ویرایش کند.
"""
from django.db import migrations

REFERRAL_SOURCES = [
    ("اینستاگرام", 10),
    ("جستجوی گوگل", 20),
    ("معرفی دوستان و آشنایان", 30),
    ("تبلیغات پیامکی", 40),
    ("سایر موارد", 100),
]


def seed_referral_sources(apps, schema_editor):
    ReferralSource = apps.get_model("accounts", "ReferralSource")
    for title, sort_order in REFERRAL_SOURCES:
        ReferralSource.objects.get_or_create(title=title, defaults={"sort_order": sort_order})


def remove_referral_sources(apps, schema_editor):
    ReferralSource = apps.get_model("accounts", "ReferralSource")
    ReferralSource.objects.filter(title__in=[title for title, _ in REFERRAL_SOURCES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_referral_sources, remove_referral_sources),
    ]
