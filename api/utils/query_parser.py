import re
import logging
from typing import Dict, Any
from starlette.datastructures import QueryParams

logger = logging.getLogger(__name__)

FILTER_PATTERN = re.compile(r"filter\[(.+?)\]\[(.+?)\]")

def _parse_filter_value(value: str) -> Any:
    value_lower = value.lower()
    if value_lower in ('true', 'yes', 'on', '1'):
        return True
    if value_lower in ('false', 'no', 'off', '0'):
        return False
    if value_lower in ('null', 'none'):
        return None
    return value 


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

'''
if __name__ == '__main__':
    from starlette.datastructures import QueryParams

    # Test cases
    test_params_1 = QueryParams("filter[name][ilike]=%test%&filter[status][eq]=active&skip=0&limit=10")
    test_params_2 = QueryParams("filter[count][gte]=10&filter[is_deleted][eq]=false&filter[created_at][lt]=2023-01-01")
    test_params_3 = QueryParams("filter[relation.field][neq]=some_value&filter[another_field][isnull]=true")
    test_params_4 = QueryParams("filter[tags][in]=python,fastapi&filter[id][eq]=123") # 'in' com vírgula
    test_params_5 = QueryParams("invalid_filter=abc&filter[name]invalid=test") # Inválidos
    test_params_6 = QueryParams("") # Vazio

    print("--- Teste 1 ---")
    print(parse_filters(test_params_1))
    # Esperado: {'name': {'ilike': '%test%'}, 'status': {'eq': 'active'}}

    print("\n--- Teste 2 ---")
    print(parse_filters(test_params_2))
    # Esperado: {'count': {'gte': '10'}, 'is_deleted': {'eq': False}, 'created_at': {'lt': '2023-01-01'}}

    print("\n--- Teste 3 ---")
    print(parse_filters(test_params_3))
    # Esperado: {'relation.field': {'neq': 'some_value'}, 'another_field': {'isnull': True}}

    print("\n--- Teste 4 ---")
    print(parse_filters(test_params_4))
    # Esperado: {'tags': {'in': 'python,fastapi'}, 'id': {'eq': '123'}}

    print("\n--- Teste 5 ---")
    print(parse_filters(test_params_5))
    # Esperado: {}

    print("\n--- Teste 6 ---")
    print(parse_filters(test_params_6))
    # Esperado: {}
'''