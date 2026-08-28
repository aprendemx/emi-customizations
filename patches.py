"""
Sustitución de funciones de edx-platform.

Reemplaza lo que el fork `aprendemx/edx-platform` rama `emi/teak-platform`
hacía a mano en `common/djangoapps/student/views/management.py`: añadir una
función `sort_by_display_name` y un `elif` dentro de la vista `index()`.

--------------------------------------------------------------------------
POR QUÉ NO HACE FALTA TOCAR LA VISTA
--------------------------------------------------------------------------
La vista `index()` ya llama a `sort_by_start_date` cuando el flag
`ENABLE_COURSE_SORTING_BY_START_DATE` está activo — y en EMI lo está.

En vez de añadir una rama nueva a la vista (lo que obliga a forkear el core),
sustituimos esa función por una que ordena alfabéticamente. Mismo resultado
visible, cero modificaciones a edx-platform.

Consecuencia: el flag `ENABLE_COURSE_SORTING_BY_DISPLAY_NAME` que introducía
el fork deja de existir. El interruptor equivalente es
`EMI_CATALOG_SORT_BY_DISPLAY_NAME` (ver settings/common.py).

--------------------------------------------------------------------------
POR QUÉ HAY QUE PARCHEAR VARIOS MÓDULOS
--------------------------------------------------------------------------
Los llamadores usan `from ... import nombre`, lo que copia la referencia a la
función al namespace del llamador en tiempo de import. Reemplazar el atributo
solo en el módulo de origen NO afecta a quien ya tiene su propia referencia.

**Esta lista debe revisarse en cada actualización de Open edX.** Si una
versión nueva añade un llamador, el parche deja de cubrirlo en silencio.
Comando para regenerarla, sobre un clon de edx-platform:

    grep -rn "sort_by_start_date" --include="*.py" | grep -v "def sort_by"

Verificado contra release/teak.2. PENDIENTE de reverificar en Ulmo.
"""

import logging
import re
from importlib import import_module

from django.conf import settings

log = logging.getLogger(__name__)


def _patch_in_modules(module_paths, attr_name, new_func):
    """
    Sustituye `attr_name` por `new_func` en cada módulo de `module_paths`.

    Registra en el log cada sustitución y avisa si un módulo no expone el
    atributo esperado: eso significa que upstream cambió y el parche podría
    haber dejado de aplicarse donde hacía falta.
    """
    applied = []
    for path in module_paths:
        try:
            module = import_module(path)
        except ImportError:
            log.warning(
                "emi_customizations: no se pudo importar %s para parchear %s",
                path, attr_name,
            )
            continue

        if not hasattr(module, attr_name):
            log.warning(
                "emi_customizations: %s no expone %s. "
                "¿Cambió upstream? El parche NO se aplicó ahí.",
                path, attr_name,
            )
            continue

        setattr(module, attr_name, new_func)
        applied.append(path)

    log.info(
        "emi_customizations: %s parcheado en %d módulo(s): %s",
        attr_name, len(applied), ", ".join(applied) or "ninguno",
    )
    return applied


# ---------------------------------------------------------------------------
# Orden del catálogo por nombre
# ---------------------------------------------------------------------------
# EMI nombra sus cursos por nivel de idioma: A1, A1+, A2, A2+, B1, B1+...
# Un `sorted()` alfabético normal pondría "A10" antes que "A2", de ahí el
# ordenamiento natural que separa letras de números.

_CATALOG_SORT_MODULES = (
    "lms.djangoapps.courseware.courses",              # origen
    "lms.djangoapps.courseware.views.views",          # from ... import
    "common.djangoapps.student.views.management",     # from ... import (el que forkeaba EMI)
)


def _natural_sort_key(course):
    """
    Clave de orden que trata los números como números.

    "A1+", "A2", "A2+", "B1", "B1+" salen en ese orden; con un sorted()
    alfabético simple, "A10" iría antes que "A2".
    """
    display_name = course.display_name_with_default
    partes = re.split(r"([A-Za-z]+|\d+)", display_name)
    clave = []
    for parte in partes:
        if parte.isdigit():
            clave.append((1, int(parte), ""))
        else:
            # Tupla homogénea para que la comparación nunca mezcle tipos.
            clave.append((0, 0, parte.lower()))
    return clave


def sort_by_display_name(courses):
    """
    Ordena alfabéticamente por nombre de visualización, con orden natural.

    Sustituye a `sort_by_start_date`, que es la función que la vista `index()`
    llama cuando ENABLE_COURSE_SORTING_BY_START_DATE está activo.
    """
    return sorted(courses, key=_natural_sort_key)


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

def apply_all():
    """
    Aplica todos los parches habilitados. Llamado desde AppConfig.ready().
    """
    if getattr(settings, "EMI_CATALOG_SORT_BY_DISPLAY_NAME", True):
        _patch_in_modules(
            _CATALOG_SORT_MODULES, "sort_by_start_date", sort_by_display_name
        )
