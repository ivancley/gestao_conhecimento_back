import re
import logging
from typing import List, Optional, Dict, Any, Type, Literal, Tuple, Set
from datetime import datetime, timezone

from sqlalchemy.sql.selectable import Select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import asc, desc, inspect, or_
from sqlalchemy.orm import RelationshipProperty
from starlette.datastructures import QueryParams
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import Load, RelationshipProperty, with_loader_criteria, selectinload, noload


logger = logging.getLogger(__name__)

FILTER_PATTERN = re.compile(r"filter\[(.+?)\]\[(.+?)\]")

OPERATOR_MAP = {
    'eq': lambda c, v: c == v,
    'neq': lambda c, v: c != v,
    'lt': lambda c, v: c < v,
    'lte': lambda c, v: c <= v,
    'gt': lambda c, v: c > v,
    'gte': lambda c, v: c >= v,
    'in': lambda c, v: c.in_(v),
    'notin': lambda c, v: c.notin_(v),
    'like': lambda c, v: c.like(v),
    'ilike': lambda c, v: c.ilike(v),
    'isnull': lambda c, v: c.is_(None) if _parse_bool(v) else c.is_not(None),
    'contains': lambda c, v: c.contains(v),
    'startswith': lambda c, v: c.startswith(v),
    'endswith': lambda c, v: c.endswith(v),
}


