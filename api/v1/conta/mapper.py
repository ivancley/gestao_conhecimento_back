from typing import List, Optional

from api.v1._database.models import Usuario
from api.v1._shared.schemas import UsuarioView, ContaView
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

class ContaMapper:
    """
    Mapper for Conta operations.
    
    This mapper converts Usuario models to ContaView schemas,
    ensuring sensitive fields like passwords are not exposed.
    """
    
    def map_to_conta_view(self, usuario: Usuario) -> Optional[ContaView]:
        """
        Map a Usuario model to a ContaView schema.
        
        Args:
            usuario: Usuario model instance
            
        Returns:
            ContaView schema without sensitive fields
        """
        if not usuario:
            return None
            
        return ContaView(
            id=usuario.id,
            nome=usuario.nome,
            email=usuario.email,
            flg_ativo=usuario.flg_ativo,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
            senha=usuario.senha
        )

# Create singleton instance
conta_mapper = ContaMapper()

# Export mapper function for backward compatibility
def map_to_conta_view(usuario: Usuario) -> Optional[ContaView]:
    """Map a Usuario model to a ContaView."""
    return conta_mapper.map_to_conta_view(usuario)