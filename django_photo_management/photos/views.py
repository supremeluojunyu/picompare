import base64
import os

from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from photo_access.utils import allowed_person_numbers, person_number_allowed

from .models import (
    PendingConfirmation,
    PersonPhoto,
    UploadBatch,
    UploadQualityFailureItem,
    UploadQualityReport,
)
from .oracle_sync import upload_should_sync_to_oracle
from .serializers import PendingSerializer
from .tasks import compare_and_save, process_single_photo
from .upload_validation import get_effective_rules, validate_upload_constraints


def _person_number_from_upload_name(name: str) -> str:
    base = os.path.basename(name)
    return os.path.splitext(base)[0]


def _scoped_photo_queryset(user, qs):
    allowed = allowed_person_numbers(user)
    if allowed is None:
        return qs
    if not allowed:
        return qs.none()
    return qs.filter(person_number__in=allowed)


class PhotoUploadViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def upload_batch(self, request):
        if request.user.role not in ['admin', 'secretary']:
            return Response({'error': '无权限'}, status=403)
        files = request.FILES.getlist('photos')
        if files:
            skipped = []
            to_run = []
            for f in files:
                raw = f.read()
                person_number = _person_number_from_upload_name(f.name)
                if not person_number_allowed(request.user, person_number):
                    skipped.append(person_number)
                    continue
                to_run.append((raw, person_number))
            if not to_run:
                return Response({
                    'error': '没有符合管理组备案的证件号照片',
                    'skipped_person_numbers': skipped,
                }, status=400)

            rules = get_effective_rules()
            valid_pairs = []
            failed_rows = []
            for raw, person_number in to_run:
                ok, issues = validate_upload_constraints(raw, rules)
                if ok:
                    valid_pairs.append((raw, person_number))
                else:
                    failed_rows.append((person_number, raw, issues))

            quality_report = None
            if failed_rows:
                quality_report = UploadQualityReport.objects.create(uploader=request.user)
                for person_number, raw, issues in failed_rows[:200]:
                    UploadQualityFailureItem.objects.create(
                        report=quality_report,
                        person_number=person_number,
                        preview_image=raw,
                        issues=issues,
                    )

            if not valid_pairs:
                err_body = {
                    'error': '所选照片均未通过上传规范校验，已拒绝入库',
                    'quality_fail_count': len(failed_rows),
                }
                if quality_report:
                    err_body['quality_report_id'] = quality_report.id
                    err_body['quality_redirect'] = request.build_absolute_uri(
                        f'/upload/quality-report/{quality_report.pk}/'
                    )
                return Response(err_body, status=400)

            want_oracle = upload_should_sync_to_oracle(request.data, request.POST)
            batch = UploadBatch.objects.create(uploader=request.user, total_count=len(valid_pairs))
            for raw, person_number in valid_pairs:
                process_single_photo.delay(
                    base64.b64encode(raw).decode('ascii'),
                    person_number,
                    batch.id,
                    sync_to_oracle=want_oracle,
                )
            resp = {
                'batch_id': batch.id,
                'status': 'processing',
                'count': len(valid_pairs),
            }
            if skipped:
                resp['skipped_person_numbers'] = skipped
                resp['skipped_count'] = len(skipped)
            if quality_report:
                resp['quality_report_id'] = quality_report.pk
                resp['quality_fail_count'] = len(failed_rows)
                resp['quality_redirect'] = request.build_absolute_uri(
                    f'/upload/quality-report/{quality_report.pk}/'
                )
                resp['quality_partial'] = True
            return Response(resp)
        folder_path = request.data.get('folder_path')
        if folder_path and os.path.isdir(folder_path):
            batch = UploadBatch.objects.create(uploader=request.user)
            return Response({'batch_id': batch.id, 'status': 'processing'})
        return Response({'error': '请选择图片文件或提供有效文件夹路径'}, status=400)

    @action(detail=False, methods=['post'])
    def confirm_pending(self, request):
        pending_id = request.data.get('pending_id')
        action_taken = request.data.get('action')
        pending = get_object_or_404(PendingConfirmation, id=pending_id, confirmed=False)
        if not person_number_allowed(request.user, pending.person_number):
            return Response({'error': '无权处理该证件号的待确认项'}, status=403)
        if action_taken == 'accept':
            want_oracle = upload_should_sync_to_oracle(request.data, request.POST)
            result = compare_and_save(
                bytes(pending.adjusted_image),
                pending.person_number,
                pending.upload_batch_id,
                is_adjusted=True,
                sync_to_oracle=want_oracle,
            )
            pending.confirmed = True
            pending.confirmed_by = request.user
            pending.save()
            return Response(result)
        pending.delete()
        return Response({'status': 'rejected'})

    @action(detail=False, methods=['get'])
    def pending_list(self, request):
        qs = PendingConfirmation.objects.filter(confirmed=False)
        qs = _scoped_photo_queryset(request.user, qs)
        serializer = PendingSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        from datetime import datetime, timedelta

        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        qs = PersonPhoto.objects.filter(upload_time__date__gte=week_ago)
        qs = _scoped_photo_queryset(request.user, qs)
        total_uploads = qs.count()
        compared = qs.exclude(similarity_score__isnull=True)
        compared_n = compared.count()
        pass_count = compared.filter(similarity_score__gte=0.85).count()
        pass_rate = pass_count / compared_n if compared_n > 0 else 0
        baseline_week = qs.filter(adjust_details__is_baseline=True).count()
        return Response({
            'week_uploads': total_uploads,
            'week_compared': compared_n,
            'week_baselines': baseline_week,
            'pass_rate': pass_rate,
        })
