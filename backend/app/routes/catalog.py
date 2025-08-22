from flask import Blueprint, jsonify, request, g
from app.business_logic.shared_services.catalog_service import CatalogService
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode
from app.schemas.catalog import CatalogUpdateRequest, CatalogData
from app.utils.decorators import token_required
from app import limiter
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('catalog', __name__, url_prefix='/api/v1/catalog')


@bp.route('', methods=['GET'])
@limiter.limit("60 per minute")
def get_catalog():
    """Get the current catalog configuration."""
    try:
        catalog_data = CatalogService.get_catalog_for_api()
        
        # Add cache headers for client-side caching
        response = jsonify(catalog_data)
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes
        response.headers['ETag'] = f'"{catalog_data["version"]}"'
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Error getting catalog: {str(e)}")
        return ResponseService.server_error(
            message='Failed to retrieve catalog',
            error_code=ErrorCode.DATABASE_ERROR.value,
            details={'operation': 'get_catalog'}
        )


@bp.route('', methods=['PUT'])
@token_required
@limiter.limit("10 per minute")
def update_catalog():
    """Update the catalog configuration (admin only)."""
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            return ResponseService.validation_error(
                message='No data provided',
                error_code=ErrorCode.MISSING_REQUIRED_FIELD.value
            )
        
        # Validate the request
        try:
            update_request = CatalogUpdateRequest.from_dict(request_data)
        except Exception as e:
            return ResponseService.validation_error(
                message=f'Invalid request data: {str(e)}',
                error_code=ErrorCode.INVALID_FORMAT.value
            )
        
        # Validate the catalog data
        try:
            validated_data = CatalogService.validate_catalog_data(update_request.data.to_dict())
        except ValueError as e:
            return ResponseService.validation_error(
                message=str(e),
                error_code=ErrorCode.INVALID_VALUE.value
            )
        
        # Get the current user
        updated_by = getattr(g, 'staff_name', 'unknown')
        
        # Update the catalog
        updated_catalog = CatalogService.update_catalog(validated_data, updated_by)
        
        # Return the updated catalog
        response_data = {
            'message': 'Catalog updated successfully',
            'version': updated_catalog.version,
            'updated_by': updated_catalog.updated_by,
            'updated_at': updated_catalog.updated_at.isoformat() if updated_catalog.updated_at else None
        }
        
        return ResponseService.success(response_data)
        
    except Exception as e:
        logger.error(f"Error updating catalog: {str(e)}")
        return ResponseService.server_error(
            message='Failed to update catalog',
            error_code=ErrorCode.DATABASE_ERROR.value,
            details={'operation': 'update_catalog'}
        )


@bp.route('/version', methods=['GET'])
@limiter.limit("60 per minute")
def get_catalog_version():
    """Get just the catalog version for lightweight polling."""
    try:
        catalog = CatalogService.get_catalog()
        if not catalog:
            catalog = CatalogService.seed_catalog_if_missing()
        
        response = jsonify({'version': catalog.version})
        response.headers['Cache-Control'] = 'public, max-age=60'  # 1 minute
        response.headers['ETag'] = f'"{catalog.version}"'
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Error getting catalog version: {str(e)}")
        return ResponseService.server_error(
            message='Failed to retrieve catalog version',
            error_code=ErrorCode.DATABASE_ERROR.value,
            details={'operation': 'get_catalog_version'}
        )
