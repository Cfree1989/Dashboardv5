import pytest
import json
from unittest.mock import patch, MagicMock
from app.services.catalog_service import CatalogService
from app.schemas.catalog import CatalogData, Material, Printer, PrintMethod, CatalogUpdateRequest
from app.models.catalog import CatalogStore


class TestCatalogSchemaValidation:
    """Test catalog schema validation and data structures."""
    
    def test_valid_printer_creation(self):
        """Test creating a valid printer."""
        printer = Printer(
            id="test-printer",
            name="Test Printer",
            supported_methods=[PrintMethod.FILAMENT],
            is_active=True
        )
        printer.validate()
        assert printer.id == "test-printer"
        assert printer.name == "Test Printer"
        assert printer.supported_methods == [PrintMethod.FILAMENT]
        assert printer.is_active is True
    
    def test_invalid_printer_empty_id(self):
        """Test printer validation fails with empty ID."""
        printer = Printer(id="", name="Test Printer", supported_methods=[PrintMethod.FILAMENT])
        with pytest.raises(ValueError, match="Printer ID cannot be empty"):
            printer.validate()
    
    def test_invalid_printer_empty_name(self):
        """Test printer validation fails with empty name."""
        printer = Printer(id="test", name="", supported_methods=[PrintMethod.FILAMENT])
        with pytest.raises(ValueError, match="Printer name cannot be empty"):
            printer.validate()
    
    def test_invalid_printer_no_methods(self):
        """Test printer validation fails with no supported methods."""
        printer = Printer(id="test", name="Test Printer", supported_methods=[])
        with pytest.raises(ValueError, match="Printer must support at least one method"):
            printer.validate()
    
    def test_valid_material_creation(self):
        """Test creating a valid material."""
        material = Material(
            id="test-material",
            method=PrintMethod.FILAMENT,
            name="Test Material",
            unit_cost_per_g_cents=10,
            colors=["Black", "White"],
            is_active=True
        )
        material.validate()
        assert material.id == "test-material"
        assert material.method == PrintMethod.FILAMENT
        assert material.name == "Test Material"
        assert material.unit_cost_per_g_cents == 10
        assert material.colors == ["Black", "White"]
        assert material.is_active is True
    
    def test_invalid_material_empty_id(self):
        """Test material validation fails with empty ID."""
        material = Material(
            id="",
            method=PrintMethod.FILAMENT,
            name="Test Material",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        with pytest.raises(ValueError, match="Material ID cannot be empty"):
            material.validate()
    
    def test_invalid_material_empty_name(self):
        """Test material validation fails with empty name."""
        material = Material(
            id="test",
            method=PrintMethod.FILAMENT,
            name="",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        with pytest.raises(ValueError, match="Material name cannot be empty"):
            material.validate()
    
    def test_invalid_material_negative_cost(self):
        """Test material validation fails with negative cost."""
        material = Material(
            id="test",
            method=PrintMethod.FILAMENT,
            name="Test Material",
            unit_cost_per_g_cents=-5,
            colors=["Black"]
        )
        with pytest.raises(ValueError, match="Material cost cannot be negative"):
            material.validate()
    
    def test_invalid_material_no_colors(self):
        """Test material validation fails with no colors."""
        material = Material(
            id="test",
            method=PrintMethod.FILAMENT,
            name="Test Material",
            unit_cost_per_g_cents=10,
            colors=[]
        )
        with pytest.raises(ValueError, match="Material must have at least one color"):
            material.validate()
    
    def test_material_strips_whitespace_from_colors(self):
        """Test material strips whitespace from color names."""
        material = Material(
            id="test",
            method=PrintMethod.FILAMENT,
            name="Test Material",
            unit_cost_per_g_cents=10,
            colors=["  Black  ", "  White  ", ""]  # Empty color should be filtered out
        )
        assert material.colors == ["Black", "White"]
    
    def test_valid_catalog_creation(self):
        """Test creating a valid catalog."""
        printer = Printer(id="printer1", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        material = Material(
            id="material1",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        
        catalog = CatalogData(
            version=1,
            methods=[PrintMethod.FILAMENT],
            printers=[printer],
            materials=[material]
        )
        catalog.validate()
        assert catalog.version == 1
        assert catalog.methods == [PrintMethod.FILAMENT]
        assert len(catalog.printers) == 1
        assert len(catalog.materials) == 1
    
    def test_invalid_catalog_version(self):
        """Test catalog validation fails with invalid version."""
        printer = Printer(id="printer1", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        material = Material(
            id="material1",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        
        catalog = CatalogData(
            version=0,  # Invalid version
            methods=[PrintMethod.FILAMENT],
            printers=[printer],
            materials=[material]
        )
        with pytest.raises(ValueError, match="Catalog version must be at least 1"):
            catalog.validate()
    
    def test_invalid_catalog_no_methods(self):
        """Test catalog validation fails with no methods."""
        printer = Printer(id="printer1", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        material = Material(
            id="material1",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        
        catalog = CatalogData(
            version=1,
            methods=[],  # No methods
            printers=[printer],
            materials=[material]
        )
        with pytest.raises(ValueError, match="At least one printing method must be defined"):
            catalog.validate()
    
    def test_invalid_catalog_duplicate_printer_ids(self):
        """Test catalog validation fails with duplicate printer IDs."""
        printer1 = Printer(id="same-id", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        printer2 = Printer(id="same-id", name="Printer 2", supported_methods=[PrintMethod.FILAMENT])
        material = Material(
            id="material1",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        
        catalog = CatalogData(
            version=1,
            methods=[PrintMethod.FILAMENT],
            printers=[printer1, printer2],  # Duplicate IDs
            materials=[material]
        )
        with pytest.raises(ValueError, match="Printer IDs must be unique"):
            catalog.validate()
    
    def test_invalid_catalog_duplicate_material_ids(self):
        """Test catalog validation fails with duplicate material IDs."""
        printer = Printer(id="printer1", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        material1 = Material(
            id="same-id",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        material2 = Material(
            id="same-id",
            method=PrintMethod.FILAMENT,
            name="Material 2",
            unit_cost_per_g_cents=15,
            colors=["White"]
        )
        
        catalog = CatalogData(
            version=1,
            methods=[PrintMethod.FILAMENT],
            printers=[printer],
            materials=[material1, material2]  # Duplicate IDs
        )
        with pytest.raises(ValueError, match="Material IDs must be unique"):
            catalog.validate()
    
    def test_catalog_removes_duplicate_methods(self):
        """Test catalog removes duplicate methods."""
        printer = Printer(id="printer1", name="Printer 1", supported_methods=[PrintMethod.FILAMENT])
        material = Material(
            id="material1",
            method=PrintMethod.FILAMENT,
            name="Material 1",
            unit_cost_per_g_cents=10,
            colors=["Black"]
        )
        
        catalog = CatalogData(
            version=1,
            methods=[PrintMethod.FILAMENT, PrintMethod.FILAMENT, PrintMethod.RESIN],  # Duplicates
            printers=[printer],
            materials=[material]
        )
        assert set(catalog.methods) == {PrintMethod.FILAMENT, PrintMethod.RESIN}


class TestCatalogService:
    """Test catalog service methods."""
    
    def test_get_default_catalog(self):
        """Test getting the default catalog configuration."""
        default_catalog = CatalogService.get_default_catalog()
        
        assert default_catalog['version'] == 1
        assert 'Filament' in default_catalog['methods']
        assert 'Resin' in default_catalog['methods']
        assert len(default_catalog['printers']) > 0
        assert len(default_catalog['materials']) > 0
        
        # Check specific default values
        printer_names = [p['name'] for p in default_catalog['printers']]
        assert 'Prusa MK3S' in printer_names
        assert 'Formlabs Form 3' in printer_names
        
        material_names = [m['name'] for m in default_catalog['materials']]
        assert 'PLA' in material_names
        assert 'ABS' in material_names
        assert 'Standard Resin' in material_names
    
    @patch('app.services.catalog_service.CatalogStore')
    def test_get_catalog_existing(self, mock_catalog_store):
        """Test getting existing catalog from database."""
        mock_catalog = MagicMock()
        mock_catalog_store.query.filter_by.return_value.first.return_value = mock_catalog
        
        result = CatalogService.get_catalog()
        assert result == mock_catalog
        mock_catalog_store.query.filter_by.assert_called_once_with(id='active')
    
    @patch('app.services.catalog_service.CatalogStore')
    def test_get_catalog_nonexistent(self, mock_catalog_store):
        """Test getting catalog when none exists."""
        mock_catalog_store.query.filter_by.return_value.first.return_value = None
        
        result = CatalogService.get_catalog()
        assert result is None
    
    @patch('app.services.catalog_service.log_event')
    @patch('app.services.catalog_service.db')
    @patch('app.services.catalog_service.CatalogStore')
    def test_seed_catalog_if_missing_new(self, mock_catalog_store, mock_db, mock_log_event):
        """Test seeding catalog when none exists."""
        # Mock no existing catalog
        mock_catalog_store.query.filter_by.return_value.first.return_value = None
        
        # Mock the new catalog instance
        mock_new_catalog = MagicMock()
        mock_catalog_store.return_value = mock_new_catalog
        
        result = CatalogService.seed_catalog_if_missing()
        
        # Verify catalog was created
        mock_catalog_store.assert_called_once()
        mock_db.session.add.assert_called_once_with(mock_new_catalog)
        mock_db.session.commit.assert_called_once()
        mock_log_event.assert_called_once()
        
        assert result == mock_new_catalog
    
    @patch('app.services.catalog_service.CatalogStore')
    def test_seed_catalog_if_missing_existing(self, mock_catalog_store):
        """Test seeding catalog when one already exists."""
        # Mock existing catalog
        mock_existing_catalog = MagicMock()
        mock_catalog_store.query.filter_by.return_value.first.return_value = mock_existing_catalog
        
        result = CatalogService.seed_catalog_if_missing()
        
        # Verify no new catalog was created
        mock_catalog_store.assert_not_called()
        assert result == mock_existing_catalog
    
    def test_validate_catalog_data_valid(self):
        """Test validating valid catalog data."""
        valid_data = {
            'version': 1,
            'methods': ['Filament', 'Resin'],
            'printers': [
                {
                    'id': 'printer1',
                    'name': 'Printer 1',
                    'supported_methods': ['Filament'],
                    'is_active': True
                }
            ],
            'materials': [
                {
                    'id': 'material1',
                    'method': 'Filament',
                    'name': 'Material 1',
                    'unit_cost_per_g_cents': 10,
                    'colors': ['Black'],
                    'is_active': True
                }
            ]
        }
        
        result = CatalogService.validate_catalog_data(valid_data)
        assert isinstance(result, CatalogData)
        assert result.version == 1
    
    def test_validate_catalog_data_invalid(self):
        """Test validating invalid catalog data."""
        invalid_data = {
            'version': 0,  # Invalid version
            'methods': ['Filament'],
            'printers': [],
            'materials': []
        }
        
        with pytest.raises(ValueError, match="Invalid catalog data"):
            CatalogService.validate_catalog_data(invalid_data)


class TestJobConfigurationValidation:
    """Test job configuration validation against catalog."""
    
    def setup_method(self):
        """Set up test catalog data."""
        self.test_catalog_data = {
            'version': 1,
            'methods': ['Filament', 'Resin'],
            'printers': [
                {
                    'id': 'prusa-mk3s',
                    'name': 'Prusa MK3S',
                    'supported_methods': ['Filament'],
                    'is_active': True
                },
                {
                    'id': 'form3',
                    'name': 'Formlabs Form 3',
                    'supported_methods': ['Resin'],
                    'is_active': True
                },
                {
                    'id': 'inactive-printer',
                    'name': 'Inactive Printer',
                    'supported_methods': ['Filament'],
                    'is_active': False
                }
            ],
            'materials': [
                {
                    'id': 'pla',
                    'method': 'Filament',
                    'name': 'PLA',
                    'unit_cost_per_g_cents': 10,
                    'colors': ['Black', 'White', 'Orange'],
                    'is_active': True
                },
                {
                    'id': 'abs',
                    'method': 'Filament',
                    'name': 'ABS',
                    'unit_cost_per_g_cents': 10,
                    'colors': ['Black', 'Grey'],
                    'is_active': True
                },
                {
                    'id': 'resin-standard',
                    'method': 'Resin',
                    'name': 'Standard Resin',
                    'unit_cost_per_g_cents': 20,
                    'colors': ['Grey', 'Clear'],
                    'is_active': True
                },
                {
                    'id': 'inactive-material',
                    'method': 'Filament',
                    'name': 'Inactive Material',
                    'unit_cost_per_g_cents': 10,
                    'colors': ['Red'],
                    'is_active': False
                }
            ]
        }
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_valid_job_configuration(self, mock_get_catalog):
        """Test valid job configuration passes validation."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='PLA',
            color='Black',
            printer='Prusa MK3S'
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_invalid_method(self, mock_get_catalog):
        """Test validation fails with invalid method."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='InvalidMethod',
            material='PLA',
            color='Black',
            printer='Prusa MK3S'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid print method" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_invalid_material(self, mock_get_catalog):
        """Test validation fails with invalid material."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='InvalidMaterial',
            color='Black',
            printer='Prusa MK3S'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid material" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_material_method_mismatch(self, mock_get_catalog):
        """Test validation fails when material doesn't match method."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Resin',
            material='PLA',  # PLA is for Filament, not Resin
            color='Grey',
            printer='Formlabs Form 3'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "not compatible with method" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_invalid_color_for_material(self, mock_get_catalog):
        """Test validation fails with invalid color for material."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='PLA',
            color='Purple',  # Purple not available for PLA
            printer='Prusa MK3S'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid color" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_invalid_printer(self, mock_get_catalog):
        """Test validation fails with invalid printer."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='PLA',
            color='Black',
            printer='InvalidPrinter'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid printer" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_printer_method_mismatch(self, mock_get_catalog):
        """Test validation fails when printer doesn't support method."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Resin',
            material='Standard Resin',
            color='Grey',
            printer='Prusa MK3S'  # Prusa MK3S only supports Filament
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "does not support method" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_inactive_material_ignored(self, mock_get_catalog):
        """Test inactive materials are not considered valid."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='Inactive Material',  # This material is inactive
            color='Red',
            printer='Prusa MK3S'
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid material" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_inactive_printer_ignored(self, mock_get_catalog):
        """Test inactive printers are not considered valid."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='PLA',
            color='Black',
            printer='Inactive Printer'  # This printer is inactive
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "Invalid printer" in errors[0]
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_case_insensitive_validation(self, mock_get_catalog):
        """Test validation is case insensitive."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='filament',  # lowercase
            material='pla',     # lowercase
            color='black',      # lowercase
            printer='prusa mk3s'  # lowercase
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_whitespace_handling(self, mock_get_catalog):
        """Test validation handles whitespace properly."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='  Filament  ',  # with whitespace
            material='  PLA  ',      # with whitespace
            color='  Black  ',       # with whitespace
            printer='  Prusa MK3S  '  # with whitespace
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_multiple_validation_errors(self, mock_get_catalog):
        """Test multiple validation errors are reported."""
        mock_catalog = MagicMock()
        mock_catalog.data = self.test_catalog_data
        mock_get_catalog.return_value = mock_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='InvalidMethod',
            material='InvalidMaterial',
            color='InvalidColor',
            printer='InvalidPrinter'
        )
        
        assert is_valid is False
        assert len(errors) == 4
        assert any("Invalid print method" in error for error in errors)
        assert any("Invalid material" in error for error in errors)
        assert any("Invalid printer" in error for error in errors)
    
    @patch('app.services.catalog_service.CatalogService.seed_catalog_if_missing')
    @patch('app.services.catalog_service.CatalogService.get_catalog')
    def test_catalog_seeding_on_missing(self, mock_get_catalog, mock_seed_catalog):
        """Test catalog is seeded when missing."""
        # Mock no existing catalog
        mock_get_catalog.return_value = None
        
        # Mock seeded catalog
        mock_seeded_catalog = MagicMock()
        mock_seeded_catalog.data = self.test_catalog_data
        mock_seed_catalog.return_value = mock_seeded_catalog
        
        is_valid, errors = CatalogService.validate_job_configuration(
            method='Filament',
            material='PLA',
            color='Black',
            printer='Prusa MK3S'
        )
        
        mock_seed_catalog.assert_called_once()
        assert is_valid is True
        assert len(errors) == 0


class TestCatalogAPIEndpoints:
    """Test catalog API endpoints."""
    
    def test_get_catalog_success(self, client):
        """Test successful GET /api/v1/catalog."""
        response = client.get('/api/v1/catalog')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'version' in data
        assert 'data' in data
        assert 'updated_by' in data
        assert 'updated_at' in data
        
        # Check cache headers
        assert 'Cache-Control' in response.headers
        assert 'ETag' in response.headers
    
    def test_get_catalog_version_success(self, client):
        """Test successful GET /api/v1/catalog/version."""
        response = client.get('/api/v1/catalog/version')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'version' in data
        assert isinstance(data['version'], int)
        
        # Check cache headers
        assert 'Cache-Control' in response.headers
        assert 'ETag' in response.headers
    
    def test_update_catalog_no_auth(self, client):
        """Test PUT /api/v1/catalog without authentication."""
        response = client.put('/api/v1/catalog', json={'data': {}})
        
        assert response.status_code == 401  # Unauthorized
    
    def test_update_catalog_no_data(self, client, auth_headers):
        """Test PUT /api/v1/catalog with no data."""
        response = client.put('/api/v1/catalog', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No data provided' in data['error']
    
    def test_update_catalog_invalid_data(self, client, auth_headers):
        """Test PUT /api/v1/catalog with invalid data."""
        invalid_data = {
            'data': {
                'version': 0,  # Invalid version
                'methods': [],
                'printers': [],
                'materials': []
            }
        }
        
        response = client.put('/api/v1/catalog', json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_update_catalog_valid_data(self, client, auth_headers):
        """Test PUT /api/v1/catalog with valid data."""
        valid_data = {
            'data': {
                'version': 1,
                'methods': ['Filament', 'Resin'],
                'printers': [
                    {
                        'id': 'test-printer',
                        'name': 'Test Printer',
                        'supported_methods': ['Filament'],
                        'is_active': True
                    }
                ],
                'materials': [
                    {
                        'id': 'test-material',
                        'method': 'Filament',
                        'name': 'Test Material',
                        'unit_cost_per_g_cents': 10,
                        'colors': ['Black'],
                        'is_active': True
                    }
                ]
            }
        }
        
        response = client.put('/api/v1/catalog', json=valid_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'version' in data
        assert 'updated_by' in data
        assert 'updated_at' in data
        assert data['message'] == 'Catalog updated successfully'


class TestCatalogIntegration:
    """Test catalog integration with job submission and approval."""
    
    def test_job_submission_with_catalog_validation(self, client, auth_headers):
        """Test job submission validates against catalog."""
        # First, update catalog to have specific materials/printers
        catalog_data = {
            'data': {
                'version': 1,
                'methods': ['Filament', 'Resin'],
                'printers': [
                    {
                        'id': 'prusa-mk3s',
                        'name': 'Prusa MK3S',
                        'supported_methods': ['Filament'],
                        'is_active': True
                    }
                ],
                'materials': [
                    {
                        'id': 'pla',
                        'method': 'Filament',
                        'name': 'PLA',
                        'unit_cost_per_g_cents': 10,
                        'colors': ['Black', 'White'],
                        'is_active': True
                    }
                ]
            }
        }
        
        # Update catalog
        response = client.put('/api/v1/catalog', json=catalog_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Try to submit job with invalid material (not in catalog)
        job_data = {
            'student_name': 'Test Student',
            'student_email': 'test@example.com',
            'discipline': 'Engineering',
            'class_name': 'Test Class',
            'method': 'Filament',
            'material': 'InvalidMaterial',  # Not in catalog
            'color': 'Black',
            'printer': 'Prusa MK3S',
            'weight_grams': 50,
            'notes': 'Test job'
        }
        
        response = client.post('/api/v1/submit', json=job_data)
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid material' in data['error']
    
    def test_job_approval_with_catalog_validation(self, client, auth_headers):
        """Test job approval validates printer against catalog."""
        # Create a job first
        job_data = {
            'student_name': 'Test Student',
            'student_email': 'test@example.com',
            'discipline': 'Engineering',
            'class_name': 'Test Class',
            'method': 'Filament',
            'material': 'PLA',
            'color': 'Black',
            'printer': 'Prusa MK3S',
            'weight_grams': 50,
            'notes': 'Test job'
        }
        
        response = client.post('/api/v1/submit', json=job_data)
        assert response.status_code == 201
        job_id = response.get_json()['job']['id']
        
        # Update catalog to have specific printers
        catalog_data = {
            'data': {
                'version': 1,
                'methods': ['Filament', 'Resin'],
                'printers': [
                    {
                        'id': 'prusa-mk3s',
                        'name': 'Prusa MK3S',
                        'supported_methods': ['Filament'],
                        'is_active': True
                    }
                ],
                'materials': [
                    {
                        'id': 'pla',
                        'method': 'Filament',
                        'name': 'PLA',
                        'unit_cost_per_g_cents': 10,
                        'colors': ['Black'],
                        'is_active': True
                    }
                ]
            }
        }
        
        response = client.put('/api/v1/catalog', json=catalog_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Try to approve with invalid printer
        approval_data = {
            'printer': 'InvalidPrinter',  # Not in catalog
            'cost_usd': 5.00,
            'notes': 'Approved'
        }
        
        response = client.post(f'/api/v1/jobs/{job_id}/approve', json=approval_data, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid printer' in data['error']
