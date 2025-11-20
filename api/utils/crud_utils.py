import logging
from typing import List, Optional, Dict, Any, Type, Literal, Tuple, Set
from sqlalchemy.orm import selectinload, Load, RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.selectable import Select
from sqlalchemy import asc, desc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def _get_column_or_relationship(
    model_cls: Type,
    field_specifier: str,
    relations_map: Dict[str, RelationshipProperty]
) -> Tuple[InstrumentedAttribute, Optional[Type], List[RelationshipProperty]]:
    """
    Obtém o atributo SQLAlchemy (coluna ou relação) correspondente a um especificador de campo.
    Retorna o atributo final, a classe do modelo onde ele está (se for relacionado) e a lista de joins necessários.

    Args:
        model_cls: A classe do modelo base.
        field_specifier: O nome do campo (ex: "name", "relation.field", "relation.sub_relation.field").
        relations_map: Mapa de nomes de string para atributos de relação do model_cls base.

    Returns:
        Uma tupla (atributo_final, classe_do_atributo, joins_necessarios).

    Raises:
        ValueError: Se o campo ou relação for inválido.
    """
    parts = field_specifier.split('.')
    current_model = model_cls
    target_attribute = None
    joins_needed: List[RelationshipProperty] = []

    for i, part in enumerate(parts):
        if not hasattr(current_model, part):
            raise ValueError(f"Modelo '{current_model.__name__}' não possui o atributo ou relação '{part}' especificado em '{field_specifier}'")

        attr = getattr(current_model, part)

        if isinstance(attr.property, RelationshipProperty):
            # É uma relação, precisamos avançar para o próximo modelo
            if i == len(parts) - 1:
                 # O último pedaço não pode ser a própria relação para filtros/sorts
                 raise ValueError(f"Não é possível filtrar/ordenar diretamente pela relação '{part}'. Especifique um campo dentro dela (ex: '{field_specifier}.id').")

            # Adiciona a relação à lista de joins necessários (usando o mapeamento original se for o primeiro nível)
            if i == 0:
                if part not in relations_map:
                     raise ValueError(f"Relação '{part}' não encontrada no 'relations_map' fornecido para o modelo base {model_cls.__name__}.")
                joins_needed.append(relations_map[part])
            else:
                # Para relações aninhadas, usamos o atributo diretamente
                 joins_needed.append(attr) # Adiciona o atributo de relação SQLAlchemy

            current_model = attr.property.mapper.class_ # Avança para a classe relacionada
        elif isinstance(attr, InstrumentedAttribute):
            # É uma coluna (ou similar), chegamos ao fim
            if i != len(parts) - 1:
                raise ValueError(f"Atributo '{part}' em '{field_specifier}' não é uma relação, mas existem mais partes.")
            target_attribute = attr
            break # Encontramos a coluna final
        else:
            raise ValueError(f"Atributo '{part}' em '{field_specifier}' tem tipo inesperado: {type(attr)}")

    if target_attribute is None:
         raise ValueError(f"Não foi possível resolver o atributo final para '{field_specifier}'.")

    return target_attribute, current_model, joins_needed


