# app.py
from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg

app = Flask(__name__, template_folder="templates")

# Pastas
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    if 'videos' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = request.files.getlist('videos')
    resolution = request.form.get("resolution") or ""
    shopee_mode = request.form.get("shopeeMode") == "true"

    processed_files = []

    for file in files:
        if file.filename == "":
            continue

        # Cria nomes únicos
        uid = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{file.filename}")
        file.save(input_path)

        output_filename = f"processed_{file.filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Pega o caminho do FFmpeg
        ffmpeg_path = ffmpeg.get_ffmpeg_exe()

        cmd = [ffmpeg_path, "-y", "-i", input_path]

        # Resolução
        if resolution:
            width, height = resolution.split("x")
            cmd += ["-vf", f"scale={width}:{height}"]

        # Codec
        cmd += ["-c:v", "libx264", "-c:a", "aac"]

        try:
            # Sem capturar stdout/stderr para não travar Gunicorn
            subprocess.run(cmd, check=True, timeout=180)
            processed_files.append(output_filename)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Erro ao processar {file.filename}: {e}"}), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": f"Tempo esgotado para {file.filename}"}), 500

    return jsonify(processed_files)


# Download individual
@app.route("/download")
def download():
    filename = request.args.get("file")
    if not filename:
        return "Arquivo não especificado", 400
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

# Download todos
@app.route("/download-all")
def download_all():
    import zipfile
    from io import BytesIO

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for f in os.listdir(OUTPUT_FOLDER):
            path = os.path.join(OUTPUT_FOLDER, f)
            zf.write(path, arcname=f)
    memory_file.seek(0)
    return send_from_directory(directory=OUTPUT_FOLDER, path=None, as_attachment=True, download_name="all_videos.zip")

# Preview de voz placeholder (Edge TTS já faz o áudio)
@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    voice = request.form.get("voice")
    # Aqui você conecta ao Edge TTS
    # Retorna um mp3 de exemplo
    from io import BytesIO
    dummy_audio = BytesIO()
    dummy_audio.write(b"")  # vazio só para placeholder
    dummy_audio.seek(0)
    return send_from_directory(".", "placeholder.mp3", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