def _parse_bool(value: Any) -> bool:
    """Converte um valor para booleano de forma flexível."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on')
    return bool(value)


def _parse_filter_value(value: str) -> Any:
    value_lower = value.lower()
    if value_lower in ('true', 'yes', 'on', '1'):
        return True
    if value_lower in ('false', 'no', 'off', '0'):
        return False
    if value_lower in ('null', 'none'):
        return None
    return value


def _get_column_or_relationship(
    model_cls: Type,
    field_specifier: str,
    relations_map: Dict[str, RelationshipProperty]
) -> Tuple[InstrumentedAttribute, Optional[Type], List[RelationshipProperty]]:
    parts = field_specifier.split('.')
    current_model = model_cls
    target_attribute = None
    joins_needed: List[RelationshipProperty] = []

    for i, part in enumerate(parts):
        if not hasattr(current_model, part):
            raise ValueError(f"Modelo '{current_model.__name__}' não possui o atributo ou relação '{part}' especificado em '{field_specifier}'")

        attr = getattr(current_model, part) # attr é um InstrumentedAttribute

        # attr.property é onde reside a configuração da coluna ou relação
        if isinstance(attr.property, RelationshipProperty):
            if i == len(parts) - 1:
                 raise ValueError(f"Não é possível filtrar/ordenar diretamente pela relação '{part}'. Especifique um campo dentro dela (ex: '{field_specifier}.id').")

            # A RelationshipProperty em si é o que precisamos para o join
            current_relationship_prop: RelationshipProperty = attr.property

            if i == 0: # Relação direta do model_cls base
                if part not in relations_map: # Verifica se a relação base está mapeada
                     raise ValueError(f"Relação '{part}' não encontrada no 'relations_map' fornecido para o modelo base {model_cls.__name__}. Certifique-se que o relations_map contém '{part}': Model.{part}.property.")
                # Usa a RelationshipProperty do relations_map, que deve ser a mesma que current_relationship_prop
                joins_needed.append(relations_map[part])
            else: # Relação aninhada
                 joins_needed.append(current_relationship_prop)

            current_model = current_relationship_prop.mapper.class_
        elif isinstance(attr, InstrumentedAttribute): # Checa o InstrumentedAttribute diretamente para colunas
            if i != len(parts) - 1:
                raise ValueError(f"Atributo '{part}' em '{field_specifier}' não é uma relação, mas existem mais partes.")
            target_attribute = attr
            break
        else:
            raise ValueError(f"Atributo '{part}' em '{field_specifier}' tem tipo inesperado: {type(attr)}. Esperado InstrumentedAttribute.")

    if target_attribute is None:
         raise ValueError(f"Não foi possível resolver o atributo final para '{field_specifier}'.")

    return target_attribute, current_model, joins_needed


def parse_filters(query_params: QueryParams) -> Dict[str, Dict[str, Any]]:
    filters: Dict[str, Dict[str, Any]] = {}
    processed_keys = set()

    logger.debug(f"Parsing query params: {query_params}")

    for key, value in query_params.multi_items():
        if key in processed_keys:
            continue

        match = FILTER_PATTERN.fullmatch(key)
        if match:
            field_specifier = match.group(1)
            operator = match.group(2).lower()

            if not field_specifier or not operator:
                logger.warning(f"Ignorando filtro com field ou operator vazio: {key}")
                continue

            parsed_value = _parse_filter_value(value)

            if field_specifier not in filters:
                filters[field_specifier] = {}

            if operator in filters[field_specifier]:
                 logger.warning(f"Sobrescrevendo filtro existente para {field_specifier}[{operator}] com valor '{value}'. Valor anterior era: {filters[field_specifier][operator]}")

            filters[field_specifier][operator] = parsed_value
            processed_keys.add(key)
            logger.debug(f"Parsed filter: field='{field_specifier}', operator='{operator}', value='{parsed_value}' (original: '{value}')")

        else:
            logger.debug(f"Ignorando parâmetro não-filtro: {key}")


    if not filters:
         logger.debug("Nenhum parâmetro de filtro encontrado.")
    else:
         logger.info(f"Filtros parseados: {filters}")

    return filters

def apply_filters(
    query: Select,
    model_cls: Type,
    filter_params: Dict[str, Dict[str, Any]],
    relations_map: Dict[str, RelationshipProperty],
) -> Select:
    already_joined_relationships_for_where: Set[RelationshipProperty] = set()
    applied_loader_criteria_options: Set[tuple] = set()


    for field_specifier, operators in filter_params.items():
        if not isinstance(operators, dict):
            logger.error(f"Valor para o filtro '{field_specifier}' não é um dicionário: {operators}")
            raise ValueError(f"Valor para o filtro '{field_specifier}' deve ser um dicionário de operadores.")

        try:
            # target_column: Atributo da coluna final (ex: DesempenhoModulo.aluno_id)
            # _: (related_model_cls) Modelo onde target_column reside (ex: DesempenhoModulo)
            # joins_path_properties: Lista de RelationshipProperty para o join (ex: [Modulo.desempenho_modulo.property])
            target_column, _, joins_path_properties = _get_column_or_relationship(
                model_cls, field_specifier, relations_map
            )
        except ValueError as e:
            logger.error(f"Erro ao processar filtro para '{field_specifier}': {e}")
            raise

        # 1. Aplicar JOINs para a cláusula WHERE (filtrar entidades principais)
        #    Se joins_path_properties não for vazio, significa que o filtro é em um campo de uma tabela relacionada.
        #    O join aqui é para garantir que a cláusula WHERE possa acessar o target_column.
        #    A combinação de isouter=True com um WHERE na tabela externa efetivamente funciona como um INNER JOIN
        #    para o propósito de filtrar as entidades 'model_cls'.
        current_join_root = model_cls
        for i, rel_prop in enumerate(joins_path_properties):
            if rel_prop not in already_joined_relationships_for_where:
                logger.debug(f"Aplicando JOIN para filtro WHERE na relação: {rel_prop} (de {field_specifier})")
                # rel_prop.class_attribute é o atributo InstrumentedAttribute (ex: Modulo.desempenho_modulo)
                # Se o caminho for A.b.c, o primeiro join é de A para B (usando A.b). O segundo é de B para C (usando B.c).
                # SQLAlchemy é inteligente e geralmente encadeia joins a partir do modelo base se você der o atributo no modelo base.
                # Para joins encadeados explícitos, seria preciso construir o target do join dinamicamente.
                # A lógica atual junta a partir de `model_cls` para `rel_prop.class_attribute`.
                # Se `joins_path_properties` representa um caminho (A->B, B->C), e é iterado,
                # a query seria query.join(A.b_attr).join(B.c_attr) - o SQLAlchemy resolve isso.
                query = query.join(rel_prop.class_attribute, isouter=True) # isouter=True é crucial com WHERE na tabela externa para não perder linhas principais prematuramente se o filtro principal falhar
                already_joined_relationships_for_where.add(rel_prop)


        for op_code, value in operators.items():
            op_func = OPERATOR_MAP.get(op_code.lower())
            if not op_func:
                raise ValueError(f"Operador de filtro inválido '{op_code}' para o campo '{field_specifier}'. Válidos: {list(OPERATOR_MAP.keys())}")

            try:
                _original_value = value # Guardar para a chave do applied_loader_criteria_options
                if op_code.lower() in ('in', 'notin') and not isinstance(value, (list, tuple)):
                    if isinstance(value, str):
                        value = [item.strip() for item in value.split(',') if item.strip()]
                    else:
                        raise ValueError(f"Valor para operador '{op_code}' no campo '{field_specifier}' deve ser uma lista/tupla ou string separada por vírgulas.")

                # 2. Aplicar cláusula WHERE para filtrar entidades principais
                filter_expression_for_where = op_func(target_column, value)
                query = query.where(filter_expression_for_where)
                logger.debug(f"Aplicando filtro WHERE: {filter_expression_for_where} para {field_specifier}")

                # 3. Aplicar with_loader_criteria para filtrar o conteúdo das coleções carregadas
                if joins_path_properties: # Apenas se o filtro for em uma relação
                    # O atributo da relação no model_cls (ex: Modulo.desempenho_modulo)
                    # Este é o primeiro "pulo" no caminho da relação.
                    first_relationship_property_in_path = joins_path_properties[0]
                    instrumented_relationship_on_model_cls = first_relationship_property_in_path.class_attribute

                    # O critério do loader deve ser aplicado à coluna `target_column`
                    # que reside no modelo alvo da `instrumented_relationship_on_model_cls` (ou mais aninhado).

                    # CASO SIMPLES: O target_column está no modelo diretamente relacionado
                    # Ex: Modulo.desempenho_modulo (relação), DesempenhoModulo.aluno_id (target_column)
                    # Neste caso, len(joins_path_properties) == 1.
                    # O loader_criteria_expression pode usar target_column diretamente.
                    if target_column.parent.class_ == first_relationship_property_in_path.mapper.class_: # Verifica se target_column é do modelo diretamente relacionado
                        loader_criteria_expression = op_func(target_column, value) # Usa o mesmo target_column e value

                        option_key = (instrumented_relationship_on_model_cls.key, target_column.key, op_code, str(_original_value))
                        if option_key not in applied_loader_criteria_options:
                            query = query.options(
                                with_loader_criteria(
                                    instrumented_relationship_on_model_cls, # Ex: Modulo.desempenho_modulo
                                    loader_criteria_expression             # Ex: DesempenhoModulo.aluno_id == valor
                                )
                            )
                            applied_loader_criteria_options.add(option_key)
                            logger.debug(f"Aplicando with_loader_criteria para {instrumented_relationship_on_model_cls.key} com {loader_criteria_expression}")
                        else:
                            logger.debug(f"with_loader_criteria para {instrumented_relationship_on_model_cls.key} com {loader_criteria_expression} já aplicado.")
                    else:
                        # CASO COMPLEXO: O target_column está em um modelo mais aninhado.
                        # Ex: Modulo.aulas.conteudos.titulo
                        # instrumented_relationship_on_model_cls seria Modulo.aulas
                        # target_column seria Conteudo.titulo
                        # O lambda para with_loader_criteria(Modulo.aulas, ...) precisaria fazer join com Conteudos.
                        # Isso requer uma construção de lambda dinâmica mais elaborada.
                        # Por enquanto, vamos apenas logar, pois o seu caso de uso é o simples.
                        logger.warning(
                            f"Filtragem de conteúdo de coleção aninhada profunda para '{field_specifier}' "
                            f"via with_loader_criteria não é automaticamente construída. "
                            f"O filtro principal será aplicado, mas a coleção '{instrumented_relationship_on_model_cls.key}' "
                            f"pode não ser filtrada profundamente se a condição estiver em uma sub-relação."
                        )

            except Exception as e:
                logger.error(f"Erro ao aplicar operador '{op_code}' com valor '{value}' no campo '{field_specifier}': {e}")
                raise ValueError(f"Erro ao aplicar filtro '{op_code}={value}' para '{field_specifier}': {e}") from e
    return query


def apply_sorting(
    query: Select,
    model_cls: Type,
    sort_by: str,
    sort_dir: Optional[Literal["asc", "desc"]],
    relations_map: Dict[str, RelationshipProperty]
    # Poderia receber `already_joined_relationships` se quisesse otimizar
    # e não depender apenas do SQLAlchemy para não duplicar joins estruturalmente idênticos.
) -> Select:

    if not sort_by:
        return query

    direction = sort_dir.lower() if sort_dir else "asc"
    if direction not in ("asc", "desc"):
        raise ValueError(f"Direção de ordenação inválida: '{sort_dir}'. Use 'asc' ou 'desc'.")

    try:
        target_column, _, joins_to_apply = _get_column_or_relationship(
            model_cls, sort_by, relations_map
        )
    except ValueError as e:
        logger.error(f"Erro ao processar ordenação por '{sort_by}': {e}")
        raise

    # O SQLAlchemy geralmente é inteligente o suficiente para não adicionar um JOIN
    # se um JOIN estruturalmente idêntico (mesma tabela de destino, mesma condição ON)
    # já existe na query. Então, para a ordenação, podemos simplesmente tentar adicioná-los.
    # Se `apply_filters` já adicionou `chat_aluno`, o SQLAlchemy deve reutilizá-lo aqui.
    for rel_prop in joins_to_apply:
         logger.debug(f"Garantindo JOIN para ordenação na relação: {rel_prop} (originado por sort_by='{sort_by}')")
         query = query.join(rel_prop.class_attribute, isouter=True) # Use rel_prop.class_attribute


    order_func = asc if direction == "asc" else desc
    query = query.order_by(order_func(target_column))
    logger.debug(f"Aplicando ordenação: {order_func(target_column)}")

    return query

def apply_search(
    query: Select,
    model_cls: Type,
    search: Optional[str],
    search_fields: List[str],
) -> Select:
    """Aplica busca textual (case-insensitive) em campos específicos, incluindo propriedades de relacionamentos."""
    if not search or not search_fields:
        return query

    search_term = f"%{search}%"
    conditions = []
    mapper = inspect(model_cls)
    joins_added = set()  # Controla joins para evitar duplicatas

    for field_name in search_fields:
        # Verifica campos com notação de ponto (ex: 'voucher.codigo_voucher')
        if '.' in field_name:
            rel_name, rel_field = field_name.split('.', 1)
            
            # Verifica se o relacionamento existe
            if rel_name not in mapper.relationships:
                logger.warning(f"Relacionamento '{rel_name}' não encontrado em {model_cls.__name__}")
                continue
                
            relationship = mapper.relationships[rel_name]
            if not isinstance(relationship, RelationshipProperty):
                continue
                
            # Adiciona JOIN se necessário
            if rel_name not in joins_added:
                query = query.join(getattr(model_cls, rel_name))
                joins_added.add(rel_name)
            
            # Obtém o modelo relacionado e verifica o campo
            related_model = relationship.mapper.class_
            related_mapper = inspect(related_model)
            
            if rel_field not in related_mapper.columns and rel_field not in related_mapper.synonyms:
                logger.warning(f"Campo '{rel_field}' não encontrado em {related_model.__name__}")
                continue
                
            column = getattr(related_model, rel_field)
            if hasattr(column.type, "python_type") and issubclass(column.type.python_type, str):
                conditions.append(column.ilike(search_term))
            else:
                logger.warning(f"Campo '{field_name}' não é string, ignorando")
                
        # Campo local (não relacional)
        else:
            if field_name not in mapper.columns and field_name not in mapper.synonyms:
                logger.warning(f"Campo local '{field_name}' não encontrado")
                continue
                
            column = getattr(model_cls, field_name)
            if hasattr(column.type, "python_type") and issubclass(column.type.python_type, str):
                conditions.append(column.ilike(search_term))
            else:
                logger.warning(f"Campo local '{field_name}' não é string, ignorando")

    if conditions:
        query = query.filter(or_(*conditions))
        logger.debug(f"Busca aplicada: termo='{search}' em campos={search_fields}")

    return query

def parse_select_fields_for_pydantic(select_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Converte uma string de seleção (ex: "id,nome,curso.[categorias].id")
    em um dicionário para o argumento `include` do Pydantic model_dump,
    suportando aninhamento e sintaxe de lista `[...]` em qualquer nível.
    """
    if not select_str:
        return None

    fields_to_process: List[str] = [field.strip() for field in select_str.split(',') if field.strip()]
    if not fields_to_process:
        return None

    include_dict: Dict[str, Any] = {}
    
    list_part_regex = re.compile(r"\[([a-zA-Z0-9_]+)\]")

    for field_path in fields_to_process:
        parts = field_path.split('.')
        current_level = include_dict

        for i, part in enumerate(parts):
            is_last_part = (i == len(parts) - 1)
            
            list_match = list_part_regex.fullmatch(part)

            if list_match:
                list_name = list_match.group(1)

                if not isinstance(current_level.get(list_name), dict):
                    current_level[list_name] = {}
                
                list_container = current_level[list_name]

                if not isinstance(list_container.get('__all__'), dict):
                     list_container['__all__'] = {}

                if is_last_part:
                    list_container['__all__'] = True
                    break 
                else:
                    current_level = list_container['__all__']

            else: 
                if is_last_part:
                    if not isinstance(current_level.get(part), dict):
                        current_level[part] = True
                else:
                    if not isinstance(current_level.get(part), dict):
                        current_level[part] = {}
                    current_level = current_level[part]

    logger.debug(f"Estrutura 'include' parseada para Pydantic: {include_dict}")
    return include_dict if include_dict else None

