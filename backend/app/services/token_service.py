from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app


def _serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY", "dev-secret-key")
    salt = current_app.config.get("CONFIRM_TOKEN_SALT", "confirm-token")
    return URLSafeTimedSerializer(secret_key, salt=salt)


def generate_confirmation_token(job_id: str) -> str:
    return _serializer().dumps({"job_id": job_id})


def verify_confirmation_token(token: str, max_age_seconds: int = 60 * 60 * 72) -> str:
    """Return job_id if valid, else raise ValueError."""
    try:
        data = _serializer().loads(token, max_age=max_age_seconds)
        job_id = data.get("job_id")
        if not job_id:
            raise ValueError("Invalid token payload")
        return job_id
    except SignatureExpired as e:
        raise ValueError("expired") from e
    except BadSignature as e:
        raise ValueError("invalid") from e


