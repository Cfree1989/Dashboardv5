from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app import db


class CatalogStore(db.Model):
    """Stores the catalog configuration as a single JSON document with versioning."""
    
    __tablename__ = 'catalog_store'
    
    id = Column(String(50), primary_key=True)  # Always 'active' for the current catalog
    version = Column(Integer, nullable=False, default=1)
    data = Column(JSON, nullable=False)
    updated_by = Column(String(100), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<CatalogStore(id={self.id}, version={self.version})>'
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'version': self.version,
            'data': self.data,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
