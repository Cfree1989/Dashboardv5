from flask import Blueprint
from flask import jsonify, request
from app.utils.decorators import token_required
from app.utils.date_utils import DateUtils
from app.services.analytics_service import AnalyticsService
from app.services.interfaces.analytics_service_interface import DateRange, AnalyticsFilters

bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# Create service instance
analytics_service = AnalyticsService()


def _parse_date_range():
    """Parse date range from query parameters using DateUtils"""
    return DateUtils.parse_date_range()


@bp.route('/overview', methods=['GET'])
@token_required
def overview():
    # Parse date range and filters
    start, end = _parse_date_range()
    date_range = DateRange(start, end)
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    filters = AnalyticsFilters(printer=printer_filter, discipline=discipline_filter)
    
    # Use AnalyticsService to get overview metrics
    payload = analytics_service.get_overview_metrics(date_range, filters)
    
    return jsonify(payload), 200


@bp.route('/trends', methods=['GET'])
@token_required
def trends():
    # Parse date range and filters
    start, end = _parse_date_range()
    date_range = DateRange(start, end)
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    filters = AnalyticsFilters(printer=printer_filter, discipline=discipline_filter)
    
    # Use AnalyticsService to get trend data
    trend_data = analytics_service.get_trend_data(date_range, filters)
    
    # Map to expected response format (maintain API compatibility)
    payload = {
        'series': trend_data['submissions'], 
        'approvals': trend_data['approvals'], 
        'metric': 'submissions',
        'date_range': trend_data['date_range']
    }
    
    return jsonify(payload), 200


@bp.route('/resources', methods=['GET'])
@token_required
def resources():
    # Parse date range and filters
    start, end = _parse_date_range()
    date_range = DateRange(start, end)
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    filters = AnalyticsFilters(printer=printer_filter, discipline=discipline_filter)
    
    # Use AnalyticsService to get resource metrics
    payload = analytics_service.get_resource_metrics(date_range, filters)
    
    return jsonify(payload), 200


@bp.route('/financial', methods=['GET'])
@token_required
def financial():
    # Parse date range and filters
    start, end = _parse_date_range()
    date_range = DateRange(start, end)
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    filters = AnalyticsFilters(printer=printer_filter, discipline=discipline_filter)
    
    # Use AnalyticsService to get financial summary
    payload = analytics_service.get_financial_summary(date_range, filters)
    
    return jsonify(payload), 200

