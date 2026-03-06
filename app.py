# app.py
from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
import tempfile
import asyncio
import edge_tts
import imageio_ffmpeg as ffmpeg
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

# Rota para preview da voz
@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    text = request.form.get("text", "")
    voice = request.form.get("voice", "pt-BR-FranciscaNeural")
    
    if not text:
        return "Texto vazio", 400

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_path = tmp_file.name
    tmp_file.close()

    async def synthesize():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_path)

    asyncio.run(synthesize())
    return send_from_directory(os.path.dirname(tmp_path), os.path.basename(tmp_path), as_attachment=True)

# Rota principal de processamento de vídeos
@app.route("/process", methods=["POST"])
def process():
    files = request.files.getlist("videos")
    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    resolution = request.form.get("resolution")
    shopee_mode = request.form.get("shopeeMode") == "true"
    cut_audio = request.form.get("cutAudio") == "on"
    text = request.form.get("text", "")
    voice = request.form.get("voice", "pt-BR-FranciscaNeural")

    processed_files = []

    for file in files:
        filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"processed_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        file.save(input_path)

        cmd = [ffmpeg.get_ffmpeg_exe(), "-y", "-i", input_path]

        # Aplicar resolução se escolhida
        if resolution:
            width, height = resolution.split("x")
            cmd += ["-vf", f"scale={width}:{height}"]

        cmd += ["-c:v", "libx264", "-c:a", "aac", output_path]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Erro ao processar vídeo: {e}"}), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Processamento do vídeo demorou muito"}), 500

        # Se houver texto de narração, gerar voz e mixar
        if text.strip():
            tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            async def synthesize():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(tmp_audio)
            asyncio.run(synthesize())

            # Mixar áudio com vídeo final
            final_output = os.path.join(OUTPUT_FOLDER, f"final_{output_filename}")
            cmd_mix = [
                ffmpeg.get_ffmpeg_exe(),
                "-y",
                "-i", output_path,
                "-i", tmp_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                final_output
            ]
            subprocess.run(cmd_mix, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            processed_files.append(f"final_{output_filename}")
        else:
            processed_files.append(output_filename)

    return jsonify(processed_files)

# Rota de download
@app.route("/download")
def download_file():
    filename = request.args.get("file")
    if not filename:
        return "Arquivo não especificado", 400
    path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        return "Arquivo não encontrado", 404
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
