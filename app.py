from flask import Flask, request, send_file, jsonify, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

# Limite de upload: 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ====================
# ROTAS
# ====================

@app.route("/")
def index():
    return render_template("index.html")  # index.html dentro de templates/

@app.route("/process", methods=["POST"])
def process():
    files = request.files.getlist("videos")  # note que o input name="videos"
    if not files:
        return jsonify({"error":"Nenhum arquivo enviado"}), 400

    processed_files = []

    resolution = request.form.get("resolution", "")
    w, h = (resolution.split("x") if resolution else (None, None))

    for file in files:
        if file.filename == "":
            continue

        filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"processed_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        file.save(input_path)

        scale = ["-vf", f"scale={w}:{h}"] if w and h else []

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
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            processed_files.append(output_filename)
        except Exception:
            continue

    if not processed_files:
        return jsonify({"error":"Falha ao processar vídeos"}), 500

    return jsonify(processed_files)

@app.route("/download")
def download():
    file = request.args.get("file")
    if not file:
        return "Arquivo não especificado", 400
    path = os.path.join(OUTPUT_FOLDER, file)
    if not os.path.exists(path):
        return "Arquivo não encontrado", 404
    return send_file(path, as_attachment=True)

@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    # Placeholder para integração com Edge TTS
    text = request.form.get("text","")
    voice = request.form.get("voice","pt-BR-FranciscaNeural")
    dummy_path = os.path.join(OUTPUT_FOLDER, "dummy.mp3")
    with open(dummy_path,"wb") as f:
        f.write(b"")  # arquivo vazio por enquanto
    return send_file(dummy_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