def apply_select_load_options(
    query: Select,
    model_cls: Type,
    include_param: Optional[str] = None,
) -> Select:
    """
    Aplica opções de carregamento (selectinload, noload) à query SQLAlchemy
    com base no parâmetro 'include'.

    Por PADRÃO, relacionamentos NÃO são carregados para máxima performance.
    Apenas relacionamentos explicitamente mencionados no include são carregados.

    Args:
        select_param: String de include como "[tenants].nome,[roles].nome"

    Comportamento:
    - Sem include: todos relacionamentos são bloqueados (noload)
    - Com include: apenas relacionamentos especificados são carregados (selectinload)
    """
    model_inspector = sa_inspect(model_cls)
    model_relation_keys = {r.key for r in model_inspector.relationships}

    # Extrair relacionamentos solicitados
    relations_to_load = extract_relationships_from_select_hybrid(include_param, model_relation_keys)

    options_to_apply: List[Load] = []

    # ✅ CORREÇÃO: Aplicar selectinload para relacionamentos solicitados, noload para o resto
    for rel_name in model_relation_keys:
        rel_attr = getattr(model_cls, rel_name)

        if rel_name in relations_to_load:
            # Relacionamento solicitado: usar selectinload
            options_to_apply.append(selectinload(rel_attr))
            logger.debug(f"Carregando relacionamento: {model_cls.__name__}.{rel_name}")
        else:
            # Relacionamento NÃO solicitado: usar noload
            options_to_apply.append(noload(rel_attr))
            logger.debug(f"Bloqueando relacionamento: {model_cls.__name__}.{rel_name}")

    if options_to_apply:
        query = query.options(*options_to_apply)
        logger.debug(
            f"Aplicando {len(options_to_apply)} opções de carregamento para {model_cls.__name__}"
        )

    return query

