"""按「人员编号 ↔ 管理组」控制照片可见范围（超级管理员不受限）。"""


def allowed_person_numbers(user):
    """
    返回当前用户允许操作的人员编号集合。
    None 表示不限制（超级管理员）；空集合表示未配置管理组或组内无人员。
    """
    if not user or not user.is_authenticated:
        return frozenset()
    if user.is_superuser:
        return None
    mg_id = getattr(user, 'photo_scope_group_id', None)
    if not mg_id:
        return frozenset()
    from .models import PersonIdGroupAssignment

    return frozenset(
        PersonIdGroupAssignment.objects.filter(management_group_id=mg_id).values_list(
            'person_number', flat=True
        )
    )


def person_number_allowed(user, person_number: str) -> bool:
    allowed = allowed_person_numbers(user)
    if allowed is None:
        return True
    return person_number in allowed
