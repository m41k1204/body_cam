import json
from textwrap import dedent

def generate_prompt(texto: str, palabras: list[str]) -> str:
    """
    Devuelve un prompt preparado para el esquema messages-v1 de Bedrock.
    Retorna SOLO el contenido del mensaje de usuario.
    """
    ejemplos = [
        {
            "texto": "Oficial, podemos arreglar esto aquí entre nosotros con un café.",
            "esperado": {"corrupcion": True, "evidence": "podemos arreglar esto aquí", "confidence": 0.95}
        },
        {
            "texto": "Buenas noches, documentos por favor. Todo en orden, puede continuar.",
            "esperado": {"corrupcion": False, "evidence": "", "confidence": 0.05}
        }
    ]

    ejemplos_str = "\n".join(
        [f"### Ejemplo {i+1}\nTexto: \"{e['texto']}\"\nJSON esperado:\n{json.dumps(e['esperado'], ensure_ascii=False)}"
         for i, e in enumerate(ejemplos)]
    )

    user_content = dedent(f"""
        Tarea:
        Analiza el siguiente diálogo o descripción de una intervención policial de tráfico y
        determina si existe un acto o intento de corrupción.

        Definición operativa de corrupción:
        - Petición u ofrecimiento de dinero, favores, regalos o influencia para alterar el procedimiento.
        - Amenazas o extorsión para obtener ventaja económica o evitar sanciones.
        - Cualquier forma de soborno, coima, “arreglo” o aprovechamiento indebido.

        Palabras clave comunes (no limitantes):
        {json.dumps(palabras, ensure_ascii=False)}

        Instrucciones:
        1. Lee el texto completo.
        2. Si hay indicios de corrupción según la definición, marca "corrupcion": true. 
        3. Extrae la frase exacta o fragmento que lo demuestra en "evidence".
        4. Asigna "confidence" en rango 0-1 (probabilidad subjetiva).
        5. Si no hay indicios, usa "corrupcion": false y deja "evidence" vacío.
        6. Responde ÚNICAMENTE con un JSON válido que siga este esquema:
           {{"corrupcion": bool, "evidence": str, "confidence": float}}

        Validación:
        - Si no puedes producir un JSON válido, responde exactamente: ERROR

        {ejemplos_str}

        ### Texto a evaluar
        \"\"\"{texto}\"\"\"

        ### JSON:
    """)

    return user_content
