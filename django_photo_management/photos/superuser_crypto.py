"""仅超级管理员：Fernet 秘钥配置、读取、备份导出。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OraclePhotoSyncConfig, SuperuserCryptoSettings
from .oracle_secret import decrypt_oracle_password_for_connection, derived_fernet_key_b64


class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_superuser)


def _env_fernet_set() -> bool:
    return bool((getattr(settings, 'ORACLE_SYNC_FERNET_KEY', None) or '').strip())


def _db_fernet_row() -> SuperuserCryptoSettings:
    obj, _ = SuperuserCryptoSettings.objects.get_or_create(pk=1)
    return obj


def _effective_source() -> str:
    if _env_fernet_set():
        return 'env'
    row = SuperuserCryptoSettings.objects.filter(pk=1).first()
    if row and (row.oracle_sync_fernet_key or '').strip():
        return 'database'
    return 'derived'


def _fernet_key_fingerprint(key_str: str) -> str:
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:16]


def _effective_fernet_key_string() -> tuple[str, str]:
    """(密钥字符串, source) 与 oracle_secret._fernet 逻辑一致。"""
    src = _effective_source()
    if src == 'env':
        return (settings.ORACLE_SYNC_FERNET_KEY.strip(), 'env')
    if src == 'database':
        return (_db_fernet_row().oracle_sync_fernet_key.strip(), 'database')
    return (derived_fernet_key_b64(), 'derived')


def _validate_fernet_key(key: str) -> str | None:
    s = (key or '').strip()
    if not s:
        return None
    try:
        Fernet(s.encode('utf-8'))
    except Exception:
        return '不是有效的 Fernet 密钥（应为 urlsafe base64，约 44 字符）'
    return None


class SuperuserCryptoStatusView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        src = _effective_source()
        key_str, _ = _effective_fernet_key_string()
        fp = _fernet_key_fingerprint(key_str) if key_str else None
        cfg = OraclePhotoSyncConfig.objects.order_by('-id').first()
        has_oracle_pw = bool(cfg and (cfg.password or '').strip())
        row = SuperuserCryptoSettings.objects.filter(pk=1).first()
        db_has = bool(row and (row.oracle_sync_fernet_key or '').strip())
        return Response(
            {
                'effective_source': src,
                'effective_source_label': {
                    'env': '环境变量 ORACLE_SYNC_FERNET_KEY',
                    'database': '数据库（本页保存）',
                    'derived': '由 Django SECRET_KEY 派生',
                }.get(src, src),
                'env_key_set': _env_fernet_set(),
                'database_key_set': db_has,
                'key_fingerprint': fp,
                'oracle_config_exists': cfg is not None,
                'oracle_has_saved_password': has_oracle_pw,
            }
        )


class SuperuserCryptoSaveKeyView(APIView):
    permission_classes = [IsSuperuser]

    def post(self, request):
        if _env_fernet_set():
            return Response(
                {
                    'error': '当前生效密钥来自环境变量 ORACLE_SYNC_FERNET_KEY，无法通过前端覆盖。'
                    '请修改服务器环境变量，或取消该变量后再使用本页保存。',
                },
                status=status.HTTP_409_CONFLICT,
            )
        raw = request.data.get('fernet_key')
        if raw is None:
            return Response({'error': '缺少 fernet_key 字段（可传空字符串以清除数据库中的密钥）'}, status=400)
        s = (raw if isinstance(raw, str) else str(raw)).strip()
        if not s:
            row = _db_fernet_row()
            row.oracle_sync_fernet_key = ''
            row.save(update_fields=['oracle_sync_fernet_key', 'updated_at'])
            return Response({'ok': True, 'cleared': True, 'effective_source': _effective_source()})
        err = _validate_fernet_key(s)
        if err:
            return Response({'error': err}, status=400)
        row = _db_fernet_row()
        row.oracle_sync_fernet_key = s
        row.save(update_fields=['oracle_sync_fernet_key', 'updated_at'])
        return Response({'ok': True, 'effective_source': _effective_source(), 'key_fingerprint': _fernet_key_fingerprint(s)})


class SuperuserCryptoRevealView(APIView):
    permission_classes = [IsSuperuser]

    def post(self, request):
        target = (request.data.get('target') or '').strip().lower()
        if target == 'fernet':
            key_str, src = _effective_fernet_key_string()
            return Response(
                {
                    'target': 'fernet',
                    'effective_source': src,
                    'fernet_key': key_str,
                    'warning': '请勿泄露；更换密钥后已加密的 Oracle 密码需重新在后台保存。',
                }
            )
        if target == 'oracle_password':
            cfg = OraclePhotoSyncConfig.objects.order_by('-id').first()
            if not cfg or not (cfg.password or '').strip():
                return Response({'error': '未配置 Oracle 同步或密码为空'}, status=404)
            try:
                plain = decrypt_oracle_password_for_connection(cfg.password)
            except ValueError as e:
                return Response({'error': str(e)}, status=400)
            return Response(
                {
                    'target': 'oracle_password',
                    'password': plain,
                    'warning': '此为 Oracle 数据库账户明文密码，仅限应急查看，请勿泄露。',
                }
            )
        return Response({'error': 'target 须为 fernet 或 oracle_password'}, status=400)


class SuperuserCryptoExportView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        include_oracle = request.query_params.get('include_oracle_password') in ('1', 'true', 'yes', 'on')
        key_str, src = _effective_fernet_key_string()
        payload = {
            'version': 1,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'effective_source': src,
            'fernet_key': key_str,
            'notes': (
                '由 SECRET_KEY 派生时请同时安全备份 Django SECRET_KEY；'
                '更换 Fernet 密钥后请在管理后台重新保存 Oracle 数据库密码。'
                if src == 'derived'
                else '请妥善保管本文件，勿提交到版本库。'
            ),
        }
        if include_oracle:
            cfg = OraclePhotoSyncConfig.objects.order_by('-id').first()
            if cfg and (cfg.password or '').strip():
                try:
                    payload['oracle_password'] = decrypt_oracle_password_for_connection(cfg.password)
                except ValueError as e:
                    payload['oracle_password_error'] = str(e)
            else:
                payload['oracle_password'] = None
        body = json.dumps(payload, ensure_ascii=False, indent=2)
        resp = HttpResponse(body, content_type='application/json; charset=utf-8')
        ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')
        name = f'oracle-crypto-backup-{ts}.json'
        resp['Content-Disposition'] = f'attachment; filename="{name}"'
        return resp
