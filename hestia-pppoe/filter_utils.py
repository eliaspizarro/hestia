# filter_utils.py
# Utilidades de filtrado para el proyecto Hestia
# Todos los comentarios y documentación estarán en español.

from typing import List, Any

def filter_excluded(objetos: List[Any], lista_excluir: List[str], campo: str = None) -> List[Any]:
    """
    Filtra una lista de objetos (dict o str) excluyendo aquellos cuyo campo especificado
    coincide exactamente con algún valor de lista_excluir. Si campo es None, filtra el objeto directamente.
    """
    if campo:
        return [obj for obj in objetos if obj.get(campo) not in lista_excluir]
    else:
        return [obj for obj in objetos if obj not in lista_excluir]
