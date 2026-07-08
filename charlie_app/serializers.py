from rest_framework import serializers

from .models import CorruptionReport, Department, ReportStatus, ReportComment


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'email', 'phone', 'description', 'created_at']


class ReportStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStatus
        fields = ['id', 'status', 'description']


class ReportCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = ReportComment
        fields = ['id', 'report', 'author', 'author_username', 'text', 'is_official', 'created_at', 'updated_at']
        read_only_fields = ['author_username', 'created_at', 'updated_at']


class CorruptionReportSerializer(serializers.ModelSerializer):
    related_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), required=False, allow_null=True
    )
    status = serializers.PrimaryKeyRelatedField(
        queryset=ReportStatus.objects.all(), required=False, allow_null=True
    )
    evidence_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = CorruptionReport
        fields = [
            'id',
            'title',
            'description',
            'category',
            'severity',
            'location',
            'related_department',
            'reporter_name',
            'reporter_email',
            'is_anonymous',
            'status',
            'evidence_file',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
