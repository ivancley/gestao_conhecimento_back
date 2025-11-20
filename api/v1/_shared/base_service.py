from typing import Generic, TypeVar, List, Optional, Dict, Any, Literal, Tuple, Type
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.utils.crud_utils import apply_filters, apply_sorting, get_validated_load_options
from api.utils.utils_bd import apply_search, apply_select_load_options, parse_select_fields_for_pydantic

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
CreateSchemaType = TypeVar('CreateSchemaType')  # Schema for creating an item
UpdateSchemaType = TypeVar('UpdateSchemaType')  # Schema for updating an item
GenericSchemaType = TypeVar('GenericSchemaType')  # Generic schema for returning an item

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, GenericSchemaType]):
    """
    Base class for all Service classes to reduce code duplication and improve maintainability.

    This class provides common CRUD operations with consistent error handling.
    """

    def __init__(
        self,
        model_class: Type[ModelType],
        entity_name: str,
        relationship_map: Dict[str, Any],
        generic_schema: Type[GenericSchemaType], 
    ):
        """
        Initialize the base service with model class and relationship map.

        Args:
            model_class: The SQLAlchemy model class
            entity_name: The name of the entity (used in error messages)
            relationship_map: Dictionary mapping relationship names to SQLAlchemy relationship attributes
        """
        self.model_class = model_class
        self.entity_name = entity_name
        self.relationship_map = relationship_map
        self.generic_schema = generic_schema

    def _get_query_with_includes(
        self,
        db: Session,
        base_query: Any,
        include: Optional[List[str]] = None
    ) -> Any:
        """
        Add relationship loading options to a query based on the include parameter.

        Args:
            db: Database session
            base_query: The base SQLAlchemy query
            include: List of relationship names to include

        Returns:
            The query with include options added
        """
        if include:
            try:
                load_options = get_validated_load_options(self.model_class, self.relationship_map, include)
                base_query = base_query.options(*load_options)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid include parameter: {str(e)}")
        return base_query

    def get_by_id(
        self,
        db: Session,
        id: UUID,
        include: Optional[List[str]] = None,
        select_fields: Optional[List[str]] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[ModelType]:
        """
        Get an entity by ID.

        Args:
            db: Database session
            id: Entity ID
            include: Related entities to include
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            The entity or None if not found
        """
        query = select(self.model_class).where(self.model_class.id == id)
        
        # Apply user ownership filter if user_id is provided and model has usuario_id
        if user_id and hasattr(self.model_class, 'usuario_id'):
            query = query.where(self.model_class.usuario_id == user_id)
        # Garantir que relacionamentos solicitados em 'include' não recebam estratégia noload
        include_param_for_load_options = ",".join(include) if include else select_fields
        query = apply_select_load_options(
            query,
            self.model_class,
            include_param=include_param_for_load_options
        )
        result = db.execute(query).scalar_one_or_none()
        
        if select_fields:
            pydantic_include_structure = parse_select_fields_for_pydantic(select_fields)
            view_instance = self.generic_schema.model_validate(result.__dict__)
            # model_dump lida com include=None ou include={} da forma correta.
            return view_instance.model_dump(include=pydantic_include_structure)
        
        return result

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
    ) -> Tuple[List[ModelType], int]:
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
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            Tuple of (list of entities, total count)
        """
        base_query = select(self.model_class)
        count_query = select(func.count(self.model_class.id))
        
        # Apply user ownership filter if user_id is provided and model has usuario_id
        if user_id and hasattr(self.model_class, 'usuario_id'):
            base_query = base_query.where(self.model_class.usuario_id == user_id)
            count_query = count_query.where(self.model_class.usuario_id == user_id)
        
        if search:
            base_query = apply_search(base_query, self.model_class, search, self.searchable_fields)
            count_query = apply_search(count_query.select_from(self.model_class), self.model_class, search, self.searchable_fields)
        
        if filter_params:
            try:
                base_query = apply_filters(base_query, self.model_class, filter_params, self.relationship_map)
                count_query = apply_filters(count_query.select_from(self.model_class), self.model_class, filter_params, self.relationship_map)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid filter parameter: {str(e)}")
        
        total_count = db.execute(count_query).scalar() or 0
        
        if sort_by:
            try:
                base_query = apply_sorting(base_query, self.model_class, sort_by, sort_dir, self.relationship_map)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort parameter: {str(e)}")
        
        # Apply includes
        if include:
            base_query = self._get_query_with_includes(db, base_query, include)
        
        # Garantir que relacionamentos solicitados em 'include' não recebam estratégia noload
        include_param_for_load_options = ",".join(include) if include else select_fields
        base_query = apply_select_load_options(
            base_query,
            self.model_class,
            include_param=include_param_for_load_options
        )
        query = base_query.offset(skip).limit(limit)
        results = db.execute(query).scalars().all()
        
        if select_fields:
            pydantic_include_structure = parse_select_fields_for_pydantic(select_fields)
            processed_results = [
                self.generic_schema.model_validate(item.__dict__).model_dump(include=pydantic_include_structure)
                for item in results
            ]
            return processed_results, total_count
        else:
            return results, total_count

    def create(self, db: Session, data: CreateSchemaType) -> ModelType:
        """
        Create a new entity.

        Args:
            db: Database session
            data: Data for creating the entity

        Returns:
            The created entity
        """
        create_data = data.model_dump(exclude_unset=True)
        
        db_model = self.model_class(**create_data)
        db.add(db_model)

        try:
            db.flush()  # Ensure ID and other DB defaults are ready
            db.commit()  # Save the main entity
            db.refresh(db_model)  # Update scalar attributes of db_model
            
            # Determine which relationships to load after create
            relations_to_load_after_create = []
            for rel_name in self.relationship_map.keys():
                relations_to_load_after_create.append(rel_name)
            
            if relations_to_load_after_create:
                try:
                    db.refresh(db_model, attribute_names=relations_to_load_after_create)
                except Exception as refresh_err:
                    print(f"WARNING: Failed to load relationships {relations_to_load_after_create} after creating {self.entity_name} (ID: {db_model.id}): {refresh_err}")
            
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity Error when creating {self.entity_name}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not create {self.entity_name}. Check for unique value violations or invalid foreign keys."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when creating {self.entity_name}.")

        return db_model

    def update(
        self,
        db: Session,
        id: UUID,
        data: UpdateSchemaType,
        user_id: Optional[UUID] = None,
    ) -> Optional[ModelType]:
        """
        Update an existing entity.

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
        
        for key, value in update_data.items():
            if hasattr(db_model, key):
                setattr(db_model, key, value)
            else:
                print(f"Warning: Field '{key}' not found in {self.entity_name} model during update.")

        db.add(db_model)
        try:
            db.commit()
            db.refresh(db_model)
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity Error when updating {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not update {self.entity_name}. Check for unique value violations or invalid foreign keys."
            )
        except Exception as e:
            db.rollback()
            print(f"Unexpected error when updating {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when updating {self.entity_name}.")

        return db_model

    def delete(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[ModelType]:
        """
        Soft delete an entity by setting flg_excluido to True.

        Args:
            db: Database session
            id: Entity ID
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            The soft deleted entity or None if not found
        """
        db_model = self.get_by_id(db, id, user_id=user_id)
        if db_model is None:
            return None
            
        try:
            # Soft delete by setting flg_excluido to True
            if hasattr(db_model, 'flg_excluido'):
                db_model.flg_excluido = True
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
            else:
                # If model doesn't support soft delete, do hard delete
                db.delete(db_model)
                db.commit()
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity Error when deleting {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not delete {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            print(f"Unexpected error when deleting {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when deleting {self.entity_name}.")
            
        return db_model

    def restore(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[ModelType]:
        """
        Restore a soft deleted entity by setting flg_excluido to False.

        Args:
            db: Database session
            id: Entity ID
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            The restored entity or None if not found
        """
        # Get the entity including soft deleted ones
        query = select(self.model_class).where(self.model_class.id == id)
        
        # Apply user ownership filter if user_id is provided and model has usuario_id
        if user_id and hasattr(self.model_class, 'usuario_id'):
            query = query.where(self.model_class.usuario_id == user_id)
            
        db_model = db.execute(query).scalar_one_or_none()
        
        if db_model is None:
            return None
            
        try:
            # Restore by setting flg_excluido to False
            if hasattr(db_model, 'flg_excluido'):
                db_model.flg_excluido = False
                db.add(db_model)
                db.commit()
                db.refresh(db_model)
            else:
                # If model doesn't support soft delete, this operation is not applicable
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{self.entity_name} does not support soft delete/restore operations."
                )
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity Error when restoring {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not restore {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            print(f"Unexpected error when restoring {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when restoring {self.entity_name}.")
            
        return db_model

    def get_deleted(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        select_fields: Optional[str] = None,
        include: Optional[List[str]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_dir: Optional[Literal["asc", "desc"]] = "asc",
        user_id: Optional[UUID] = None,
    ) -> Tuple[List[ModelType], int]:
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
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            Tuple of (list of soft deleted entities, total count)
        """
        if not hasattr(self.model_class, 'flg_excluido'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{self.entity_name} does not support soft delete operations."
            )
            
        base_query = select(self.model_class).where(self.model_class.flg_excluido == True)
        count_query = select(func.count(self.model_class.id)).where(self.model_class.flg_excluido == True)
        
        # Apply user ownership filter if user_id is provided and model has usuario_id
        if user_id and hasattr(self.model_class, 'usuario_id'):
            base_query = base_query.where(self.model_class.usuario_id == user_id)
            count_query = count_query.where(self.model_class.usuario_id == user_id)
        
        if search:
            base_query = apply_search(base_query, self.model_class, search, self.searchable_fields)
            count_query = apply_search(count_query.select_from(self.model_class), self.model_class, search, self.searchable_fields)
        
        if filter_params:
            try:
                base_query = apply_filters(base_query, self.model_class, filter_params, self.relationship_map)
                count_query = apply_filters(count_query.select_from(self.model_class), self.model_class, filter_params, self.relationship_map)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid filter parameter: {str(e)}")
        
        total_count = db.execute(count_query).scalar() or 0
        
        if sort_by:
            try:
                base_query = apply_sorting(base_query, self.model_class, sort_by, sort_dir, self.relationship_map)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid sort parameter: {str(e)}")
        
        base_query = apply_select_load_options(
            base_query,
            self.model_class,
            include_param=self._merge_include_into_select(select_fields, include)
        )
        query = base_query.offset(skip).limit(limit)
        results = db.execute(query).scalars().all()
        
        return results, total_count

    def hard_delete(self, db: Session, id: UUID, user_id: Optional[UUID] = None) -> Optional[ModelType]:
        """
        Hard delete an entity (permanently remove from database).

        Args:
            db: Database session
            id: Entity ID
            user_id: ID of the logged-in user (for filtering by ownership)

        Returns:
            The deleted entity or None if not found
        """
        # Get the entity including soft deleted ones
        query = select(self.model_class).where(self.model_class.id == id)
        
        # Apply user ownership filter if user_id is provided and model has usuario_id
        if user_id and hasattr(self.model_class, 'usuario_id'):
            query = query.where(self.model_class.usuario_id == user_id)
            
        db_model = db.execute(query).scalar_one_or_none()
        
        if db_model is None:
            return None
            
        try:
            db.delete(db_model)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity Error when hard deleting {self.entity_name} ID {id}: {e.orig}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not hard delete {self.entity_name} (ID: {id}) due to existing references or other integrity constraints."
            )
        except Exception as e:
            db.rollback()
            print(f"Unexpected error when hard deleting {self.entity_name} ID {id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error when hard deleting {self.entity_name}.")
            
        return db_model

    def _merge_include_into_select(self, select_fields: Optional[str], include: Optional[List[str]]) -> Optional[str]:
        """
        Combina o parâmetro `select` (string) com a lista `include` produzindo
        uma única string compatível com a sintaxe esperada por
        `apply_select_load_options`.  Cada relacionamento em `include` é
        convertido para a forma "[rel]" para que seja interpretado como
        relacionamento completo.

        Exemplo:
            select_fields = "id,nome"
            include = ["paciente", "consultas"]
            -> "id,nome,[paciente],[consultas]"
        """

        if not include:
            return select_fields  # pode ser None ou string

        include_tokens = ",".join(f"[{rel}]" for rel in include)

        if select_fields:
            return f"{select_fields},{include_tokens}"
        else:
            return include_tokens