from django.contrib import admin
from django.urls import path, include
from charlie_app.views import ReportListView, ReportDetailView, add_comment, resolve_report
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Serve app's admin-facing reports list and detail pages at /admin/reports/
    path('admin/reports/', ReportListView.as_view(), name='admin_report_list'),
    path('admin/reports/<int:pk>/', ReportDetailView.as_view(), name='admin_report_detail'),
    path('admin/reports/<int:pk>/comment/', add_comment, name='admin_add_comment'),
    path('admin/reports/<int:pk>/resolve/', resolve_report, name='admin_resolve_report'),
    path('admin/', admin.site.urls),
    path('', include('charlie_app.urls', namespace='charlie_app')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
