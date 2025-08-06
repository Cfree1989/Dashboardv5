from flask import Blueprint
from flask import jsonify
from app.models.event import Event
from app.utils.decorators import token_required

bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# TODO: Implement analytics routes

@bp.route('/events', methods=['GET'])
@token_required
def list_events():
    events = Event.query.all()
    return jsonify([e.to_dict() for e in events]), 200 