# Em utils_bd.py ou no seu service base
def get_dynamic_relations_map(model_cls: Type) -> Dict[str, RelationshipProperty]:
    """Gera o relations_map dinamicamente para um modelo."""
    mapper = sa_inspect(model_cls)
    return {
        rel.key: rel.property # rel é InspectionAttr, rel.property é a RelationshipProperty
        for rel in mapper.relationships
    }
    
def get_validated_load_options(
    model_cls: Type,
    relations_map: Dict[str, RelationshipProperty],
    include: List[str]
) -> List[Load]:
    """
    Valida os nomes das relações em 'include' e retorna as opções de carregamento SQLAlchemy.

    Args:
        model_cls: A classe do modelo SQLAlchemy base.
        relations_map: Mapa de nomes de relação para atributos de relação do model_cls base.
        include: Lista de nomes de string das relações a serem carregadas (ex: ["users", "tasks"]).

    Returns:
        Uma lista de opções SQLAlchemy Load (geralmente selectinload).

    Raises:
        ValueError: Se algum nome em 'include' não for uma relação válida no 'relations_map'.
    """
    load_options: List[Load] = []
    invalid_includes = []

    if not include:
        return []

    for relation_name in include:
        if relation_name in relations_map:
            relation_attr = relations_map[relation_name]
            # Usa selectinload por padrão para relações to-many, que é geralmente mais eficiente
            # Pode ser trocado por joinedload se houver um motivo específico
            load_options.append(selectinload(relation_attr))
            logger.debug(f"Adicionando opção de carregamento: selectinload({model_cls.__name__}.{relation_name})")
        else:
            invalid_includes.append(relation_name)

    if invalid_includes:
        valid_options = list(relations_map.keys())
        raise ValueError(f"Relação(ões) inválida(s) fornecida(s) para 'include': {', '.join(invalid_includes)}. Relações válidas para {model_cls.__name__}: {valid_options}")

    return load_options

