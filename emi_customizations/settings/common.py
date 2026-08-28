"""
Valores por defecto. Se pueden sobrescribir desde un plugin de Tutor sin
reconstruir la imagen.
"""


def plugin_settings(settings):
    """
    Open edX llama a esta función al cargar los settings del LMS.
    """
    # Ordena el catálogo alfabéticamente por nombre, con orden natural
    # (A1, A1+, A2, A2+, B1...). EMI nombra sus cursos por nivel de idioma.
    #
    # Sustituye a sort_by_start_date, así que ENABLE_COURSE_SORTING_BY_START_DATE
    # debe seguir en True para que la vista index() llame a la función.
    settings.EMI_CATALOG_SORT_BY_DISPLAY_NAME = True
