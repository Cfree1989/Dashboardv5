from flask import Blueprint, request, jsonify
from app.utils.decorators import token_required
from app.models.staff import Staff
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
    return jsonify({'staff': [s.to_dict() for s in staff_list]})

@bp.route('', methods=['POST'])
@token_required
def add_staff():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'message': 'Name is required'}), 400
    if Staff.query.get(name):
        return jsonify({'message': 'Staff member with this name already exists'}), 409
    new_staff = Staff(name=name)
    db.session.add(new_staff)
    db.session.commit()
    return jsonify(new_staff.to_dict()), 201

@bp.route('/<string:name>', methods=['PATCH'])
@token_required
def update_staff(name):
    data = request.get_json() or {}
    if 'is_active' not in data:
        return jsonify({'message': 'is_active field is required'}), 400
    is_active = data.get('is_active')
    staff = Staff.query.get(name)
    if not staff:
        return jsonify({'message': 'Staff member not found'}), 404
    staff.is_active = bool(is_active)
    if not staff.is_active:
        staff.deactivated_at = datetime.utcnow()
    else:
        staff.deactivated_at = None
    db.session.commit()
    return jsonify(staff.to_dict())