"""
Agente Verificador — pero NO es otro LLM.

Un "verificador" implementado como otro modelo generativo tiene el mismo
problema que quiere resolver: puede alucinar su propia verificación. En vez
de eso, este es un chequeo determinista en Python.

Dos capas de chequeo:
1. Números sueltos: cada número en la respuesta debe aparecer en algún
   resultado crudo de tool. Detecta datos inventados en general.
2. Marcadores de partido (ej. "3-3"): un número puede existir legítimamente
   en la fuente por separado (un "3" de un partido, un "0" de otro) sin que
   la COMBINACIÓN "3-3" como marcador exista en ningún partido real. Esto
   fue justo el bug real que encontramos: el Narrador fusionó el marcador
   de un partido de fase de grupos con el de la final, inventando "3-3" que
   no corresponde a ningún partido — cada dígito individual sí aparecía en
   la fuente (por separado), así que el chequeo de números sueltos no lo
   atrapaba solo.
"""
import re

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_SCORE_RE = re.compile(r"\b(\d{1,2})\s*[-–a]\s*(\d{1,2})\b")
_LIST_MARKER_RE = re.compile(r"(?m)^\s*\d+\.\s+")


def _quitar_numeracion_de_lista(texto: str) -> str:
    """
    Quita marcadores de lista tipo '1. ', '2. ' al inicio de línea antes de
    buscar números a verificar — son formato de presentación (el modelo
    enumerando su propia respuesta), no un dato que venga de una tool.
    Sin esto, un '1.' de lista se marcaba como 'número no verificado' aunque
    la respuesta fuera perfecta.
    """
    return _LIST_MARKER_RE.sub("", texto)


def _pares_marcador(texto: str) -> set[tuple[str, str]]:
    return {tuple(sorted(par)) for par in _SCORE_RE.findall(texto)}


def verificar_respuesta(respuesta: str, tool_outputs: list[str]) -> str:
    if not tool_outputs:
        # El agente no llamó ninguna tool (ej. dijo "no encontré nada") — nada que verificar.
        return respuesta

    fuente = "\n".join(str(o) for o in tool_outputs)

    # Capa 1: números sueltos (ignorando numeración de lista tipo '1. ')
    numeros_respuesta = set(_NUM_RE.findall(_quitar_numeracion_de_lista(respuesta)))
    numeros_fuente = set(_NUM_RE.findall(fuente))
    no_verificados = sorted(numeros_respuesta - numeros_fuente)

    # Capa 2: marcadores de partido (la combinación de los dos números juntos)
    marcadores_respuesta = _pares_marcador(respuesta)
    marcadores_fuente = _pares_marcador(fuente)
    marcadores_inventados = sorted(marcadores_respuesta - marcadores_fuente)

    avisos = []
    if no_verificados:
        avisos.append(
            "no pude confirmar contra los datos del grafo el/los siguiente(s) "
            f"número(s) mencionados arriba: {', '.join(no_verificados)}"
        )
    if marcadores_inventados:
        marcadores_txt = ", ".join(f"{a}-{b}" for a, b in marcadores_inventados)
        avisos.append(
            f"el/los marcador(es) {marcadores_txt} no coinciden con ningún partido "
            "real de los datos consultados — podría ser un resultado inventado o "
            "la mezcla de dos partidos distintos"
        )

    if not avisos:
        return respuesta

    return (
        respuesta
        + "\n\n⚠️ Nota de verificación: "
        + "; y ".join(avisos)
        + ". Tómalo con cautela."
    )
