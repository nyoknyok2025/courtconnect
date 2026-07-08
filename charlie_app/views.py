import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q, F, Count
from .models import (
    CorruptionReport,
    ReportStatus,
    Department,
    ReportComment,
)
from .ml_service import predict_report_category as predict_report_category_model
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, permissions
from .serializers import CorruptionReportSerializer

# Home Page
def home(request):
    """Show login first, then route authenticated users to the correct dashboard."""
    if not request.user.is_authenticated:
        return redirect('charlie_app:login')
    return redirect('charlie_app:dashboard')


def register(request):
    """Allow users to create a regular account."""
    if request.user.is_authenticated:
        return redirect('charlie_app:dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username, password=request.POST['password1'])
            if user is not None:
                login(request, user)
                return redirect('charlie_app:dashboard')
        else:
            # surface form errors to the user via messages
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field}: {e}")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


def register_redirect(request):
    """Ensure users reach the registration form. If already authenticated, log them out first."""
    if request.user.is_authenticated:
        logout(request)
    return redirect('charlie_app:register')


def logout_and_redirect(request):
    """Log the user out and redirect to the login page."""
    if request.user.is_authenticated:
        logout(request)
    return redirect('charlie_app:login')


# Report Listing
class ReportListView(ListView):
    """List all corruption reports"""
    model = CorruptionReport
    template_name = 'report_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = CorruptionReport.objects.all()
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status__status=status)
        
        # Filter by severity
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CorruptionReport.CATEGORY_CHOICES
        context['statuses'] = ReportStatus.objects.all()
        context['severities'] = CorruptionReport.SEVERITY_CHOICES
        return context


# Report Detail View
class ReportDetailView(DetailView):
    """View detailed report and comments"""
    model = CorruptionReport
    template_name = 'report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        return context


# Report Submission Form
class CreateReportView(CreateView):
    """Create a new corruption report"""
    model = CorruptionReport
    template_name = 'report_form.html'
    fields = ['title', 'description', 'category', 'severity', 'location', 'related_department', 'reporter_name', 'reporter_email', 'is_anonymous', 'evidence_file']
    # After a user submits a report, show their reports list (user-scoped path)
    success_url = reverse_lazy('charlie_app:my_reports')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not Department.objects.exists():
            default_departments = [
                {
                    'name': 'Anti-Corruption Commission',
                    'email': 'contact@acc.gov',
                    'phone': '+1-800-ACC-HELP',
                    'description': 'Handles corruption complaints and investigations.',
                },
                {
                    'name': 'Public Service Oversight Authority',
                    'email': 'oversight@psa.gov',
                    'phone': '+1-800-PSA-INFO',
                    'description': 'Monitors public service conduct and safety.',
                },
                {
                    'name': 'Governance & Ethics Department',
                    'email': 'ethics@govdept.gov',
                    'phone': '+1-800-GOV-ETH',
                    'description': 'Reviews governance issues and official misconduct.',
                },
            ]
            for dept in default_departments:
                Department.objects.get_or_create(name=dept['name'], defaults=dept)

        if 'related_department' in form.fields:
            form.fields['related_department'].empty_label = 'Select a department...'
        return form
    
    def form_valid(self, form):
        # Set the reporter if user is logged in
        if self.request.user.is_authenticated:
            form.instance.reporter = self.request.user
        # Avoid resolving the related object (which raises DoesNotExist when the FK points
        # to a non-existent row). Check the raw FK id instead and ensure it refers to an
        # existing ReportStatus. If missing, create a default 'submitted' status and assign it.
        status_id = getattr(form.instance, 'status_id', None)
        if status_id is None or not ReportStatus.objects.filter(pk=status_id).exists():
            default_status, created = ReportStatus.objects.get_or_create(
                status='submitted',
                defaults={'description': 'Automatically created default status'}
            )
            form.instance.status = default_status

        return super().form_valid(form)


class CorruptionReportViewSet(viewsets.ModelViewSet):
    queryset = CorruptionReport.objects.all().order_by('-created_at')
    serializer_class = CorruptionReportSerializer
    permission_classes = [permissions.AllowAny]


@require_http_methods(["POST"])
def predict_report_category(request):
    """Return a predicted category for a report description using the pretrained model."""
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    text = payload.get('text') or payload.get('description') or payload.get('message') or ''
    if not str(text).strip():
        return JsonResponse({'error': 'Provide text to classify.'}, status=400)

    return JsonResponse(predict_report_category_model(str(text)))


def _serialize_report(report, request=None):
    data = {
        'id': report.pk,
        'title': report.title,
        'description': report.description,
        'category': report.category,
        'severity': report.severity,
        'location': report.location,
        'related_department_id': report.related_department_id,
        'related_department': report.related_department.name if report.related_department else None,
        'reporter_name': report.reporter_name,
        'reporter_email': report.reporter_email,
        'is_anonymous': report.is_anonymous,
        'status': report.status.status if report.status else None,
        'evidence_file': None,
        'created_at': report.created_at.isoformat() if report.created_at else None,
        'updated_at': report.updated_at.isoformat() if report.updated_at else None,
    }
    if report.evidence_file:
        try:
            data['evidence_file'] = request.build_absolute_uri(report.evidence_file.url) if request is not None else report.evidence_file.url
        except Exception:
            data['evidence_file'] = None
    return data


