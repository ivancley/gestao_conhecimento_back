from typing import Optional
from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.v1._database.models import WebLink
from api.v1._shared.base_service import BaseService
from api.v1._shared.schemas import WebLinkCreate, WebLinkGeneric, WebLinkUpdate

logger = logging.getLogger(__name__)


# Mapeamento de nomes de relacionamento
RELATIONSHIP_MAP = {
    "usuario": WebLink.usuario,
}

class WebLinkService(BaseService[WebLink, WebLinkCreate, WebLinkUpdate, WebLinkGeneric]):
    """
    Service for WebLink entity.

    This class handles database operations for WebLink.
    It inherits from BaseService which provides common CRUD operations.
    """

    def __init__(self):
        """Initialize the WebLinkService with its model class and relationship map."""
        super().__init__(
            model_class=WebLink,
            entity_name="WebLink",
            relationship_map=RELATIONSHIP_MAP,
            generic_schema=WebLinkGeneric
        )
        
        # Define Campos de busca (apenas campos de texto)
        self.searchable_fields = [
            "weblink",
            "resumo",
            "title",
        ]

    def create(self, db: Session, data: WebLinkCreate) -> WebLink:
        """
        Create a new WebLink entity with special handling for enum values.

        Args:
            db: Database session
            data: Data for creating the entity

        Returns:
            The created entity
        """
        create_data = data.model_dump(exclude_unset=True)

        # Create the model instance
        db_model = WebLink(**create_data)
        db.add(db_model)

        try:
            db.flush()  
            db.commit()  
            db.refresh(db_model)  

        except IntegrityError as e:
            db.rollback()
            print(f"Erro de Integridade ao criar {self.entity_name}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Não foi possível criar {self.entity_name}. Verifique se há violação de valores únicos ou chaves estrangeiras inválidas."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno no servidor ao criar {self.entity_name}.")

        return db_model

    def update(
        self,
        db: Session,
        id: UUID,
        data: WebLinkUpdate
    ) -> Optional[WebLink]:
        """
        Update an existing WebLink entity with special handling for enum values.

        Args:
            db: Database session
            id: Entity ID
            data: Data for updating the entity

        Returns:
            The updated entity or None if not found
        """
        db_model = self.get_by_id(db, id)
        if db_model is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(db_model, key):
                setattr(db_model, key, value) 
            else:
                print(f"Aviso: Campo '{key}' não encontrado no modelo {self.entity_name} durante update.")

        db.add(db_model)
        try:
            db.commit()
            db.refresh(db_model)
        except IntegrityError as e:
            db.rollback()
            print(f"Erro de Integridade ao atualizar {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Não foi possível atualizar {self.entity_name}. Verifique se há violação de valores únicos ou chaves estrangeiras inválidas."
            )
        except Exception as e:
            db.rollback()
            print(f"Erro inesperado ao atualizar {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno no servidor ao atualizar {self.entity_name}.")

        return db_model
    
    def get_by_telefone(self, db: Session, telefone: str) -> Optional[WebLink]:
        return db.query(self.model_class).filter(self.model_class.telefone == telefone).first()

WebLink_service = WebLinkService()
