from typing import Generic, TypeVar, List, Optional, Dict, Any, Type, Set
from uuid import UUID
from enum import Enum
import traceback
from api.utils.utils_bd import (
    parse_select_fields_for_pydantic,
    extract_relationships_from_select_hybrid,
)
from sqlalchemy.inspection import inspect as sa_inspect

# Type variables for generics
ModelType = TypeVar('ModelType')  # Database model
ViewSchemaType = TypeVar('ViewSchemaType')  # Schema for returning an item

class BaseMapper(Generic[ModelType, ViewSchemaType]):
    """
    Base class for all Mapper classes to reduce code duplication and improve performance.

    This class provides common mapping operations with optimized relationship loading.
    """

    def __init__(
        self,
        model_class: Type[ModelType],
        view_class: Type[ViewSchemaType],
        entity_name: str,
        relationship_map: Dict[str, Dict[str, Any]],
        sensitive_fields: Optional[List[str]] = None,
    ):
        """
        Initialize the base mapper with model class, view class, and relationship map.

        Args:
            model_class: The SQLAlchemy model class
            view_class: The Pydantic view model class
            entity_name: The name of the entity (used in error messages)
            relationship_map: Dictionary mapping relationship names to their mapper functions and types
                Format: {
                    'relation_name': {
                        'mapper': mapper_function,
                        'is_list': True/False,
                        'model_class': RelatedModelClass
                    }
                }
        """
        self.model_class = model_class
        self.view_class = view_class
        self.entity_name = entity_name
        self.relationship_map = relationship_map
        self.sensitive_fields = sensitive_fields or []
        self._visiting_tracker: Set[UUID] = set()

    def _is_being_visited(self, model: ModelType) -> bool:
        """Check if a model is already being visited to prevent infinite recursion."""
        model_id = getattr(model, 'id', None)
        if model_id is None:
            return False

        return model_id in self._visiting_tracker

    def _mark_as_visiting(self, model: ModelType) -> None:
        """Mark a model as being visited."""
        model_id = getattr(model, 'id', None)
        if model_id is not None:
            self._visiting_tracker.add(model_id)

    def _unmark_as_visiting(self, model: ModelType) -> None:
        """Unmark a model as being visited."""
        model_id = getattr(model, 'id', None)
        if model_id is not None and model_id in self._visiting_tracker:
            self._visiting_tracker.remove(model_id)

    def _handle_enum_value(self, value: Any) -> Any:
        """Convert enum values to their string representation."""
        if isinstance(value, Enum):
            return value.value
        return value

    def _extract_model_data(self, model: ModelType) -> Dict[str, Any]:
        """Extract data from a model instance."""
        # Get all attributes from the model
        data = {}
        for column in model.__table__.columns:
            attr_name = column.name
            if attr_name in self.sensitive_fields:
                continue  # Skip sensitive fields
            value = getattr(model, attr_name, None)
            data[attr_name] = self._handle_enum_value(value)

        return data

    def map_to_view(
        self,
        model: ModelType,
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
    ) -> Optional[ViewSchemaType]:
        """
        Map a model instance to a view model.

        Args:
            model: The model instance to map
            include: List of relationships to include

        Returns:
            The mapped view model or None if mapping fails
        """
        if model is None:
            return None

        # Check for circular references
        if self._is_being_visited(model):
            return None

        # Mark as visiting to prevent infinite recursion
        self._mark_as_visiting(model)

        try:
            # Extract base data from model
            view_data = self._extract_model_data(model)

            # Initialize relationship fields
            for rel_name, rel_config in self.relationship_map.items():
                if rel_config.get('is_list', False):
                    view_data[rel_name] = []
                else:
                    view_data[rel_name] = None

            # Determinar quais relacionamentos incluir
            requested_rels: List[str] = list(include or [])

            if select_fields:
                model_relation_keys = {r.key for r in sa_inspect(self.model_class).relationships}
                requested_rels.extend(
                    list(
                        extract_relationships_from_select_hybrid(select_fields, model_relation_keys)
                    )
                )

            # Incluir relacionamentos solicitados
            if requested_rels:
                for rel_name in requested_rels:
                    if rel_name in self.relationship_map:
                        rel_config = self.relationship_map[rel_name]
                        mapper_func = rel_config.get('mapper')

                        if mapper_func:
                            related_attr = getattr(model, rel_name, None)

                            if related_attr is not None:
                                if rel_config.get('is_list', False):
                                    # Handle to-many relationships
                                    if isinstance(related_attr, (list, set)):
                                        # Pass the include parameter to support nested includes
                                        mapped_list = [mapper_func(obj, include) for obj in related_attr if obj is not None]
                                        view_data[rel_name] = [item for item in mapped_list if item is not None]
                                else:
                                    # Handle to-one relationships
                                    mapped_related = mapper_func(related_attr, include)
                                    if mapped_related:
                                        view_data[rel_name] = mapped_related

            # Validate and create view model
            try:
                validated_view = self.view_class.model_validate(view_data)

                # Se select_fields foi fornecido, aplicar recorte usando utilitário existente
                if select_fields:
                    include_structure = parse_select_fields_for_pydantic(select_fields)
                    return validated_view.model_dump(include=include_structure)

                return validated_view
            except Exception as e_pydantic:
                print(f"ERRO Pydantic: Falha ao validar {self.entity_name}View para ID {getattr(model, 'id', None)}. Erro: {e_pydantic}")
                return None

        except Exception as e_outer:
            print(f"ERRO INESPERADO no mapper para {self.entity_name} (ID: {getattr(model, 'id', None)}). Erro: {e_outer}")
            print(traceback.format_exc())
            return None
        finally:
            # Unmark as visiting
            self._unmark_as_visiting(model)

    def map_list_to_view(
        self,
        models: List[ModelType],
        include: Optional[List[str]] = None,
        select_fields: Optional[str] = None,
    ) -> List[ViewSchemaType]:
        """
        Map a list of model instances to view models.

        Args:
            models: The list of model instances to map
            include: List of relationships to include

        Returns:
            The list of mapped view models
        """
        if not models:
            return []

        mapped_list = [self.map_to_view(model, include, select_fields) for model in models if model is not None]
        return [view for view in mapped_list if view is not None]