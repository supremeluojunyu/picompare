import base64
import logging
import os

from celery import shared_task
from django.conf import settings

from photo_access.utils import person_number_allowed

from .face_recognizer import face_recognizer
from .models import PersonPhoto, UploadBatch
from .oracle_sync import sync_photo_blob
from .upload_validation import get_effective_rules, validate_upload_constraints

logger = logging.getLogger('photos')


@shared_task(bind=True, max_retries=3)
def process_upload_batch(self, batch_id, folder_path):
    del batch_id, folder_path
    pass


@shared_task(bind=True)
def process_single_photo(self, photo_bytes_base64, person_number, batch_id, sync_to_oracle=False):
    try:
        batch = UploadBatch.objects.get(pk=batch_id)
    except UploadBatch.DoesNotExist:
        return {'status': 'fail', 'reason': '上传批次不存在'}
    if not person_number_allowed(batch.uploader, person_number):
        return {
            'status': 'fail',
            'reason': '该证件号不在您管理组的备案范围内，或您未绑定照片管理组（请联系超级管理员）',
        }

    photo_bytes = base64.b64decode(photo_bytes_base64)
    return compare_and_save(
        photo_bytes, person_number, batch_id, is_adjusted=False, sync_to_oracle=sync_to_oracle
    )


def _persist_person_photo(
    photo_bytes,
    person_number,
    batch_id,
    uploader,
    is_adjusted,
    similarity_score,
    adjust_details,
    *,
    sync_to_oracle=False,
):
    filename = f'{person_number}_{batch_id}.jpg'
    file_full_path = os.path.join(str(settings.PHOTO_STORAGE_DIR), filename)
    os.makedirs(settings.PHOTO_STORAGE_DIR, exist_ok=True)
    with open(file_full_path, 'wb') as f:
        f.write(photo_bytes)
    PersonPhoto.objects.create(
        person_number=person_number,
        photo_blob=photo_bytes,
        file_path=file_full_path,
        uploader=uploader,
        batch_id=batch_id,
        similarity_score=similarity_score,
        is_adjusted=is_adjusted,
        adjust_details=adjust_details,
    )
    if sync_to_oracle:
        ok, err = sync_photo_blob(person_number, photo_bytes)
        if not ok:
            logger.warning('Oracle 同步失败 person_number=%s: %s', person_number, err)


def compare_and_save(photo_bytes, person_number, batch_id, is_adjusted, sync_to_oracle=False):
    ok_rules, rule_issues = validate_upload_constraints(photo_bytes, get_effective_rules())
    if not ok_rules:
        return {'status': 'fail', 'reason': '; '.join(rule_issues)}

    batch = UploadBatch.objects.get(pk=batch_id)
    uploader = batch.uploader
    if not person_number_allowed(uploader, person_number):
        return {'status': 'fail', 'reason': '该证件号不在您管理组的备案范围内'}

    prev_photo = PersonPhoto.objects.filter(person_number=person_number).order_by('-upload_time').first()
    if not prev_photo:
        if not settings.PHOTO_ALLOW_FIRST_AS_BASELINE:
            return {'status': 'fail', 'reason': f'编号 {person_number} 无前置照片'}
        if settings.PHOTO_BASELINE_REQUIRE_FACE:
            emb = face_recognizer.get_face_embedding(photo_bytes)
            if emb is None:
                return {
                    'status': 'fail',
                    'reason': '首张照片未检测到人脸，无法建立基准（可关闭 PHOTO_BASELINE_REQUIRE_FACE 或检查 InsightFace）',
                }
        details = {'is_baseline': True}
        _persist_person_photo(
            photo_bytes, person_number, batch_id, uploader, is_adjusted,
            similarity_score=None,
            adjust_details=details,
            sync_to_oracle=sync_to_oracle,
        )
        logger.info('基准照入库 person_number=%s batch_id=%s', person_number, batch_id)
        return {'status': 'success', 'is_baseline': True, 'similarity': None}

    emb_new = face_recognizer.get_face_embedding(photo_bytes)
    emb_old = face_recognizer.get_face_embedding(bytes(prev_photo.photo_blob))
    match, score = face_recognizer.compare(emb_new, emb_old)
    if not match:
        return {'status': 'fail', 'reason': f'人脸比对不通过，相似度{score:.3f}'}
    _persist_person_photo(
        photo_bytes, person_number, batch_id, uploader, is_adjusted,
        similarity_score=score,
        adjust_details={},
        sync_to_oracle=sync_to_oracle,
    )
    return {'status': 'success', 'is_baseline': False, 'similarity': score}
