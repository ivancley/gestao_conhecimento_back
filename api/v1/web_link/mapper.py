from typing import List, Optional

from api.v1._database.models import WebLink
from api.v1._shared.base_mapper import BaseMapper
from api.v1._shared.schemas import WebLinkView

class WebLinkMapper(BaseMapper[WebLink, WebLinkView]):
    """
    Mapper for WebLink entity.

    This class handles mapping between WebLink ORM models and WebLinkView Pydantic models.
    It inherits from BaseMapper which provides common mapping operations with caching.
    """

    def __init__(self):
        """Initialize the WebLinkMapper with its model class, view class, and relationship map."""
        # Define relationship map with forward declarations to avoid circular imports
        relationship_map = {
            'usuario': {
                'mapper': lambda model, include: self._get_usuario_mapper().map_to_view(model, include),
                'is_list': False,
                'model_class': 'usuario'  # String to avoid circular imports
            }
        }

        super().__init__(
            model_class=WebLink,
            view_class=WebLinkView,
            entity_name="WebLink",
            relationship_map=relationship_map,
            sensitive_fields=[]
        )
    
    def _get_usuario_mapper(self):
        """Get the consultaMapper instance (lazy loading to avoid circular imports)."""
        from api.v1.usuario.mapper import usuario_mapper
        return usuario_mapper
    

# Create a singleton instance
web_link_mapper = WebLinkMapper()

# Export the mapper functions to maintain backward compatibility
def map_to_web_link_view(
    model: WebLink,
    include: Optional[List[str]] = None,
    select_fields: Optional[str] = None,
) -> Optional[WebLinkView]:
    """Map a WebLink model to a WebLinkView."""
    return web_link_mapper.map_to_view(model, include, select_fields)

def map_list_to_web_link_view(
    models: List[WebLink],
    include: Optional[List[str]] = None,
    select_fields: Optional[str] = None,
) -> List[WebLinkView]:
    """Map a list of WebLink models to a list of WebLinkViews."""
    return web_link_mapper.map_list_to_view(models, include, select_fields)
