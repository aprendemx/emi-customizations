"""
Settings de producción. Hereda de common y permite sobrescribir desde
la configuración del entorno.
"""

from .common import plugin_settings as common_settings


def plugin_settings(settings):
    common_settings(settings)
    settings.EMI_CATALOG_SORT_BY_DISPLAY_NAME = settings.ENV_TOKENS.get(
        "EMI_CATALOG_SORT_BY_DISPLAY_NAME",
        settings.EMI_CATALOG_SORT_BY_DISPLAY_NAME,
    )