@require_http_methods(['GET', 'POST'])
def api_reports(request):
    if request.method == 'GET':
        reports = CorruptionReport.objects.all().order_by('-created_at')
        data = [_serialize_report(report, request) for report in reports]
        return JsonResponse(data, safe=False)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    required = ['title', 'description', 'category', 'severity', 'location', 'reporter_name', 'reporter_email']
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return JsonResponse({'error': 'Missing required fields.', 'missing': missing}, status=400)

    related_department = None
    department_value = payload.get('related_department')
    if department_value:
        if isinstance(department_value, int) or str(department_value).isdigit():
            try:
                related_department = Department.objects.get(pk=int(department_value))
            except Department.DoesNotExist:
                related_department = None
        else:
            related_department = Department.objects.filter(name=str(department_value)).first()
            if related_department is None:
                related_department = Department.objects.create(
                    name=str(department_value),
                    email='no-reply@example.com',
                    phone='',
                    description='Created from API request',
                )

    report = CorruptionReport.objects.create(
        title=payload['title'],
        description=payload['description'],
        category=payload['category'],
        severity=payload['severity'],
        location=payload['location'],
        related_department=related_department,
        reporter_name=payload['reporter_name'],
        reporter_email=payload['reporter_email'],
        is_anonymous=bool(payload.get('is_anonymous', False)),
        status=ReportStatus.objects.filter(status='submitted').first(),
    )

    if request.user.is_authenticated:
        report.reporter = request.user
        report.save()

    return JsonResponse(_serialize_report(report, request), status=201)


@require_http_methods(['GET'])
def api_report_detail(request, pk):
    report = get_object_or_404(CorruptionReport, pk=pk)
    return JsonResponse(_serialize_report(report, request))


# My Reports (for logged-in users)
@login_required
def my_reports(request):
    """Show a logged-in user's own reports."""
    reports = CorruptionReport.objects.filter(reporter=request.user)
    total_reports = reports.count()
    resolved_reports = reports.filter(status__status='resolved').count()
    open_reports = reports.exclude(status__status__in=['resolved', 'closed', 'rejected']).count()

    context = {
        'reports': reports,
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'open_reports': open_reports,
    }
    return render(request, 'my_reports.html', context)


@login_required
def dashboard(request):
    """Route authenticated users to the correct dashboard."""
    if request.user.is_staff:
        return redirect('charlie_app:admin_dashboard')
    return redirect('charlie_app:user_dashboard')


@login_required
def admin_dashboard(request):
    """Admin dashboard showing all reports and business metrics."""
    if not request.user.is_staff:
        return redirect('charlie_app:user_dashboard')

    total_reports = CorruptionReport.objects.count()
    recent_reports = CorruptionReport.objects.all()[:5]
    pending_count = CorruptionReport.objects.exclude(status__status__in=['resolved', 'closed', 'rejected']).count()

    context = {
        'total_reports': total_reports,
        'recent_reports': recent_reports,
        'pending_count': pending_count,
    }
    return render(request, 'dashboard.html', context)


@login_required
def user_dashboard(request):
    """Dashboard for normal users showing their own reports."""
    reports = CorruptionReport.objects.filter(reporter=request.user)
    total_reports = reports.count()
    resolved_reports = reports.filter(status__status='resolved').count()
    open_reports = reports.exclude(status__status__in=['resolved', 'closed', 'rejected']).count()

    context = {
        'reports': reports,
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'open_reports': open_reports,
    }
    return render(request, 'user_dashboard.html', context)


# Add comment to report
@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    """Add a comment to a report"""
    report = get_object_or_404(CorruptionReport, pk=pk)
    
    if request.user.is_staff or request.user == report.reporter:
        text = request.POST.get('text')
        if text:
            comment = ReportComment.objects.create(
                report=report,
                author=request.user,
                text=text,
                is_official=request.user.is_staff
            )
            # Redirect based on request path to the appropriate scoped detail view
            path = request.path or ''
            if path.startswith('/admin/'):
                return redirect('admin_report_detail', pk=pk)
            if path.startswith('/user/'):
                return redirect('charlie_app:report_detail', pk=pk)
            return redirect('charlie_app:report_detail', pk=pk)

    # If not authorized or no text, redirect based on path as well
    path = request.path or ''
    if path.startswith('/admin/'):
        return redirect('admin_report_detail', pk=pk)
    if path.startswith('/user/'):
        return redirect('charlie_app:report_detail', pk=pk)
    return redirect('charlie_app:report_detail', pk=pk)


# API: Get report statistics
def report_statistics(request):
    """Return JSON statistics"""
    stats = {
        'total_reports': CorruptionReport.objects.count(),
        'by_category': list(CorruptionReport.objects.values('category').annotate(count=Count('id'))),
        'by_status': list(CorruptionReport.objects.values('status__status').annotate(count=Count('id'))),
        'by_severity': list(CorruptionReport.objects.values('severity').annotate(count=Count('id'))),
    }
    return JsonResponse(stats)


@login_required
@require_http_methods(["POST"])
def resolve_report(request, pk):
    """Mark a report as resolved (staff only)."""
    # Only staff may mark reports resolved
    if not request.user.is_staff:
        return redirect('charlie_app:user_dashboard')

    report = get_object_or_404(CorruptionReport, pk=pk)
    resolved_status = ReportStatus.objects.filter(status='resolved').first()
    if not resolved_status:
        resolved_status = ReportStatus.objects.create(status='resolved', description='Marked resolved by admin')

    report.status = resolved_status
    from django.utils import timezone
    report.resolved_at = timezone.now()
    report.save()

    # Redirect back to admin report detail if available, otherwise to list
    try:
        return redirect('admin_report_detail', pk=pk)
    except Exception:
        return redirect('admin_report_list')
