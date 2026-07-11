# Agente Virtual - Orientación Universitaria (UTH)

## Estructura del proyecto

```
agente_uth/
├── src/
│   ├── nlp_utils.py        # Normalización, tokenización y stop words
│   ├── chatbot_engine.py   # Motor: sistema experto + clasificación + logs
│   ├── app_web.py          # Interfaz web (Flask) - chat en el navegador
│   ├── bot.py              # Integración con Telegram (mismo motor)
│   └── pruebas_piloto.py   # Pruebas con usuarios simulados
├── data/
│   └── knowledge_base.json # Base de conocimiento (31 FAQs, 4 categorías)
├── logs/
│   └── auditoria_consultas.csv  # Se genera automáticamente al usar el bot
└── docs/
    └── informes_parcial1,2.pdf
```

## Instalación

1. Clonar o descomprimir el proyecto.
2. Instalar dependencias:
   ```
   pip install flask
   pip install python-telegram-bot   # solo si se usará Telegram
   ```

## Ejecución — Interfaz Web (navegador)

```
cd src
python app_web.py
```

Abrir en el navegador: **http://127.0.0.1:5000**

## Ejecución — Telegram (opcional)

1. Crear un bot con [@BotFather](https://t.me/BotFather) en Telegram y
   obtener el token.
2. Configurar la variable de entorno:
   ```
   export TELEGRAM_BOT_TOKEN="tu_token_aqui"
   ```
3. Ejecutar:
   ```
   cd src
   python bot.py
   ```

## Ejecución — Pruebas piloto

```
cd src
python pruebas_piloto.py
```

Esto ejecuta 14 consultas simuladas (casos normales, ambiguos y de
transferencia) y reporta el porcentaje de aciertos. Resultado actual:
**14/14 (100%)**. Los resultados también quedan registrados en
`logs/auditoria_consultas.csv`.

## Notas técnicas

- El motor (`chatbot_engine.py`) es compartido entre la interfaz web y
  Telegram: una sola fuente de verdad para la base de conocimiento y la
  lógica de clasificación.
- Derivación a agente humano automática tras 3 intentos fallidos
  consecutivos (bucle de error), o ante petición explícita
  ("hablar con un asesor", "humano", "soporte").
- Cada consulta queda registrada en `logs/auditoria_consultas.csv` con:
  fecha/hora, sesión, consulta original, tokens detectados, FAQ asignada,
  categoría, puntaje de coincidencia y resultado.
