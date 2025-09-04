from flask import Blueprint, request
from app.utils.decorators import token_required
from app.models.staff import Staff
from app.business_logic.shared_services.response_service import ResponseService
from app import db
from datetime import datetime

bp = Blueprint('staff', __name__, url_prefix='/api/v1/staff')

@bp.route('', methods=['GET'])
@token_required
def list_staff():
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    if include_inactive:
        staff_list = Staff.query.all()
    else:
        staff_list = Staff.query.filter_by(is_active=True).all()
    return ResponseService.success({'staff': [s.to_dict() for s in staff_list]})

@bp.route('', methods=['POST'])
@token_required
def add_staff():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return ResponseService.validation_error('Name is required')
    if Staff.query.get(name):
        return ResponseService.conflict('Staff member with this name already exists')
    new_staff = Staff(name=name)
    db.session.add(new_staff)
    db.session.commit()
    return ResponseService.success(new_staff.to_dict(), status=201)

@bp.route('/<string:name>', methods=['PATCH', 'PUT'])
@token_required
def update_staff(name):
    data = request.get_json() or {}
    if 'is_active' not in data:
        return ResponseService.validation_error('is_active field is required')
    is_active = data.get('is_active')
    staff = Staff.query.get(name)
    if not staff:
        return ResponseService.not_found('Staff member not found')
    staff.is_active = bool(is_active)
    if not staff.is_active:
        staff.deactivated_at = datetime.utcnow()
    else:
        staff.deactivated_at = None
    db.session.commit()
    return ResponseService.success(staff.to_dict())