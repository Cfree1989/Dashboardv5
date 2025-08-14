from typing import List, Optional, Dict, Any
from enum import Enum


class PrintMethod(str, Enum):
    FILAMENT = "Filament"
    RESIN = "Resin"


class Printer:
    def __init__(self, id: str, name: str, supported_methods: List[PrintMethod], is_active: bool = True):
        self.id = id.strip() if id else ""
        self.name = name.strip() if name else ""
        self.supported_methods = supported_methods
        self.is_active = is_active
    
    def validate(self):
        if not self.id:
            raise ValueError('Printer ID cannot be empty')
        if not self.name:
            raise ValueError('Printer name cannot be empty')
        if not self.supported_methods:
            raise ValueError('Printer must support at least one method')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'supported_methods': [m.value for m in self.supported_methods],
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Printer':
        supported_methods = [PrintMethod(m) for m in data.get('supported_methods', [])]
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            supported_methods=supported_methods,
            is_active=data.get('is_active', True)
        )


class Material:
    def __init__(self, id: str, method: PrintMethod, name: str, unit_cost_per_g_cents: int, 
                 colors: List[str], is_active: bool = True):
        self.id = id.strip() if id else ""
        self.method = method
        self.name = name.strip() if name else ""
        self.unit_cost_per_g_cents = unit_cost_per_g_cents
        self.colors = [color.strip() for color in colors if color.strip()]
        self.is_active = is_active
    
    def validate(self):
        if not self.id:
            raise ValueError('Material ID cannot be empty')
        if not self.name:
            raise ValueError('Material name cannot be empty')
        if self.unit_cost_per_g_cents < 0:
            raise ValueError('Material cost cannot be negative')
        if not self.colors:
            raise ValueError('Material must have at least one color')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'method': self.method.value,
            'name': self.name,
            'unit_cost_per_g_cents': self.unit_cost_per_g_cents,
            'colors': self.colors,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        return cls(
            id=data.get('id', ''),
            method=PrintMethod(data.get('method', 'Filament')),
            name=data.get('name', ''),
            unit_cost_per_g_cents=data.get('unit_cost_per_g_cents', 0),
            colors=data.get('colors', []),
            is_active=data.get('is_active', True)
        )


class CatalogData:
    def __init__(self, version: int, methods: List[PrintMethod], printers: List[Printer], materials: List[Material]):
        self.version = version
        self.methods = list(set(methods))  # Remove duplicates
        self.printers = printers
        self.materials = materials
    
    def validate(self):
        if self.version < 1:
            raise ValueError('Catalog version must be at least 1')
        if not self.methods:
            raise ValueError('At least one printing method must be defined')
        if not self.printers:
            raise ValueError('At least one printer must be defined')
        if not self.materials:
            raise ValueError('At least one material must be defined')
        
        # Check for duplicate IDs
        printer_ids = [p.id for p in self.printers]
        if len(printer_ids) != len(set(printer_ids)):
            raise ValueError('Printer IDs must be unique')
        
        material_ids = [m.id for m in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError('Material IDs must be unique')
        
        # Validate individual items
        for printer in self.printers:
            printer.validate()
        for material in self.materials:
            material.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'methods': [m.value for m in self.methods],
            'printers': [p.to_dict() for p in self.printers],
            'materials': [m.to_dict() for m in self.materials]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CatalogData':
        methods = [PrintMethod(m) for m in data.get('methods', [])]
        printers = [Printer.from_dict(p) for p in data.get('printers', [])]
        materials = [Material.from_dict(m) for m in data.get('materials', [])]
        
        return cls(
            version=data.get('version', 1),
            methods=methods,
            printers=printers,
            materials=materials
        )


class CatalogResponse:
    def __init__(self, version: int, data: CatalogData, updated_by: str, updated_at: Optional[str] = None):
        self.version = version
        self.data = data
        self.updated_by = updated_by
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'data': self.data.to_dict(),
            'updated_by': self.updated_by,
            'updated_at': self.updated_at
        }


class CatalogUpdateRequest:
    def __init__(self, data: CatalogData):
        self.data = data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CatalogUpdateRequest':
        catalog_data = CatalogData.from_dict(data.get('data', {}))
        return cls(data=catalog_data)
