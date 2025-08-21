from typing import Optional, Dict, Any, List, Tuple
from app import db
from app.models.catalog import CatalogStore
from app.schemas.catalog import CatalogData, CatalogUpdateRequest
from app.business_logic.shared_services.event_service import log_event
import json


class CatalogService:
    """Service for managing the catalog configuration."""
    
    @staticmethod
    def get_default_catalog() -> Dict[str, Any]:
        """Return the default catalog configuration."""
        return {
            "version": 1,
            "methods": ["Filament", "Resin"],
            "printers": [
                {
                    "id": "prusa-mk4s",
                    "name": "Prusa MK4S",
                    "supported_methods": ["Filament"],
                    "is_active": True
                },
                {
                    "id": "prusa-xl",
                    "name": "Prusa XL",
                    "supported_methods": ["Filament"],
                    "is_active": True
                },
                {
                    "id": "raise3d-pro2-plus",
                    "name": "Raise3D Pro 2 Plus",
                    "supported_methods": ["Filament"],
                    "is_active": True
                },
                {
                    "id": "formlabs-form3",
                    "name": "Formlabs Form 3",
                    "supported_methods": ["Resin"],
                    "is_active": True
                }
            ],
            "materials": [
                {
                    "id": "pla",
                    "method": "Filament",
                    "name": "PLA",
                    "unit_cost_per_g_cents": 10,
                    "colors": [
                        "True Red", "True Orange", "Light Orange", "True Yellow", "Dark Yellow",
                        "Lime Green", "Green", "Forest Green", "Blue", "Electric Blue",
                        "Midnight Purple", "Light Purple", "Clear", "True White", "Gray",
                        "True Black", "Brown", "Copper", "Bronze", "True Silver",
                        "True Gold", "Glow in the Dark", "Color Changing"
                    ],
                    "is_active": True
                },
                {
                    "id": "resin",
                    "method": "Resin",
                    "name": "Resin",
                    "unit_cost_per_g_cents": 20,
                    "colors": ["Black", "White", "Gray", "Clear"],
                    "is_active": True
                }
            ]
        }
    
    @staticmethod
    def get_catalog() -> Optional[CatalogStore]:
        """Get the current catalog from the database."""
        return CatalogStore.query.filter_by(id='active').first()
    
    @staticmethod
    def seed_catalog_if_missing() -> CatalogStore:
        """Seed the default catalog if it doesn't exist."""
        catalog = CatalogService.get_catalog()
        if not catalog:
            default_data = CatalogService.get_default_catalog()
            catalog = CatalogStore(
                id='active',
                version=1,
                data=default_data,
                updated_by='system'
            )
            db.session.add(catalog)
            db.session.commit()
            
            # Log the seeding event
            try:
                log_event(
                    'CatalogSeeded',
                    {'description': 'Default catalog configuration seeded'},
                    triggered_by='system'
                )
            except Exception:
                # Don't fail if event logging fails
                pass
                
        return catalog
    
    @staticmethod
    def update_catalog(catalog_data: CatalogData, updated_by: str) -> CatalogStore:
        """Update the catalog with new data."""
        catalog = CatalogService.get_catalog()
        if not catalog:
            catalog = CatalogService.seed_catalog_if_missing()
        
        # Increment version
        new_version = catalog.version + 1
        catalog_data.version = new_version
        
        # Update the catalog
        catalog.version = new_version
        catalog.data = catalog_data.to_dict()
        catalog.updated_by = updated_by
        
        db.session.commit()
        
        # Log the update event
        try:
            log_event(
                'CatalogUpdated',
                {'description': f'Catalog updated to version {new_version} by {updated_by}'},
                triggered_by=updated_by
            )
        except Exception:
            # Don't fail if event logging fails
            pass
        
        return catalog
    
    @staticmethod
    def validate_catalog_data(data: Dict[str, Any]) -> CatalogData:
        """Validate catalog data against the schema."""
        try:
            catalog_data = CatalogData.from_dict(data)
            catalog_data.validate()
            return catalog_data
        except Exception as e:
            raise ValueError(f"Invalid catalog data: {str(e)}")
    
    @staticmethod
    def get_catalog_for_api() -> Dict[str, Any]:
        """Get catalog data formatted for API responses."""
        catalog = CatalogService.get_catalog()
        if not catalog:
            catalog = CatalogService.seed_catalog_if_missing()
        
        return {
            'version': catalog.version,
            'data': catalog.data,
            'updated_by': catalog.updated_by,
            'updated_at': catalog.updated_at.isoformat() if catalog.updated_at else None
        }

    @staticmethod
    def validate_job_configuration(method: str, material: str, color: str, printer: str) -> Tuple[bool, List[str]]:
        """
        Validate that a job's method/material/color/printer combination is valid according to the current catalog.
        
        Args:
            method: The print method (e.g., "Filament", "Resin")
            material: The material name (e.g., "PLA", "ABS", "Standard Resin")
            color: The color name (e.g., "Black", "White")
            printer: The printer name (e.g., "Prusa MK4S", "Formlabs Form 3")
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Get the current catalog
        catalog = CatalogService.get_catalog()
        if not catalog:
            # If no catalog exists, seed it and continue validation
            catalog = CatalogService.seed_catalog_if_missing()
        
        catalog_data = catalog.data
        
        # Normalize inputs for case-insensitive comparison
        method_lower = method.strip().lower() if method else ""
        material_lower = material.strip().lower() if material else ""
        color_lower = color.strip().lower() if color else ""
        printer_lower = printer.strip().lower() if printer else ""
        
        # Validate method exists
        methods = [m.lower() for m in catalog_data.get('methods', [])]
        if method_lower and method_lower not in methods:
            errors.append(f"Invalid print method: '{method}'. Valid methods: {', '.join(catalog_data.get('methods', []))}")
        
        # Validate material exists and matches method
        materials = catalog_data.get('materials', [])
        material_found = False
        material_method = None
        material_colors = []
        
        for mat in materials:
            if mat.get('is_active', True):  # Only check active materials
                mat_name_lower = mat.get('name', '').strip().lower()
                mat_method_lower = mat.get('method', '').strip().lower()
                
                if mat_name_lower == material_lower:
                    material_found = True
                    material_method = mat.get('method', '')
                    material_colors = [c.strip().lower() for c in mat.get('colors', [])]
                    break
        
        if material_lower and not material_found:
            valid_materials = [mat.get('name') for mat in materials if mat.get('is_active', True)]
            errors.append(f"Invalid material: '{material}'. Valid materials: {', '.join(valid_materials)}")
        
        # Validate material matches method
        if material_found and method_lower and material_method.lower() != method_lower:
            errors.append(f"Material '{material}' is not compatible with method '{method}'. Material '{material}' is for '{material_method}' method.")
        
        # Validate color exists for the material
        if material_found and color_lower and color_lower not in material_colors:
            valid_colors = [c for c in material_colors]
            errors.append(f"Invalid color '{color}' for material '{material}'. Valid colors: {', '.join(valid_colors)}")
        
        # Validate printer exists and supports the method
        printers = catalog_data.get('printers', [])
        printer_found = False
        printer_methods = []
        
        for prt in printers:
            if prt.get('is_active', True):  # Only check active printers
                prt_name_lower = prt.get('name', '').strip().lower()
                
                if prt_name_lower == printer_lower:
                    printer_found = True
                    printer_methods = [m.strip().lower() for m in prt.get('supported_methods', [])]
                    break
        
        if printer_lower and not printer_found:
            valid_printers = [prt.get('name') for prt in printers if prt.get('is_active', True)]
            errors.append(f"Invalid printer: '{printer}'. Valid printers: {', '.join(valid_printers)}")
        
        # Validate printer supports the method
        if printer_found and method_lower and method_lower not in printer_methods:
            errors.append(f"Printer '{printer}' does not support method '{method}'. Supported methods: {', '.join(printer_methods)}")
        
        return len(errors) == 0, errors
