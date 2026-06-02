from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import json
import os
import warnings
warnings.filterwarnings("ignore")

print("=" * 65)
print("   BOVISENSE AI — Sistema de Monitoreo de Tuberculosis")
print("=" * 65)

RUTA_JSON = "sensores_tuberculosis.json"

base_sensores = {}
if os.path.exists(RUTA_JSON):
    with open(RUTA_JSON, "r", encoding="utf-8") as f:
        datos_raw = json.load(f)
    
    for registro in datos_raw:
        v_id = registro["vaca_id"].lower()
        base_sensores[v_id] = registro
    print(f"✅ Base de datos de sensores cargada: {len(base_sensores)} vacas bajo monitoreo.")
else:
    print(f"⚠️ Alerta: No se encontró el archivo '{RUTA_JSON}'. Corre primero el script generador.")

```python
GROQ_API_KEY = os.environ.get("MI_CLAVE_GROQ")
app = Flask(__name__)
cliente = Groq(api_key=GROQ_API_KEY)

def obtener_ficha_vaca(texto_usuario: str) -> str:
    """Busca si el usuario mencionó una vaca y regresa sus datos biométricos actuales"""
    for vaca_id, datos in base_sensores.items():
        id_simple = vaca_id.replace("_", "") 
        numero_id = vaca_id.split("_")[1] if "_" in vaca_id else "" 
        
        if vaca_id in texto_usuario or id_simple in texto_usuario or (numero_id and f"vaca {numero_id}" in texto_usuario):
            bio = datos["biometricos"]
            meta = datos["metadata"]
            
            reporte = f"""
            [DATOS EN TIEMPO REAL DEL SENSOR PARA EL ID {datos['vaca_id'].upper()}]
            • Raza: {meta['breed']}
            • Última fecha de sincronización: {datos['fecha']} (Día de monitoreo: {datos['dia_monitoreo']})
            • Temperatura Corporal: {bio['temperatura_celsius']}°C 
            • Peso Actual: {bio['peso_kg']} kg
            • Frecuencia Respiratoria: {bio['frecuencia_respiratoria_rpm']} rpm
            • Sensor Acústico (Detección de Tos Seca): {'SÍ DETECTADA' if bio['sensor_acustico_tos'] else 'No detectada'}
            • Estado de salud real en simulación: {meta['estado_salud_real']}
            """
            return reporte
    return ""

SYSTEM_PROMPT = """Eres BoviSense AI, un sistema experto en telemetría y vigilancia epidemiológica de Tuberculosis Bovina. 
Tu trabajo es analizar las dudas del ganadero y los datos biométricos que los sensores recopilan (Temperatura, Peso, Frecuencia Respiratoria y Tos).

INSTRUCCIONES CLAVE DE DIAGNÓSTICO:
- Rango Normal Bovino: Temperatura entre 37.5°C y 39.0°C. Frecuencia respiratoria entre 15 y 30 rpm. Sin presencia de tos crónica.
- Alerta de Tuberculosis: Si notas una temperatura mayor a 39.2°C (fiebre fluctuante), frecuencia respiratoria elevada (más de 32 rpm), presencia activa de tos acústica y, sobre todo, una baja constante de peso corporal, adviértelo como un caso altamente sospechoso de Tuberculosis Bovina.

REGLAS DE RESPUESTA:
1. Si el sistema te anexa los [DATOS EN TIEMPO REAL DEL SENSOR] de una vaca específica, analízalos de inmediato, dale el diagnóstico preventivo al ganadero explicando por qué sus constantes indican salud o sospecha de enfermedad.
2. Si el usuario te pregunta algo teórico sobre la Tuberculosis Bovina, responde de manera muy completa y educativa utilizando tu conocimiento conectado a la red.
3. Habla siempre en un español sencillo, claro y directo para el campo. Usa viñetas y emojis.
4. Recuerda siempre que tu diagnóstico es preventivo y deben llamar al Médico Veterinario Zootecnista para la prueba oficial."""

historial = []

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/chat', methods=['POST'])
def chat():
    global historial
    data = request.json
    
    if data.get('reset'):
        historial = []
        return jsonify({"response": "Consulta reiniciada."})

    user_msg = data.get('message', '')
    if not user_msg:
        bienvenida = "👋 **¡Hola! Bienvenido al centro de control unificado de BoviSense AI.**\n\nEstoy listo para resolver tus dudas generales sobre la **Tuberculosis Bovina** o para darte el reporte en tiempo real de los sensores de tus animales.\n\n¿Qué te gustaría consultar hoy?"
        return jsonify({"response": bienvenida})

    datos_vaca_encontrada = obtener_ficha_vaca(user_msg.lower())
    
    mensaje_final_ia = user_msg
    if datos_vaca_encontrada:
        mensaje_final_ia = f"{user_msg}\n\n{datos_vaca_encontrada}"

    historial.append({"role": "user", "content": mensaje_final_ia})
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}] + historial[-6:]

    try:
        completion = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes,
            max_tokens=1000,
            temperature=0.3,
        )
        respuesta = completion.choices[0].message.content
    except Exception as e:
        return jsonify({"response": f"⚠️ **Error:** {str(e)}"}), 500

    historial.append({"role": "assistant", "content": respuesta})
    return jsonify({"response": respuesta})


# === INTERFAZ GRÁFICA (HTML/CSS/JavaScript) ===
HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BoviSense AI — Monitoreo Epidemiológico</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'DM Sans', sans-serif; background: #0f172a; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; color: #f1f5f9; }
  header { width: 100%; max-width: 650px; text-align: center; margin-bottom: 20px; }
  header h1 { color: #38bdf8; font-size: 1.8rem; }
  header p { color: #64748b; font-size: .9rem; margin-top: 4px; }
  .chat-card { width: 100%; max-width: 650px; background: #1e293b; border-radius: 16px; border: 1px solid #334155; display: flex; flex-direction: column; height: 55vh; overflow: hidden; }
  #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
  .msg { max-width: 85%; padding: 12px 16px; border-radius: 14px; font-size: .92rem; line-height: 1.5; white-space: pre-wrap; }
  .msg.bot { background: #0f172a; color: #f1f5f9; align-self: flex-start; border: 1px solid #334155; }
  .msg.user { background: #0284c7; color: white; align-self: flex-end; }
  .input-area { padding: 15px; border-top: 1px solid #334155; display: flex; gap: 10px; background: #0f172a; }
  #input { flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px; color: white; outline: none; resize: none; }
  #btn-send { background: #0284c7; border: none; border-radius: 8px; width: 50px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
  .sugerencias { width: 100%; max-width: 650px; margin-top: 12px; display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; }
  .sug { background: #1e293b; border: 1px solid #334155; border-radius: 20px; padding: 6px 14px; font-size: .78rem; color: #94a3b8; cursor: pointer; }
  .sug:hover { border-color: #38bdf8; color: #38bdf8; }
  .sug.vaca { border-color: #f43f5e; color: #fda4af; }
  .sug.vaca:hover { border-color: #f43f5e; background: #4c0519; }
  footer { margin-top: 20px; font-size: .75rem; color: #475569; text-align: center; }
</style>
</head>
<body>
<header>
  <h1>🐄 BoviSense AI</h1>
  <p>Consultor de Tuberculosis y Panel de Monitoreo por Sensores</p>
</header>
<div class="chat-card">
  <div id="chat"></div>
  <div class="input-area">
    <textarea id="input" rows="1" placeholder="Haz una pregunta teórica o consulta una vaca (ej: vaca_012)..."></textarea>
    <button id="btn-send" onclick="enviar()"><svg viewBox="0 0 24 24" width="20" fill="white"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg></button>
  </div>
</div>
<div class="sugerencias">
  <span class="sug" onclick="preguntar('¿Cuáles son los principales síntomas de la tuberculosis bovina?')">🔍 Síntomas</span>
  <span class="sug" onclick="preguntar('¿Cómo se contagia la tuberculosis en el hato?')">🔊 Transmisión</span>
  <span class="sug" onclick="preguntar('¿Qué medidas de bioseguridad ayudan a prevenirla?')">🛡️ Prevención</span>
  <span class="sug vaca" onclick="preguntar('¿Cómo se encuentran las constantes de la vaca_012?')">🐄 Sensor vaca_012</span>
  <span class="sug vaca" onclick="preguntar('Dame el reporte de la vaca_001')">🐄 Sensor vaca_001</span>
</div>

<footer>BoviSense AI · Sistema conectado a Llama 3.3 vía Groq Cloud</footer>

<script>
const chat = document.getElementById('chat'); const input = document.getElementById('input');
function agregarMsg(tipo, texto) {
  const div = document.createElement('div'); div.className = 'msg ' + tipo;
  let htmlTexto = texto.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
  div.innerHTML = htmlTexto.replace(/\\n/g, '<br>'); chat.appendChild(div); chat.scrollTop = chat.scrollHeight;
}
function preguntar(texto) { input.value = texto; enviar(); }
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviar(); } });
async function enviar() {
  const msg = input.value.trim(); agregarMsg('user', msg ? msg : 'Conectando...'); input.value = '';
  try {
    const res = await fetch('/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg})});
    const data = await res.json(); chat.lastChild.remove();
    if(msg) agregarMsg('user', msg);
    agregarMsg('bot', data.response);
  } catch(err) { chat.lastChild.remove(); agregarMsg('bot', '⚠️ Error de servidor.'); }
}
enviar();
</script>
</body>
</html>"""

# 👇 ESTA SECCIÓN SE ADAPTÓ PARA EL PUERTO INTERNO DE RENDER
if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=puerto)
