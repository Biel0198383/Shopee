from flask import Flask, request, send_file, jsonify
import os
import subprocess
import imageio_ffmpeg as ffmpeg
import uuid

app = Flask(__name__)

# Limite de upload: 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == "":
        return "Arquivo sem nome", 400

    # Gera nome único para evitar conflito
    filename = f"{uuid.uuid4()}_{file.filename}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_filename = f"processed_{filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    file.save(input_path)

    # Seleção de resolução
    resolution = request.form.get("resolution", "")
    scale = []
    if resolution:
        w, h = resolution.split("x")
        scale = ["-vf", f"scale={w}:{h}"]

    # Caminho do FFmpeg via imageio
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        *scale,
        "-c:v", "libx264",
        "-c:a", "aac",
        output_path
    ]

    try:
        # Rodar FFmpeg sem timeout (async-safe)
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        return f"Erro ao processar vídeo: {e}", 500

    return send_file(output_path, as_attachment=True)

@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    # Aqui você coloca seu código do Edge TTS
    # Recebe text + voice
    return "Funcionalidade de prévia de voz ainda"

if __name__ == "__main__":
    # Rodar localmente só para testes
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
