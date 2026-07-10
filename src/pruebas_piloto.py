# -*- coding: utf-8 -*-
"""
pruebas_piloto.py
Script de pruebas con usuarios simulados para validar el funcionamiento
del motor del chatbot: clasificacion de intencion, manejo de consultas
ambiguas y derivacion por bucle de error.

Segundo Avance - Agente Virtual Guia para Orientacion Universitaria (UTH)

Ejecucion:
    python pruebas_piloto.py
Genera un reporte en consola y guarda logs en logs/auditoria_consultas.csv
"""

from chatbot_engine import ChatbotEngine

# Conjunto de consultas simuladas de usuarios (casos reales esperados +
# casos ambiguos + casos de transferencia)
CASOS_DE_PRUEBA = [
    # Caso, sesion, esperado (solo referencial para el reporte)
    ("¿Dónde pago la matrícula?", "user1", "INF01"),
    ("a que hora son las clases en la jornada matutina", "user2", "HOR02"),
    ("como hago la prematricula", "user3", "ACA02"),
    ("se me olvido mi clave del campus virtual", "user4", "SOP01"),
    ("donde estan los laboratorios de computo", "user5", "INF05"),
    ("cuantas materias puedo matricular", "user6", "ACA01"),
    ("ofrecen becas en la universidad", "user7", "SOP03"),
    ("necesito hablar con un asesor", "user8", "TRANSFERENCIA"),
    ("xkjasldjk asdkj", "user9", "SIN_RESULTADO"),     # consulta ambigua/sin sentido
    ("blablabla", "user9", "SIN_RESULTADO"),           # 2do intento fallido (misma sesion)
    ("no entiendo nada", "user9", "TRANSFERENCIA"),    # 3er intento -> bucle de error
    ("cual es el horario de registro", "user10", "HOR01"),
    ("donde queda la biblioteca", "user11", "INF04"),
    ("como solicito mi certificacion de notas", "user12", "ACA03"),
]


def ejecutar_pruebas():
    engine = ChatbotEngine()
    print("=" * 70)
    print(" PRUEBAS PILOTO CON USUARIOS SIMULADOS")
    print(f" Total de FAQs en base de conocimiento: {engine.total_faqs()}")
    print("=" * 70)

    aciertos = 0
    total = len(CASOS_DE_PRUEBA)

    for consulta, session_id, esperado in CASOS_DE_PRUEBA:
        resultado = engine.procesar_mensaje(consulta, session_id)
        faq_id = resultado.get("faq_id")
        tipo = resultado["tipo"]

        if tipo == "transferencia":
            obtenido = "TRANSFERENCIA"
        elif tipo == "sin_resultado":
            obtenido = "SIN_RESULTADO"
        else:
            obtenido = faq_id

        ok = "OK" if obtenido == esperado else "REVISAR"
        if ok == "OK":
            aciertos += 1

        print(f"[{ok:7}] Sesion={session_id:6} | Consulta: '{consulta}'")
        print(f"          Esperado={esperado} | Obtenido={obtenido}")
        print(f"          Respuesta del bot: {resultado['texto'][:90]}...")
        print("-" * 70)

    porcentaje = (aciertos / total) * 100
    print("=" * 70)
    print(f" RESULTADO FINAL: {aciertos}/{total} aciertos ({porcentaje:.1f}%)")
    print(" Los logs detallados se guardaron en logs/auditoria_consultas.csv")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_pruebas()
