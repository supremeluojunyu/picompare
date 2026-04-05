import base64

from django.views.generic import DetailView

from photo_site.mixins import SiteLoginRequiredMixin

from .models import UploadQualityReport


def _image_mime(image_bytes: bytes) -> str:
    if len(image_bytes) >= 8 and image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    return 'image/jpeg'


class UploadQualityReportView(SiteLoginRequiredMixin, DetailView):
    model = UploadQualityReport
    template_name = 'upload_quality_report.html'
    context_object_name = 'report'

    def get_queryset(self):
        return (
            UploadQualityReport.objects.filter(uploader=self.request.user)
            .prefetch_related('items')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = []
        for it in self.object.items.all():
            raw = bytes(it.preview_image)
            rows.append({
                'person_number': it.person_number,
                'issues': list(it.issues or []),
                'data_url': f'data:{_image_mime(raw)};base64,{base64.b64encode(raw).decode("ascii")}',
            })
        ctx['failure_rows'] = rows
        return ctx