def extract_relationships_from_select_hybrid(
    select_param: Optional[str],
    model_relation_keys: Set[str]
) -> Set[str]:
    """
    Extrai nomes de relacionamentos da string 'select', suportando a nova sintaxe
    com colchetes `[relacao]` e a sintaxe antiga `relacao.campo`.

    Args:
        select_param: String como "[tenants].nome,roles.nome,id,email"
        model_relation_keys: Um set com os nomes das relações válidas no modelo.

    Returns:
        Set com os nomes dos relacionamentos: {"tenants", "roles"}
    """
    if not select_param:
        return set()

    relationships = set()
    raw_fields = [field.strip() for field in select_param.split(",") if field.strip()]

    for field_path in raw_fields:
        # Nova Sintaxe: [relation_name]...
        if field_path.startswith("[") and "]" in field_path:
            relation_match = re.match(r"\[([^\]]+)\]", field_path)
            if relation_match:
                relationships.add(relation_match.group(1))
        else:
            # Sintaxe Antiga: relation_name.subfield
            base_name = field_path.split('.')[0]
            if base_name in model_relation_keys:
                relationships.add(base_name)

    return relationships


def format_relative_time(date: datetime) -> str:
    """
    Formata uma data para formato relativo em português.
    
    Args:
        date: Data a ser formatada
        
    Returns:
        String formatada como "há X dias", "há X semana(s)", etc.
    """
    if not date:
        return "nunca"
    
    # Garantir que a data está em UTC se não tiver timezone
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - date
    
    # Se for no futuro, retorna "agora"
    if diff.total_seconds() < 0:
        return "agora"
    
    # Calcular diferenças
    total_seconds = int(diff.total_seconds())
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60
    total_days = total_hours // 24
    total_weeks = total_days // 7
    total_months = total_days // 30
    total_years = total_days // 365
    
    # Retornar formato apropriado
    if total_seconds < 60:
        return "agora"
    elif total_minutes < 60:
        return f"há {total_minutes} minuto{'s' if total_minutes != 1 else ''}"
    elif total_hours < 24:
        return f"há {total_hours} hora{'s' if total_hours != 1 else ''}"
    elif total_days < 7:
        return f"há {total_days} dia{'s' if total_days != 1 else ''}"
    elif total_weeks < 4:
        return f"há {total_weeks} semana{'s' if total_weeks != 1 else ''}"
    elif total_months < 12:
        return f"há {total_months} mês{'es' if total_months != 1 else ''}"
    else:
        return f"há {total_years} ano{'s' if total_years != 1 else ''}"