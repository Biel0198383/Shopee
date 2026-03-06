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
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error":"Nenhum arquivo enviado"}), 400

    processed_files = []

    for file in files:
        if file.filename == "":
            continue

        filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_filename = f"processed_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        file.save(input_path)

        # Resolução
        resolution = request.form.get("resolution", "")
        scale = []
        if resolution:
            w, h = resolution.split("x")
            scale = ["-vf", f"scale={w}:{h}"]

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
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processed_files.append(output_filename)
        except Exception as e:
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
    # Aqui você integra Edge TTS
    # Recebe text + voice
    text = request.form.get("text","")
    voice = request.form.get("voice","pt-BR-FranciscaNeural")
    # Placeholder: retorna dummy audio
    dummy_path = os.path.join(OUTPUT_FOLDER, "dummy.mp3")
    with open(dummy_path,"wb") as f:
        f.write(b"")  # apenas arquivo vazio por enquanto
    return send_file(dummy_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
