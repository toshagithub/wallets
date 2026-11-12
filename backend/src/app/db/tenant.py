from contextvars import ContextVar


_current_tenant_id: ContextVar[int | None] = ContextVar(
    "current_tenant_id",
    default=None,
)


def set_current_tenant(tenant_id: int) -> None:
    if tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    _current_tenant_id.set(tenant_id)


def get_current_tenant() -> int:
    tenant_id = _current_tenant_id.get()

    if tenant_id is None:
        raise RuntimeError("Tenant context is not set")

    return tenant_id
