# -*- coding: utf-8 -*-
"""
chatbot_engine.py
Motor principal del Agente Virtual de Orientacion Universitaria (UTH).

Implementa:
  - Carga de la base de conocimiento (knowledge_base.json)
  - Clasificacion de intencion por palabras clave (motor de inferencia
    determinista / sistema experto basado en reglas)
  - Conteo de intentos fallidos consecutivos -> derivacion por "bucle de error"
  - Deteccion de peticion explicita de transferencia a humano
  - Registro de auditoria (logs) de cada consulta realizada

Segundo Avance - Agente Virtual Guia para Orientacion Universitaria (UTH)
"""

import json
import os
import csv
from datetime import datetime

from nlp_utils import tokenizar, calcular_puntaje, es_comando_transferencia

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "auditoria_consultas.csv")

UMBRAL_MINIMO = 3          # puntaje minimo para considerar una respuesta valida
INTENTOS_MAX_FALLO = 3     # bucle de error: 3 intentos fallidos consecutivos


class ChatbotEngine:
    def __init__(self, kb_path: str = KB_PATH, log_path: str = LOG_PATH):
        self.kb_path = kb_path
        self.log_path = log_path
        self.faqs = self._cargar_base_conocimiento()
        self._asegurar_log()
        # Contador de intentos fallidos consecutivos, por sesion
        self.fallos_consecutivos = {}

    # ------------------------------------------------------------------ #
    # Carga de datos
    # ------------------------------------------------------------------ #
    def _cargar_base_conocimiento(self) -> list:
        with open(self.kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("faqs", [])

    def _asegurar_log(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "session_id", "consulta_original",
                    "tokens_detectados", "faq_id_asignada", "categoria",
                    "puntaje", "resultado", "intentos_fallidos_sesion"
                ])

    def _registrar_log(self, session_id, consulta, tokens, faq_id,
                        categoria, puntaje, resultado, fallos):
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                session_id,
                consulta,
                " ".join(tokens),
                faq_id or "N/A",
                categoria or "N/A",
                puntaje,
                resultado,
                fallos
            ])

    # ------------------------------------------------------------------ #
    # Clasificacion de intencion (sistema experto basado en reglas)
    # ------------------------------------------------------------------ #
    def _buscar_mejor_faq(self, tokens: list):
        mejor_faq = None
        mejor_puntaje = 0
        for faq in self.faqs:
            puntaje = calcular_puntaje(tokens, faq["palabras_clave"])
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_faq = faq
        return mejor_faq, mejor_puntaje

    # ------------------------------------------------------------------ #
    # API publica
    # ------------------------------------------------------------------ #
    def procesar_mensaje(self, mensaje: str, session_id: str = "default") -> dict:
        """
        Procesa un mensaje de usuario y devuelve un diccionario con:
          - tipo: 'respuesta' | 'transferencia' | 'sin_resultado'
          - texto: respuesta a mostrar
          - faq_id, categoria (si aplica)
        """
        self.fallos_consecutivos.setdefault(session_id, 0)

        # 1. Peticion explicita de transferencia
        if es_comando_transferencia(mensaje):
            self.fallos_consecutivos[session_id] = 0
            self._registrar_log(session_id, mensaje, tokenizar(mensaje),
                                 None, None, 0, "transferencia_explicita", 0)
            return {
                "tipo": "transferencia",
                "texto": ("Te comunico con un agente humano. Canales de "
                          "atencion presencial: Edificio Principal, Oficina "
                          "de Registro. Horario: Lun-Vie 8:00 AM - 7:00 PM, "
                          "Sab 8:00 AM - 12:00 PM. Correo: "
                          "soporte@universidad.edu"),
                "faq_id": None,
                "categoria": None
            }

        # 2. Clasificacion por palabras clave
        tokens = tokenizar(mensaje)
        faq, puntaje = self._buscar_mejor_faq(tokens)

        if faq and puntaje >= UMBRAL_MINIMO:
            self.fallos_consecutivos[session_id] = 0
            self._registrar_log(session_id, mensaje, tokens, faq["id"],
                                 faq["categoria"], puntaje, "respondida", 0)
            return {
                "tipo": "respuesta",
                "texto": faq["respuesta"],
                "faq_id": faq["id"],
                "categoria": faq["categoria"]
            }

        # 3. No se encontro una intencion valida -> contar fallo
        self.fallos_consecutivos[session_id] += 1
        fallos = self.fallos_consecutivos[session_id]
        self._registrar_log(session_id, mensaje, tokens, None, None,
                             puntaje, "sin_resultado", fallos)

        if fallos >= INTENTOS_MAX_FALLO:
            self.fallos_consecutivos[session_id] = 0
            return {
                "tipo": "transferencia",
                "texto": ("No logre identificar tu consulta tras varios "
                          "intentos. Te transfiero con un agente humano. "
                          "Correo: soporte@universidad.edu | "
                          "Oficina de Registro, Lun-Vie 8:00 AM - 7:00 PM."),
                "faq_id": None,
                "categoria": None
            }

        return {
            "tipo": "sin_resultado",
            "texto": ("No logre entender tu consulta. ¿Podrias reformularla? "
                      "Tambien puedes escribir 'menu' para ver las "
                      "categorias disponibles, o 'asesor' para hablar con "
                      "una persona."),
            "faq_id": None,
            "categoria": None
        }

    def listar_categorias(self) -> list:
        categorias = []
        for faq in self.faqs:
            if faq["categoria"] not in categorias:
                categorias.append(faq["categoria"])
        return categorias

    def listar_faqs_por_categoria(self, categoria: str) -> list:
        return [f for f in self.faqs if f["categoria"].lower() == categoria.lower()]

    def total_faqs(self) -> int:
        return len(self.faqs)
