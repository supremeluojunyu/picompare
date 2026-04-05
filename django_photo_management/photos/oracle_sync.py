"""按后台配置将照片二进制写入 Oracle 指定表字段（与 Django 主库独立连接）。"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from .oracle_secret import decrypt_oracle_password_for_connection

if TYPE_CHECKING:
    from .models import OraclePhotoSyncConfig

logger = logging.getLogger('photos')


def _ident(name: str) -> str:
    v = (name or '').strip()
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', v):
        raise ValueError(f'非法标识符: {name!r}')
    return v.upper()


def get_oracle_sync_config():
    from .models import OraclePhotoSyncConfig

    return OraclePhotoSyncConfig.objects.order_by('-id').first()


def sync_photo_blob(person_number: str, photo_bytes: bytes) -> tuple[bool, str | None]:
    """
    执行 UPDATE：SET 照片列 = :blob WHERE 人员键列 = :pn
    返回 (成功, 错误信息)。
    """
    cfg = get_oracle_sync_config()
    if not cfg or not cfg.enabled:
        return True, None

    try:
        import oracledb
    except ImportError:
        return False, '未安装 oracledb，请执行: pip install oracledb'

    try:
        tab = _ident(cfg.table_name)
        pkc = _ident(cfg.person_key_column)
        phc = _ident(cfg.photo_blob_column)
        schema = (cfg.table_schema or '').strip()
        if schema:
            schema = _ident(schema)
            fqtn = f'{schema}.{tab}'
        else:
            fqtn = tab

        try:
            plain_pw = decrypt_oracle_password_for_connection(cfg.password or '')
        except ValueError as e:
            return False, str(e)

        dsn = oracledb.makedsn(
            (cfg.host or '').strip(),
            int(cfg.port or 1521),
            service_name=(cfg.service_name or '').strip(),
        )
        conn = oracledb.connect(
            user=(cfg.username or '').strip(),
            password=plain_pw,
            dsn=dsn,
        )
        try:
            sql = f'UPDATE {fqtn} SET {phc} = :1 WHERE {pkc} = :2'
            with conn.cursor() as cur:
                cur.execute(sql, [photo_bytes, str(person_number).strip()])
                if cur.rowcount == 0:
                    conn.rollback()
                    return False, f'Oracle 未更新任何行（{pkc}={person_number!r} 可能不存在）'
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.exception('Oracle 照片同步失败 person_number=%s', person_number)
        return False, str(e)

    return True, None


def oracle_sync_template_context() -> dict:
    """供上传页、待确认页模板使用的 Oracle 同步 UI 开关。"""
    cfg = get_oracle_sync_config()
    if not cfg or not cfg.enabled:
        return {
            'oracle_sync_enabled': False,
            'oracle_sync_show_opt_in': False,
            'oracle_sync_auto': False,
            'oracle_sync_default_checked': False,
        }
    return {
        'oracle_sync_enabled': True,
        'oracle_sync_show_opt_in': bool(cfg.uploader_must_opt_in),
        'oracle_sync_auto': not cfg.uploader_must_opt_in,
        'oracle_sync_default_checked': bool(cfg.default_opt_in_checked),
    }


def upload_should_sync_to_oracle(request_data, post_data) -> bool:
    """根据配置与请求参数决定是否写入 Oracle。"""
    cfg = get_oracle_sync_config()
    if not cfg or not cfg.enabled:
        return False
    if cfg.uploader_must_opt_in:
        raw = None
        if request_data is not None:
            raw = request_data.get('sync_to_oracle')
        if raw is None and post_data is not None:
            raw = post_data.get('sync_to_oracle')
        if raw is None:
            return False
        if isinstance(raw, bool):
            return raw
        s = str(raw).strip().lower()
        return s in ('1', 'true', 'yes', 'on')
    return True
