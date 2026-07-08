from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework.routers import DefaultRouter
from . import views
from .forms import CaptchaAuthenticationForm

app_name = 'charlie_app'

router = DefaultRouter()
router.register(r'api/reports', views.CorruptionReportViewSet, basename='api_reports')

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path(
        'login/',
        LoginView.as_view(template_name='login.html', authentication_form=CaptchaAuthenticationForm),
        name='login',
    ),
    path('logout/', views.logout_and_redirect, name='logout'),
    path('register/', views.register, name='register'),
    path('register-redirect/', views.register_redirect, name='register_redirect'),
    
    # Reports
    # Admin-facing reports list
    path('admin/reports/', views.ReportListView.as_view(), name='admin_report_list'),
    # Detail view remains shared for backward compatibility
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    # User-scoped detail & comment endpoints
    path('user/reports/<int:pk>/', views.ReportDetailView.as_view(), name='user_report_detail'),
    path('user/reports/<int:pk>/comment/', views.add_comment, name='user_add_comment'),
    # User-scoped create & my-reports to avoid collision with admin paths
    path('user/reports/create/', views.CreateReportView.as_view(), name='report_create'),
    path('user/my-reports/', views.my_reports, name='my_reports'),
    
    # Comments (legacy/shared)
    path('reports/<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),

    # Business pages
    path('api/statistics/', views.report_statistics, name='statistics'),
    path('api/ml/predict/', views.predict_report_category, name='api_ml_predict'),
]

urlpatterns += router.urls
