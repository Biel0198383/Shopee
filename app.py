# app.py
from flask import Flask, request, jsonify, send_file
import os
import subprocess
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "Bem-vindo ao app!"

@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == "":
        return "Arquivo sem nome", 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_filename = f"processed_{file.filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # Salva arquivo enviado
    file.save(input_path)

    # Pega o caminho do executável FFmpeg baixado pelo Python
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    # Monta comando FFmpeg (mantendo seu fluxo atual)
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        output_path
    ]

    # Executa FFmpeg com tratamento de erro
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return f"Erro ao processar vídeo: {e}", 500

    # Retorna o vídeo processado
    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
