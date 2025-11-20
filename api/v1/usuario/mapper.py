from typing import List, Optional, Dict, Any, Type
from uuid import UUID

from api.v1._database.models import Usuario
from api.v1._shared.schemas import UsuarioView
from api.v1._shared.base_mapper import BaseMapper

class UsuarioMapper(BaseMapper[Usuario, UsuarioView]):
    """
    Mapper for Usuario entity.

    This class handles mapping between Usuario ORM models and UsuarioView Pydantic models.
    It inherits from BaseMapper which provides common mapping operations with caching.
    """

    def __init__(self):
        """Initialize the UsuarioMapper with its model class, view class, and relationship map."""
        # Define relationship map with forward declarations to avoid circular imports
        relationship_map = {
            'web_links': {
                'mapper': lambda model, include: self._get_web_link_mapper().map_to_view(model, include),
                'is_list': True,
                'model_class': 'web_links'  # String to avoid circular imports
            }
        }

        super().__init__(
            model_class=Usuario,
            view_class=UsuarioView,
            entity_name="Usuario",
            relationship_map=relationship_map,
            sensitive_fields=['senha']
        )
    

# Create a singleton instance
usuario_mapper = UsuarioMapper()

# Export the mapper functions to maintain backward compatibility
def map_to_usuario_view(
    model: Usuario,
    include: Optional[List[str]] = None,
    select_fields: Optional[str] = None,
) -> Optional[UsuarioView]:
    """Map a Usuario model to a UsuarioView."""
    return usuario_mapper.map_to_view(model, include, select_fields)

def map_list_to_usuario_view(
    models: List[Usuario],
    include: Optional[List[str]] = None,
    select_fields: Optional[str] = None,
) -> List[UsuarioView]:
    """Map a list of Usuario models to a list of UsuarioViews."""
    return usuario_mapper.map_list_to_view(models, include, select_fields)