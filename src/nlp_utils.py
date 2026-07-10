# -*- coding: utf-8 -*-
"""
nlp_utils.py
Modulo de Procesamiento de Lenguaje Natural (PLN) Basico.

Responsable de:
  1. Normalizar el texto de entrada del usuario (minusculas, sin tildes,
     sin signos de puntuacion).
  2. Eliminar palabras vacias (stop words) en espanol.
  3. Tokenizar la consulta en palabras clave utiles.
  4. Clasificar la intencion comparando los tokens contra las palabras
     clave de cada FAQ en la base de conocimiento (busqueda por
     coincidencia de palabras clave + puntaje de similitud simple).

Segundo Avance - Agente Virtual Guia para Orientacion Universitaria (UTH)
"""

import re
import unicodedata

# Stop words en espanol (lista basica para este proyecto)
STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "al", "a", "en", "y", "o", "que", "es", "son", "para", "por", "con",
    "sin", "se", "su", "sus", "mi", "mis", "tu", "tus", "yo", "como",
    "donde", "cual", "cuales", "cuando", "quien", "quienes", "este",
    "esta", "estos", "estas", "ese", "esa", "esos", "esas", "lo", "le",
    "les", "me", "te", "nos", "ya", "muy", "mas", "pero", "si", "no",
    "puedo", "puedes", "tengo", "tiene", "hay", "soy", "eres", "esta",
    "estoy", "ser", "fue", "ha", "he", "han",
    "universidad", "institucion", "ofrecen", "ofrece"
}


def quitar_tildes(texto: str) -> str:
    """Convierte caracteres acentuados a su forma base (ej. 'á' -> 'a')."""
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto de entrada:
      - Convierte a minusculas
      - Elimina tildes/acentos
      - Elimina signos de puntuacion y caracteres especiales
      - Colapsa espacios multiples
    """
    texto = texto.lower()
    texto = quitar_tildes(texto)
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto: str) -> list:
    """
    Tokeniza el texto normalizado y elimina las stop words,
    devolviendo solo las palabras clave relevantes para la busqueda.
    """
    texto_normalizado = normalizar_texto(texto)
    tokens = texto_normalizado.split(" ") if texto_normalizado else []
    tokens_limpios = [t for t in tokens if t and t not in STOP_WORDS]
    return tokens_limpios


def _prefijo_comun(a: str, b: str) -> int:
    """Longitud del prefijo comun mas largo entre dos cadenas."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def calcular_puntaje(tokens_usuario: list, palabras_clave_faq: list) -> int:
    """
    Calcula un puntaje de coincidencia entre los tokens del usuario y las
    palabras clave asociadas a una FAQ.

    Reglas:
      +3 puntos por cada token del usuario que coincide EXACTAMENTE con
         un token de la palabra clave (senal fuerte).
      +3 puntos de bono si una frase clave de varias palabras coincide
         por completo (todas sus palabras presentes en la consulta).
      +1 punto por coincidencia parcial tipo prefijo, solo cuando el
         prefijo compartido es de al menos 5 caracteres y ese token clave
         no tuvo ya una coincidencia exacta (evita falsos positivos entre
         palabras cortas distintas, ej. 'queda' no debe activar frases que
         solo comparten esa palabra incidental).
    """
    puntaje = 0
    set_tokens_usuario = set(tokens_usuario)

    for frase_clave in palabras_clave_faq:
        tokens_clave = tokenizar(frase_clave)
        if not tokens_clave:
            continue

        coincidencias_exactas = [tk for tk in tokens_clave if tk in set_tokens_usuario]
        puntaje += 3 * len(coincidencias_exactas)

        if len(tokens_clave) > 1 and len(coincidencias_exactas) == len(tokens_clave):
            puntaje += 3  # bono por frase clave completa

        tokens_clave_restantes = [tk for tk in tokens_clave if tk not in set_tokens_usuario]
        for tu in set_tokens_usuario:
            for tk in tokens_clave_restantes:
                if _prefijo_comun(tu, tk) >= 5:
                    puntaje += 1

    return puntaje


def es_comando_transferencia(texto: str) -> bool:
    """
    Detecta peticiones explicitas de transferencia a un agente humano,
    segun los criterios de derivacion definidos en el primer avance.
    """
    comandos = {"humano", "asesor", "soporte", "agente", "persona", "operador"}
    tokens = set(tokenizar(texto))
    frases_directas = ["hablar con un asesor", "hablar con un humano",
                        "quiero un humano", "necesito ayuda humana"]
    texto_norm = normalizar_texto(texto)
    if any(normalizar_texto(f) in texto_norm for f in frases_directas):
        return True
    return bool(tokens & comandos)
