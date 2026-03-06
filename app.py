from flask import Flask, request, send_file, send_from_directory, render_template, jsonify
import os
import subprocess
import uuid
import asyncio
import edge_tts
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MAX_VIDEOS = 20

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    text = request.form.get("text", "")
    voice = request.form.get("voice", "")

    if not text.strip():
        return "Nenhum texto fornecido", 400

    preview_file = "/tmp/voice_preview.mp3"

    async def synthesize():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(preview_file)

    asyncio.run(synthesize())

    return send_from_directory("/tmp", "voice_preview.mp3", as_attachment=True)

@app.route("/process", methods=["POST"])
def process():
    files = request.files.getlist("videos")
    resolution = request.form.get("resolution")
    shopee_mode = request.form.get("shopeeMode") == "true"
    text = request.form.get("text", "")
    voice = request.form.get("voice", "")
    cut_audio = "cutAudio" in request.form

    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    if len(files) > MAX_VIDEOS:
        return jsonify({"error": f"Envie no máximo {MAX_VIDEOS} vídeos"}), 400

    processed_files = []

    for file in files:
        filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"processed_{filename}")

        file.save(input_path)

        cmd = [ffmpeg.get_ffmpeg_exe(), "-y", "-i", input_path]

        # Ajuste de resolução
        if resolution:
            width, height = resolution.split("x")
            cmd += ["-vf", f"scale={width}:{height}"]

        cmd += ["-c:v", "libx264", "-c:a", "aac", output_path]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        except subprocess.TimeoutExpired:
            return jsonify({"error": f"Processamento do vídeo {file.filename} demorou demais"}), 500
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Erro ao processar vídeo {file.filename}: {e}"}), 500

        processed_files.append(f"processed_{filename}")

    return jsonify(processed_files)

@app.route("/download")
def download_file():
    file = request.args.get("file")
    if not file:
        return "Arquivo não especificado", 400

    path = os.path.join(OUTPUT_FOLDER, file)
    if not os.path.exists(path):
        return "Arquivo não encontrado", 404

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
