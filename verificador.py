"""
Agente Verificador — pero NO es otro LLM.

Un "verificador" implementado como otro modelo generativo tiene el mismo
problema que quiere resolver: puede alucinar su propia verificación. En vez
de eso, este es un chequeo determinista en Python: extrae cada número que
aparece en la respuesta final del agente y confirma que también aparece en
alguno de los resultados crudos que devolvieron las tools durante esa misma
conversación. Si no puede verificar algo, lo señala — nunca lo borra ni lo
corrige por su cuenta (eso sería una alucinación silenciosa distinta).
"""
import re

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def verificar_respuesta(respuesta: str, tool_outputs: list[str]) -> str:
    if not tool_outputs:
        # El agente no llamó ninguna tool (ej. dijo "no encontré nada") — nada que verificar.
        return respuesta

    fuente = "\n".join(str(o) for o in tool_outputs)
    numeros_respuesta = set(_NUM_RE.findall(respuesta))
    numeros_fuente = set(_NUM_RE.findall(fuente))

    no_verificados = sorted(numeros_respuesta - numeros_fuente)
    if not no_verificados:
        return respuesta

    return (
        respuesta
        + "\n\n⚠️ Nota de verificación: no pude confirmar contra los datos del grafo "
        + f"el/los siguiente(s) número(s) mencionados arriba: {', '.join(no_verificados)}. "
        + "Tómalos con cautela."
    )
