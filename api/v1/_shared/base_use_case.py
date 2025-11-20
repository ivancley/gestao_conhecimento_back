from typing import Generic, TypeVar, List, Optional, Dict, Any, Literal, Callable, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.utils.exceptions import exception_internal_server_error

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
CreateSchemaType = TypeVar('CreateSchemaType')  # Schema for creating an item
UpdateSchemaType = TypeVar('UpdateSchemaType')  # Schema for updating an item
ViewSchemaType = TypeVar('ViewSchemaType')  # Schema for returning an item

class BaseUseCase(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ViewSchemaType]):
    """
    Base class for all Use Case classes to reduce code duplication and improve maintainability.

    This class provides common CRUD operations with consistent error handling and mapping
    between database models and view models.
    """

    def __init__(
        self,
        service: Any,
        entity_name: str,
        map_to_view: Callable[[ModelType, Optional[List[str]]], Optional[ViewSchemaType]],
        map_list_to_view: Callable[[List[ModelType], Optional[List[str]]], List[ViewSchemaType]]
    ):
        """
        Initialize the base use case with service and mapper functions.

        Args:
            service: The service instance that handles database operations
            entity_name: The name of the entity (used in error messages)
            map_to_view: Function to map a single model to a view model
            map_list_to_view: Function to map a list of models to view models
        """
        self.service = service
        self.entity_name = entity_name
        self.map_to_view = map_to_view
        self.map_list_to_view = map_list_to_view

    def _assign_usuario_id(self, data: Any, user_info: Optional[Any] = None) -> Any:
        """
        Assign usuario_id to data if not provided and user_info is available.
        
        Args:
            data: The schema data (Create or Update)
            user_info: Usuario object from authentication (from security.get_current_user)
            
        Returns:
            The data with usuario_id assigned if needed
        """
        # Verifica se o schema tem o campo usuario_id
        if hasattr(data, 'usuario_id'):
            # atribui do user_info
            if user_info is not None:
                try:
                    # user_info agora é um objeto Usuario, não mais uma tupla
                    logged_user_id = user_info.id if hasattr(user_info, 'id') else user_info
                    
                    # Converte para UUID se necessário
                    if not isinstance(logged_user_id, UUID):
                        logged_user_id = UUID(str(logged_user_id))
                    
                    # Cria uma nova instância com usuario_id preenchido
                    data_dict = data.model_dump(exclude_unset=True)
                    data_dict["usuario_id"] = logged_user_id
                    data = type(data)(**data_dict)
                    
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Erro ao processar usuario_id: {str(e)}"
                    )
        
        return data

    async def get_all(
        self,
        db: Session,
        skip: int,
        limit: int,
        include: Optional[List[str]],
        filter_params: Optional[Dict[str, Dict[str, Any]]],
        sort_by: Optional[str],
        sort_dir: Optional[Literal["asc", "desc"]],
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
        user_info: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get all entities with pagination, filtering, and sorting.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include: Related entities to include
            filter_params: Filtering parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (asc or desc)
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            Dictionary with total count and list of view models
        """
        try:
            if filter_params is None:
                filter_params = {}
            
            user_id = None
            if user_info:
                # user_info agora é um objeto Usuario, não mais uma tupla
                user_id = user_info.id if hasattr(user_info, 'id') else user_info
                # Convert to UUID if necessary
                if not isinstance(user_id, UUID):
                    user_id = UUID(str(user_id))
                
                #user = usuario_service.get_by_id(db=db, id=user_id)
                #if user is None or user.tipo_usuario != TipoUsuario.ADMIN.value:
                #    filter_params['flg_excluido'] = {'eq': False}
            else:
                filter_params['flg_excluido'] = {'eq': False}
            
            models, total_count = self.service.get_all(
                db=db,
                skip=skip,
                limit=limit,
                include=include,
                filter_params=filter_params,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                select_fields=select_fields,
                user_id=user_id,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise exception_internal_server_error(f"Internal server error - {str(e)}")

        if not select_fields:
            models = self.map_list_to_view(models, include)
            return {
                "total": total_count,
                "data": models,
                "page": int((skip/limit)+1),
                "limit": limit
            }

        return {
            "total": total_count,
            "data": models,
            "page": int((skip/limit)+1),
            "limit": limit
        }

    async def create(
        self,
        db: Session,
        data: CreateSchemaType,
        user_info: Optional[Any] = None
    ) -> ViewSchemaType:
        """
        Create a new entity.

        Args:
            db: Database session
            data: Data for creating the entity
            user_info: Optional Usuario object from authentication (from security.get_current_user)

        Returns:
            View model of the created entity
        """
        # Atribui usuario_id automaticamente se necessário
        data = self._assign_usuario_id(data, user_info)
        
        try:
            created_model = self.service.create(db=db, data=data)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.create: {e}")
            raise exception_internal_server_error(f"Internal server error - Create - {str(e)}")

        return self.map_to_view(created_model, None)

    async def get_by_id(
        self,
        db: Session,
        id: UUID,
        include: Optional[List[str]] = None,
        select_fields: Optional[List[str]] = None,
        user_info: Optional[Any] = None,
    ) -> Optional[ViewSchemaType]:
        """
        Get an entity by ID.

        Args:
            db: Database session
            id: Entity ID
            include: Related entities to include
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            View model of the entity or None if not found
        """
        try:
            user_id = None
            if user_info:
                user_id = user_info.id if hasattr(user_info, 'id') else user_info  # Extract user_id from Usuario object
                # Convert to UUID if necessary
                if not isinstance(user_id, UUID):
                    user_id = UUID(str(user_id))
            
            model = self.service.get_by_id(db=db, id=id, include=include, select_fields=select_fields, user_id=user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.get_by_id: {e}")
            raise exception_internal_server_error(f"Internal server error - GET - {str(e)}")

        if model is None:
            return None
        
        # If select_fields were requested, the service layer already returned
        # a serialized dictionary containing only the selected attributes.
        # In that case, we can bypass the mapper and return the data directly.
        if select_fields and isinstance(model, dict):
            # Convert JSON string fields like "alternativas" to Python objects for cleaner output
            self._convert_alternativas_recursive(model)
            return {"data": [model]}

        # For normal cases, map the model to view and return it directly
        mapped_model = self.map_to_view(model, include, select_fields)
        return mapped_model

    async def update(
        self,
        db: Session,
        id: UUID,
        data: UpdateSchemaType,
        user_info: Optional[Any] = None
    ) -> Optional[ViewSchemaType]:
        """
        Update an existing entity.

        Args:
            db: Database session
            id: Entity ID
            data: Data for updating the entity
            user_info: Optional Usuario object from authentication (from security.get_current_user)

        Returns:
            View model of the updated entity or None if not found
        """
        user_id = None
        if user_info:
            user_id = user_info.id if hasattr(user_info, 'id') else user_info
            # Convert to UUID if necessary
            if not isinstance(user_id, UUID):
                user_id = UUID(str(user_id))
        
        existing_model = self.service.get_by_id(db=db, id=id, user_id=user_id)
        if existing_model is None:
            return None

        # Atribui usuario_id automaticamente se necessário
        data = self._assign_usuario_id(data, user_info)

        try:
            updated_model = self.service.update(db=db, id=id, data=data, user_id=user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.update: {e}")
            raise exception_internal_server_error(f"Internal server error - Update - {str(e)}")

        return self.map_to_view(updated_model, None)

    async def delete(
        self,
        db: Session,
        id: UUID,
        user_info: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Delete an entity.

        Args:
            db: Database session
            id: Entity ID
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            The deleted entity or None if not found
        """
        user_id = None
        if user_info:
            user_id = user_info.id if hasattr(user_info, 'id') else user_info
            # Convert to UUID if necessary
            if not isinstance(user_id, UUID):
                user_id = UUID(str(user_id))
        
        existing_model = self.service.get_by_id(db=db, id=id, user_id=user_id)
        if existing_model is None:
            return None

        try:
            deleted_model = self.service.delete(db=db, id=id, user_id=user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.delete: {e}")
            raise exception_internal_server_error(f"Internal server error - Delete - {str(e)}")

        return deleted_model

    async def restore(
        self,
        db: Session,
        id: UUID,
        user_info: Optional[Any] = None
    ) -> Optional[ViewSchemaType]:
        """
        Restore a soft deleted entity.

        Args:
            db: Database session
            id: Entity ID
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            View model of the restored entity or None if not found
        """
        try:
            user_id = None
            if user_info:
                user_id = user_info.id if hasattr(user_info, 'id') else user_info  # Extract user_id from Usuario object
                # Convert to UUID if necessary
                if not isinstance(user_id, UUID):
                    user_id = UUID(str(user_id))
            
            restored_model = self.service.restore(db=db, id=id, user_id=user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.restore: {e}")
            raise exception_internal_server_error(f"Internal server error - Restore - {str(e)}")

        if restored_model is None:
            return None

        return self.map_to_view(restored_model, None)

    async def get_deleted(
        self,
        db: Session,
        skip: int,
        limit: int,
        include: Optional[List[str]],
        filter_params: Optional[Dict[str, Dict[str, Any]]],
        sort_by: Optional[str],
        sort_dir: Optional[Literal["asc", "desc"]],
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
        user_info: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Get all soft deleted entities with pagination, filtering, and sorting.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include: Related entities to include
            filter_params: Filtering parameters
            sort_by: Field to sort by
            sort_dir: Sort direction (asc or desc)
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            Dictionary with total count and list of view models
        """
        try:
            user_id = None
            if user_info:
                user_id = user_info.id if hasattr(user_info, 'id') else user_info  # Extract user_id from Usuario object
                # Convert to UUID if necessary
                if not isinstance(user_id, UUID):
                    user_id = UUID(str(user_id))
            
            models, total_count = self.service.get_deleted(
                db=db,
                skip=skip,
                limit=limit,
                include=include,
                filter_params=filter_params,
                sort_by=sort_by,
                sort_dir=sort_dir,
                search=search,
                select_fields=select_fields,
                user_id=user_id,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise exception_internal_server_error(f"Internal server error - {str(e)}")

        if not select_fields:
            models = self.map_list_to_view(models, include)
            return {"total": total_count, "data": models}

        return {"total": total_count, "data": models}

    async def hard_delete(
        self,
        db: Session,
        id: UUID,
        user_info: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Hard delete an entity (permanently remove from database).

        Args:
            db: Database session
            id: Entity ID
            user_info: Usuario object from authentication (from security.get_current_user)

        Returns:
            The deleted entity or None if not found
        """
        try:
            user_id = None
            if user_info:
                user_id = user_info.id if hasattr(user_info, 'id') else user_info  # Extract user_id from Usuario object
                # Convert to UUID if necessary
                if not isinstance(user_id, UUID):
                    user_id = UUID(str(user_id))
            
            deleted_model = self.service.hard_delete(db=db, id=id, user_id=user_id)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Internal error in {self.entity_name}Service.hard_delete: {e}")
            raise exception_internal_server_error(f"Internal server error - Hard Delete - {str(e)}")

        return deleted_model

    def _convert_alternativas_recursive(self, data: Any) -> None:
        """
        Recursively converts JSON string fields like "alternativas" to Python objects.
        This is useful for handling deeply nested dictionaries or lists of dictionaries.
        """
        import json
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "alternativas" and isinstance(value, str):
                    try:
                        # Parse JSON string to array
                        data[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Keep original value if parsing fails
                        pass
                elif isinstance(value, (dict, list)):
                    self._convert_alternativas_recursive(value)
        elif isinstance(data, list):
            for item in data:
                self._convert_alternativas_recursive(item)