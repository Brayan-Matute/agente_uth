# -*- coding: utf-8 -*-
"""
app_web.py
Interfaz web (widget de chat) para el Agente Virtual de Orientacion
Universitaria. Ejecuta un servidor Flask local que sirve una pagina
con un chat interactivo, conectado al motor (chatbot_engine.py).

Segundo Avance - Agente Virtual Guia para Orientacion Universitaria (UTH)

Ejecucion:
    python app_web.py
Luego abrir en el navegador: http://127.0.0.1:5000
"""

import uuid
from flask import Flask, request, jsonify, render_template_string

from chatbot_engine import ChatbotEngine

app = Flask(__name__)
engine = ChatbotEngine()

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Asistente Universitario Virtual - UTH</title>
<style>
  :root {
    --azul: #163d6b;
    --azul-claro: #2e75b6;
    --gris-fondo: #f2f4f7;
    --burbuja-bot: #eef3f9;
    --burbuja-user: #2e75b6;
  }
  * { box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--gris-fondo);
    margin: 0;
    display: flex;
    justify-content: center;
    padding: 30px 12px;
  }
  .chat-container {
    width: 100%;
    max-width: 480px;
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.12);
    display: flex;
    flex-direction: column;
    height: 640px;
    overflow: hidden;
  }
  .chat-header {
    background: var(--azul);
    color: #fff;
    padding: 16px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .chat-header .avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: var(--azul-claro);
    display: flex; align-items: center; justify-content: center;
    font-weight: bold;
  }
  .chat-header .info b { display: block; font-size: 15px; }
  .chat-header .info span { font-size: 12px; opacity: 0.85; }
  .chat-messages {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .msg {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 14px;
    line-height: 1.4;
    white-space: pre-wrap;
  }
  .msg.bot {
    background: var(--burbuja-bot);
    color: #1a1a1a;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
  }
  .msg.user {
    background: var(--burbuja-user);
    color: #fff;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
  }
  .quick-replies {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 0 16px 10px 16px;
    max-height: 160px;
    overflow-y: auto;
  }
  .quick-replies button {
    background: #fff;
    border: 1px solid var(--azul-claro);
    color: var(--azul-claro);
    border-radius: 16px;
    padding: 6px 12px;
    font-size: 12.5px;
    cursor: pointer;
    text-align: left;
    max-width: 100%;
  }
  .quick-replies button:hover { background: var(--azul-claro); color: #fff; }
  .chat-input {
    display: flex;
    border-top: 1px solid #e3e6ea;
    padding: 10px;
    gap: 8px;
  }
  .chat-input input {
    flex: 1;
    border: 1px solid #d7dbe0;
    border-radius: 20px;
    padding: 10px 16px;
    font-size: 14px;
    outline: none;
  }
  .chat-input button {
    background: var(--azul-claro);
    color: #fff;
    border: none;
    border-radius: 20px;
    padding: 0 18px;
    font-size: 14px;
    cursor: pointer;
  }
  .chat-input button:hover { background: var(--azul); }
  .footer-note {
    text-align: center;
    font-size: 11px;
    color: #8a8f98;
    margin-top: 10px;
  }
</style>
</head>
<body>

<div>
  <div class="chat-container">
    <div class="chat-header">
      <div class="avatar">UV</div>
      <div class="info">
        <b>Asistente Universitario Virtual</b>
        <span>Orientacion para estudiantes - UTH</span>
      </div>
    </div>
    <div class="chat-messages" id="chatMessages"></div>
    <div class="quick-replies" id="quickReplies"></div>
    <div class="chat-input">
      <input type="text" id="userInput" placeholder="Escribe tu consulta..." autocomplete="off">
      <button onclick="enviarMensaje()">Enviar</button>
    </div>
  </div>
  <div class="footer-note">Prototipo - Segundo Avance | Sesion: <span id="sessionLabel"></span></div>
</div>

<script>
// ============================================================
// CONFIGURACION: URL del Webhook de n8n (canal Web)
// ============================================================
// Cada vez que reinicies ngrok, te da una URL nueva (plan gratis).
// Cuando eso pase, solo tienes que actualizar la linea de abajo
// con la nueva URL que te muestre ngrok (la que dice "Forwarding").
//
// Ejemplo de URL de ngrok:  https://hatred-laxative-swoosh.ngrok-free.dev
// El path "/webhook/agente-uth-chat" NO cambia, viene del workflow de n8n.
const N8N_WEBHOOK_URL = "https://hatred-laxative-swoosh.ngrok-free.dev/webhook/agente-uth-chat";
// ============================================================

// ============================================================
// MENU DE CATEGORIAS Y PREGUNTAS (espejo de knowledge_base)
// Esto NO se manda al motor tal cual -- es solo para desplegar
// los submenus de navegacion en el chat. Al elegir una pregunta
// real, esa SI se manda al webhook de n8n.
// ============================================================
const MENU = {
  "Infraestructura": [
    "¿Dónde pago la matrícula o mensualidad?",
    "¿Dónde queda el aula o el edificio de mi clase?",
    "¿Dónde están ubicadas las oficinas de Registro y Admisiones?",
    "¿Dónde se encuentra la biblioteca?",
    "¿Dónde están los laboratorios de cómputo?",
    "¿Dónde se encuentran las áreas de comida?",
    "¿Dónde puedo estacionar mi vehículo?",
    "¿Dónde está la clínica o enfermería del campus?"
  ],
  "Horarios": [
    "¿Cuál es el horario de atención de Registro?",
    "¿A qué hora inician y terminan las clases en las diferentes jornadas?",
    "¿Cuáles son las fechas de inicio y fin del período académico actual?",
    "¿Cuándo es el período para adiciones y cancelaciones de asignaturas?",
    "¿Cuándo son los exámenes parciales?",
    "¿Cuándo son los períodos de vacaciones o receso académico?"
  ],
  "Tramites Academicos": [
    "¿Cuántas clases puedo matricular por período?",
    "¿Cómo puedo realizar la prematrícula o matrícula de mis clases?",
    "¿Qué documentación requiero para solicitar una certificación de estudios?",
    "¿Cómo se realiza el proceso formal para el retiro de un período académico?",
    "¿Cómo puedo solicitar un cambio de carrera?",
    "¿Cómo solicito equivalencias de materias de otra universidad?",
    "¿Dónde puedo consultar el pensum de mi carrera?",
    "¿Cuáles son los requisitos para solicitar mi graduación?",
    "¿Cómo gestiono mi práctica profesional supervisada?"
  ],
  "Soporte y Cuentas": [
    "Olvidé mi clave del campus virtual, ¿qué hago?",
    "¿Cómo restablezco mi contraseña del correo institucional?",
    "¿Qué becas ofrece la institución?",
    "¿La institución ofrece orientación psicológica?",
    "¿Cuáles son las modalidades y bancos autorizados para el pago de matrícula?",
    "¿Cómo obtengo o renuevo mi carnet estudiantil?",
    "¿Cómo me conecto al wifi del campus?"
  ]
};
const CATEGORIAS = Object.keys(MENU);

const sessionId = "web-" + Math.random().toString(36).substring(2, 10);
document.getElementById("sessionLabel").textContent = sessionId;

const chatMessages = document.getElementById("chatMessages");
const quickReplies = document.getElementById("quickReplies");
const userInput = document.getElementById("userInput");

function agregarMensaje(texto, tipo) {
  const div = document.createElement("div");
  div.className = "msg " + tipo;
  div.textContent = texto;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Muestra los botones de nivel 1: las 4 categorias + transferencia
function mostrarMenuCategorias() {
  quickReplies.innerHTML = "";
  CATEGORIAS.forEach(cat => {
    const btn = document.createElement("button");
    btn.textContent = cat;
    btn.onclick = () => mostrarSubmenu(cat);
    quickReplies.appendChild(btn);
  });
  const btnAsesor = document.createElement("button");
  btnAsesor.textContent = "Hablar con un asesor";
  btnAsesor.onclick = () => enviarMensaje("hablar con un asesor");
  quickReplies.appendChild(btnAsesor);
}

// Muestra los botones de nivel 2: las preguntas reales de una categoria
function mostrarSubmenu(categoria) {
  agregarMensaje(categoria, "user");
  agregarMensaje("Estas son las preguntas frecuentes de " + categoria + ":", "bot");
  quickReplies.innerHTML = "";

  MENU[categoria].forEach(pregunta => {
    const btn = document.createElement("button");
    btn.textContent = pregunta;
    btn.onclick = () => enviarMensaje(pregunta);
    quickReplies.appendChild(btn);
  });

  const btnVolver = document.createElement("button");
  btnVolver.textContent = "⬅️ Volver al menú";
  btnVolver.onclick = () => mostrarMenuCategorias();
  quickReplies.appendChild(btnVolver);
}

async function enviarMensaje(textoForzado) {
  const texto = textoForzado || userInput.value.trim();
  if (!texto) return;
  agregarMensaje(texto, "user");
  userInput.value = "";
  quickReplies.innerHTML = "";

  try {
    const resp = await fetch(N8N_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje: texto, session_id: sessionId })
    });
    const data = await resp.json();
    agregarMensaje(data.texto, "bot");
    mostrarMenuCategorias();
  } catch (e) {
    agregarMensaje("Ocurrio un error de conexion con el servidor. Verifica que n8n y ngrok esten corriendo.", "bot");
  }
}

userInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") enviarMensaje();
});

// Mensaje de bienvenida inicial
window.onload = () => {
  agregarMensaje("¡Hola! Soy tu Asistente Universitario Virtual. ¿En que puedo ayudarte hoy?", "bot");
  mostrarMenuCategorias();
};
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGINA_HTML)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    mensaje = data.get("mensaje", "")
    session_id = data.get("session_id", str(uuid.uuid4()))

    resultado = engine.procesar_mensaje(mensaje, session_id)
    return jsonify(resultado)


@app.route("/api/categorias", methods=["GET"])
def api_categorias():
    return jsonify({"categorias": engine.listar_categorias()})


if __name__ == "__main__":
    print("=" * 60)
    print(" Agente Virtual de Orientacion Universitaria (UTH)")
    print(f" Total de FAQs cargadas: {engine.total_faqs()}")
    print(" Servidor disponible en: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)