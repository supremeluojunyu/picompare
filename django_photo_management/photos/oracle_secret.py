"""Oracle 同步配置中的密码：使用 Fernet 加密后落库，连接时再解密。"""
from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger('photos')

# 存库前缀，避免对已是密文的值重复加密
ENC_PREFIX = 'enc1$'


def derived_fernet_key_b64() -> str:
    """与未配置独立密钥时 _fernet() 使用的密钥材料一致（urlsafe base64 字符串）。"""
    from django.conf import settings

    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('ascii')


def _fernet() -> Fernet:
    from django.conf import settings

    raw = (getattr(settings, 'ORACLE_SYNC_FERNET_KEY', None) or '').strip()
    if raw:
        key = raw.encode('utf-8') if isinstance(raw, str) else raw
        return Fernet(key)
    from .models import SuperuserCryptoSettings

    row = SuperuserCryptoSettings.objects.filter(pk=1).first()
    db_key = (row.oracle_sync_fernet_key if row else '') or ''
    db_key = db_key.strip()
    if db_key:
        return Fernet(db_key.encode('utf-8'))
    return Fernet(derived_fernet_key_b64().encode('ascii'))


def encrypt_oracle_password_for_storage(plain: str) -> str:
    if not plain:
        return ''
    f = _fernet()
    token = f.encrypt(plain.encode('utf-8')).decode('ascii')
    return ENC_PREFIX + token


def decrypt_oracle_password_for_connection(stored: str) -> str:
    """
    返回用于 oracledb 连接的明文密码。
    无前缀时视为历史明文数据（兼容迁移前记录）。
    """
    if not stored:
        return ''
    s = stored
    if not s.startswith(ENC_PREFIX):
        return s
    token = s[len(ENC_PREFIX) :].encode('ascii')
    try:
        return _fernet().decrypt(token).decode('utf-8')
    except InvalidToken:
        logger.error('Oracle 同步密码解密失败（密钥与库中密文不匹配）')
        raise ValueError(
            'Oracle 密码无法解密：请确认环境变量 ORACLE_SYNC_FERNET_KEY、'
            '或「秘钥配置」页中保存的 Fernet 密钥未变更；必要时请在后台重新保存 Oracle 密码。'
        ) from None


def is_stored_password_encrypted(stored: str) -> bool:
    return bool(stored and stored.startswith(ENC_PREFIX))
