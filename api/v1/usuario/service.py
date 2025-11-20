from typing import Optional, List, Dict, Any, Literal, Tuple    
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.v1._database.models import Usuario
from api.v1._shared.schemas import UsuarioCreate, UsuarioUpdate, UsuarioGeneric
from api.v1._shared.base_service import BaseService




# Mapeamento de nomes de relacionamento
RELATIONSHIP_MAP = {
    "web_links": Usuario.web_links,
}

class UsuarioService(BaseService[Usuario, UsuarioCreate, UsuarioUpdate, UsuarioGeneric]):
    """
    Service for Usuario entity.

    This class handles database operations for Usuario.
    It inherits from BaseService which provides common CRUD operations.
    """

    def __init__(self):
        """Initialize the UsuarioService with its model class and relationship map."""
        super().__init__(
            model_class=Usuario,
            entity_name="Usuario",
            relationship_map=RELATIONSHIP_MAP,
            generic_schema=UsuarioGeneric
        )
        
        # Define searchable fields for the entity
        self.searchable_fields = [
            "nome",
            "email",
            ]

    def create(self, db: Session, data: UsuarioCreate) -> Usuario:
        """
        Create a new Usuario entity with special handling for enum values.

        Args:
            db: Database session
            data: Data for creating the entity

        Returns:
            The created entity
        """
        create_data = data.model_dump(exclude_unset=True)

        # Create the model instance
        db_model = Usuario(**create_data)
        db.add(db_model)

        try:
            db.flush()  # Ensure ID and other DB defaults are ready
            db.commit()  # Save the main entity
            db.refresh(db_model)  # Update scalar attributes of db_model

            # No specific relationships to load after create for Usuario

        except IntegrityError as e:
            db.rollback()
            error_message = str(e.orig).lower()
            print(f"Erro de Integridade ao criar {self.entity_name}: {e.orig}")
            
            # Detectar qual campo está causando a violação de unicidade
            if 'email' in error_message or 'ix_usuario_email' in error_message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="O email informado já está cadastrado no sistema."
                )
            elif 'unique' in error_message or 'duplicate' in error_message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um usuário com esses dados cadastrados. Verifique email."
                )
            else:
                # Outros erros de integridade (foreign keys, etc)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Erro ao criar usuário. Verifique se todos os dados estão corretos."
                )
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno no servidor ao criar {self.entity_name}.")

        return db_model

    def update(
        self,
        db: Session,
        id: UUID,
        data: UsuarioUpdate,
        user_id: Optional[UUID] = None
    ) -> Optional[Usuario]:
        """
        Update an existing Usuario entity with special handling for enum values.

        Args:
            db: Database session
            id: Entity ID
            data: Data for updating the entity
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            The updated entity or None if not found
        """
        db_model = self.get_by_id(db, id, user_id=user_id)
        if db_model is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle enum values
        

        # Update the model
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
            error_message = str(e.orig).lower()
            print(f"Erro de Integridade ao atualizar {self.entity_name} ID {id}: {e.orig}")
            
            # Detectar qual campo está causando a violação de unicidade
            if 'email' in error_message or 'ix_usuario_email' in error_message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="O email informado já está cadastrado no sistema."
                )
            elif 'unique' in error_message or 'duplicate' in error_message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um usuário com esses dados cadastrados. Verifique email."
                )
            else:
                # Outros erros de integridade (foreign keys, etc)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Erro ao atualizar usuário. Verifique se todos os dados estão corretos."
                )
        except Exception as e:
            db.rollback()
            print(f"Erro inesperado ao atualizar {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno no servidor ao atualizar {self.entity_name}.")

        return db_model

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        include: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[Literal["asc", "desc"]] = "asc",
        user_id: Optional[UUID] = None,
    ) -> Tuple[List[Usuario], int]:
        """
        Override get_all for Usuario with special filtering logic.
        Non-admin users can only see their own profile.
        """
        # If user_id is provided, check if user is admin
        #if user_id:
        #    current_user = super().get_by_id(db, user_id, user_id=None)
        #    if current_user and current_user.tipo_usuario != TipoUsuario.ADMIN.value:
        #        # Non-admin users can only see their own profile
        #        if filter_params is None:
        #            filter_params = {}
        #        filter_params['id'] = {'eq': user_id}
        
        # Call the parent method with the modified filter_params
        return super().get_all(
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            select_fields=select_fields,
            include=include,
            filter_params=filter_params,
            sort_by=sort_by,
            sort_dir=sort_dir,
            user_id=None  # Don't apply the base user filtering for Usuario model
        )

    def get_by_id(
        self,
        db: Session,
        id: UUID,
        include: Optional[List[str]] = None,
        select_fields: Optional[List[str]] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[Usuario]:
        """
        Override get_by_id for Usuario with special filtering logic.
        Non-admin users can only see their own profile.
        """
        # If user_id is provided, check permissions
        if user_id and user_id != id:
            # Get the current user to check if they're admin
            current_user = super().get_by_id(db, user_id, user_id=None)
        #    if current_user and current_user.tipo_usuario != TipoUsuario.ADMIN.value:
        #        # Non-admin users can only see their own profile
        #        return None
        
        # Call the parent method without user_id filtering
        return super().get_by_id(
            db=db,
            id=id,
            include=include,
            select_fields=select_fields,
            user_id=None  # Don't apply the base user filtering for Usuario model
        )

    def update(
        self,
        db: Session,
        id: UUID,
        data: UsuarioUpdate,
        user_id: Optional[UUID] = None,
    ) -> Optional[Usuario]:
        """
        Override update for Usuario with special filtering logic.
        Non-admin users can only update their own profile.
        """
        # If user_id is provided, check permissions
        if user_id and user_id != id:
            # Get the current user to check if they're admin
            current_user = self.get_by_id(db, user_id, user_id=None)
        #       if current_user and current_user.tipo_usuario != TipoUsuario.ADMIN.value:
                # Non-admin users can only update their own profile
        #        return None
        
        # Call the parent method without user_id filtering
        return super().update(
            db=db,
            id=id,
            data=data,
            user_id=None  # Don't apply the base user filtering for Usuario model
        )

    def delete(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[Usuario]:
        """
        Override delete for Usuario with special filtering logic.
        Non-admin users can only delete their own profile.
        """
        # If user_id is provided, check permissions
        if user_id and user_id != id:
            # Get the current user to check if they're admin
            current_user = self.get_by_id(db, user_id, user_id=None)
        #    if current_user and current_user.tipo_usuario != TipoUsuario.ADMIN.value:
                # Non-admin users can only delete their own profile
        #        return None
        
        # Call the parent method without user_id filtering
        return super().delete(
            db=db,
            id=id,
            user_id=None  # Don't apply the base user filtering for Usuario model
        )

usuario_service = UsuarioService()