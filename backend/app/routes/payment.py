from flask import Blueprint

# Note: Payment routes are implemented in jobs blueprint under
# `/api/v1/jobs/<job_id>/payment`. This module exists to avoid
# breaking imports and to document the intended separation if we
# later move payment endpoints into their own blueprint.
bp = Blueprint('payment', __name__, url_prefix='/api/v1/payment')