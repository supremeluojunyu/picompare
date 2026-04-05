import cv2
import numpy as np
from django.conf import settings
from .image_processor import get_image_dimensions
from .models import UploadValidationConfig


def get_effective_rules():
    row = UploadValidationConfig.objects.order_by('-updated_at', '-id').first()
    if row:
        return {
            'max_file_size_mb': row.max_file_size_mb,
            'min_width': row.min_width,
            'min_height': row.min_height,
            'max_width': row.max_width,
            'max_height': row.max_height,
            'enable_clarity_check': row.enable_clarity_check,
            'clarity_threshold': row.clarity_threshold,
            'background_color_rules': row.background_color_rules or [],
        }
    return {
        'max_file_size_mb': settings.PHOTO_MAX_SIZE_MB,
        'min_width': 100,
        'min_height': 100,
        'max_width': 4096,
        'max_height': 4096,
        'enable_clarity_check': True,
        'clarity_threshold': settings.CLARITY_THRESHOLD,
        'background_color_rules': settings.BACKGROUND_ALLOWED_COLORS,
    }


def _mean_corner_colors(bgr: np.ndarray):
    h, w = bgr.shape[:2]
    pts = [
        bgr[0, 0],
        bgr[0, w - 1],
        bgr[h - 1, 0],
        bgr[h - 1, w - 1],
    ]
    return np.mean(pts, axis=0)


def validate_upload_constraints(photo_bytes: bytes, rules: dict) -> tuple[bool, list[str]]:
    issues = []
    max_mb = rules.get('max_file_size_mb') or settings.PHOTO_MAX_SIZE_MB
    if len(photo_bytes) > max_mb * 1024 * 1024:
        issues.append(f'文件超过 {max_mb} MB')

    try:
        w, h = get_image_dimensions(photo_bytes)
    except Exception:
        issues.append('无法解析为有效图片')
        return False, issues

    if w < rules['min_width'] or h < rules['min_height']:
        issues.append(f'尺寸过小（当前 {w}×{h}，最小 {rules["min_width"]}×{rules["min_height"]}）')
    if w > rules['max_width'] or h > rules['max_height']:
        issues.append(f'尺寸过大（当前 {w}×{h}，最大 {rules["max_width"]}×{rules["max_height"]}）')

    arr = np.frombuffer(photo_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        issues.append('OpenCV 无法解码图像')
        return False, issues

    if rules.get('enable_clarity_check'):
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap < rules.get('clarity_threshold', settings.CLARITY_THRESHOLD):
            issues.append(f'清晰度不足（拉普拉斯方差 {lap:.1f}，阈值 {rules.get("clarity_threshold")}）')

    mean_bgr = _mean_corner_colors(bgr)
    r, g, b = float(mean_bgr[2]), float(mean_bgr[1]), float(mean_bgr[0])
    color_rules = rules.get('background_color_rules') or []
    if color_rules:
        ok = False
        for rule in color_rules:
            try:
                if (
                    rule['r_min'] <= r <= rule['r_max']
                    and rule['g_min'] <= g <= rule['g_max']
                    and rule['b_min'] <= b <= rule['b_max']
                ):
                    ok = True
                    break
            except (KeyError, TypeError):
                continue
        if not ok:
            issues.append(f'四角平均色 RGB 约 ({r:.0f},{g:.0f},{b:.0f})，不符合背景色规则')

    return len(issues) == 0, issues
