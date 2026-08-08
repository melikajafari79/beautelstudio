from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # ثبت‌نام
    path("register/", views.RegisterView.as_view(), name="register"),
    path("register/verify/", views.VerifyRegisterView.as_view(), name="verify_register"),
    path("register/resend/", views.ResendRegisterOTPView.as_view(), name="resend_register_otp"),

    # ورود / خروج
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # فراموشی رمز عبور
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("forgot-password/verify/", views.VerifyResetOTPView.as_view(), name="verify_reset"),
    path("forgot-password/resend/", views.ResendResetOTPView.as_view(), name="resend_reset_otp"),
    path("edit-profile/", views.EditProfileView.as_view(), name="edit_profile"),
]
