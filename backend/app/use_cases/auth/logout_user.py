from ...domain.ports.token import RefreshTokenPort
from ...errors import AppError
from ...utils.security import hash_refresh_token


async def logout_user(token_port: RefreshTokenPort, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    try:
        stored_token = await token_port.get_by_hash(token_hash, for_update=True)
        if stored_token is None:
            return

        await token_port.revoke(stored_token.user_id)
        await token_port.commit()
    except AppError:
        await token_port.rollback()
        raise
    except Exception:
        await token_port.rollback()
        raise
