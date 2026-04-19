from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Legacy URL support: redirect /accounts/signup/ to the new student signup path.
    path('signup/', RedirectView.as_view(pattern_name='accounts:student_signup', permanent=False)),
    path('student/signup/', views.student_signup_request_otp, name='student_signup'),
    path('student/verify/', views.verify_otp, name='verify_otp'),
]
