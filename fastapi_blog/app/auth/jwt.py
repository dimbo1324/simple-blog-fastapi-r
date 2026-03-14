"""
Работа с JWT-токенами через библиотеку PyJWT.

Структура payload (claims):
  sub  — subject, идентификатор пользователя (str, по стандарту RFC 7519)
  exp  — время истечения (datetime, PyJWT проверяет автоматически)

Почему sub — строка, а не int?
  JWT-стандарт определяет sub как StringOrURI. Мы храним int в БД,
  но в токене сериализуем как str и конвертируем обратно при чтении.
"""

from datetime import UTC, datetime, timedelta

import jwt

from config import settings


def create_access_token(user_id: int) -> str:

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