def apply_filters(
    query: Select,
    model_cls: Type,
    filter_params: Dict[str, Dict[str, Any]],
    relations_map: Dict[str, RelationshipProperty],
    # is_count: bool = False # Otimização para contagem pode ser complexa, omitida por simplicidade inicial
) -> Select:
    """
    Aplica filtros dinâmicos a uma query SQLAlchemy baseada em um dicionário de parâmetros.

    Args:
        query: A query SQLAlchemy (Select) a ser modificada.
        model_cls: A classe do modelo SQLAlchemy base da query.
        filter_params: Dicionário de filtros. Ex: {'name': {'ilike': '%test%'}, 'relation.status': {'eq': 'active'}}
        relations_map: Mapa de nomes de relação para atributos de relação do model_cls base.
        # is_count: Flag indicando se esta query é para contagem (pode otimizar joins).

    Returns:
        A query SQLAlchemy com os filtros aplicados.

    Raises:
        ValueError: Se um filtro for inválido (campo, operador ou valor).
    """
    applied_joins: Set[RelationshipProperty] = set() # Rastreia joins já aplicados

    for field_specifier, operators in filter_params.items():
        if not isinstance(operators, dict):
            raise ValueError(f"Valor para o filtro '{field_specifier}' deve ser um dicionário de operadores. Recebido: {operators}")

        try:
            # Obtém a coluna/atributo alvo e os joins necessários
            target_column, target_model_cls, joins_to_apply = _get_column_or_relationship(
                model_cls, field_specifier, relations_map
            )
        except ValueError as e:
            logger.error(f"Erro ao processar filtro para '{field_specifier}': {e}")
            raise # Re-lança o erro para o service layer tratar

        # Adiciona os joins necessários se ainda não foram aplicados
        current_join_target = model_cls # Começa do modelo base
        for rel_prop in joins_to_apply:
            # Verifica se o join *deste nível específico* já foi feito
            # SQLAlchemy pode reutilizar joins, mas rastrear explicitamente pode ser mais claro
            # if rel_prop not in applied_joins: # TODO: Refinar lógica de join se necessário
            # Usamos isouter=True para garantir que filtros em relações não excluam
            # registros principais que não têm a relação correspondente (comportamento LEFT JOIN)
            query = query.join(rel_prop, isouter=True)
            applied_joins.add(rel_prop)
            # current_join_target = rel_prop.mapper.class_ # Atualiza para o próximo nível (não usado no momento)


        # Aplica cada operador para o campo atual
        for op_code, value in operators.items():
            op_func = OPERATOR_MAP.get(op_code.lower())
            if not op_func:
                raise ValueError(f"Operador de filtro inválido '{op_code}' para o campo '{field_specifier}'. Válidos: {list(OPERATOR_MAP.keys())}")

            try:
                # TODO: Adicionar conversão de tipo para 'value' se necessário, baseado em target_column.type
                # Ex: if isinstance(target_column.type, String): value = str(value) etc.
                # Por enquanto, assume que o valor já está no tipo correto vindo da camada do router/parser.

                # Tratamento especial para 'in' e 'notin' que esperam listas/tuplas
                if op_code.lower() in ('in', 'notin') and not isinstance(value, (list, tuple)):
                     # Tenta converter string separada por vírgula em lista
                     if isinstance(value, str):
                         value = [item.strip() for item in value.split(',') if item.strip()]
                     else:
                         raise ValueError(f"Valor para operador '{op_code}' no campo '{field_specifier}' deve ser uma lista/tupla ou string separada por vírgulas.")

                filter_expression = op_func(target_column, value)
                query = query.where(filter_expression) # Aplica a condição WHERE/AND
                logger.debug(f"Aplicando filtro: {filter_expression}")

            except Exception as e:
                logger.error(f"Erro ao aplicar operador '{op_code}' com valor '{value}' no campo '{field_specifier}': {e}")
                # Fornece mais contexto no erro
                raise ValueError(f"Erro ao aplicar filtro '{op_code}={value}' para '{field_specifier}': {e}") from e

    return query


def apply_sorting(
    query: Select,
    model_cls: Type,
    sort_by: str,
    sort_dir: Optional[Literal["asc", "desc"]],
    relations_map: Dict[str, RelationshipProperty]
) -> Select:
    """
    Aplica ordenação dinâmica a uma query SQLAlchemy.

    Args:
        query: A query SQLAlchemy (Select) a ser modificada.
        model_cls: A classe do modelo SQLAlchemy base da query.
        sort_by: O nome do campo para ordenar (ex: "name", "relation.field").
        sort_dir: A direção da ordenação ("asc" ou "desc").
        relations_map: Mapa de nomes de relação para atributos de relação do model_cls base.

    Returns:
        A query SQLAlchemy com a ordenação aplicada.

    Raises:
        ValueError: Se o campo de ordenação ou direção for inválido.
    """
    if not sort_by:
        return query # Nenhuma ordenação a aplicar

    direction = sort_dir.lower() if sort_dir else "asc"
    if direction not in ("asc", "desc"):
        raise ValueError(f"Direção de ordenação inválida: '{sort_dir}'. Use 'asc' ou 'desc'.")

    try:
        # Obtém a coluna/atributo alvo e os joins necessários
        target_column, _, joins_to_apply = _get_column_or_relationship(
            model_cls, sort_by, relations_map
        )
    except ValueError as e:
        logger.error(f"Erro ao processar ordenação por '{sort_by}': {e}")
        raise # Re-lança o erro

    # Adiciona os joins necessários se ainda não estiverem na query (SQLAlchemy pode ser inteligente aqui)
    # Reaplicar joins aqui garante que eles existam para a ordenação
    for rel_prop in joins_to_apply:
         # Usamos isouter=True para consistência com filtros, embora para sort pode não ser estritamente necessário
         query = query.join(rel_prop, isouter=True)


    # Aplica a ordenação
    order_func = asc if direction == "asc" else desc
    query = query.order_by(order_func(target_column))
    logger.debug(f"Aplicando ordenação: {order_func(target_column)}")

    return query


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
            
            # For Aula.aulas_livros specifically, skip to avoid conflict
            if model_cls.__name__ == 'Aula' and relation_name == 'aulas_livros':
                logger.debug(f"Skipping selectinload for {model_cls.__name__}.{relation_name} - known conflict")
                continue
                
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