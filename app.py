import os
import subprocess
from uuid import uuid4
from flask import Flask, request, send_from_directory, render_template, jsonify, send_file
import edge_tts

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['OUTPUT_FOLDER'] = "outputs"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Home
@app.route("/")
def index():
    return render_template("index.html")

# Processamento
@app.route("/process", methods=["POST"])
def process():
    files = request.files.getlist("videos")
    text = request.form.get("text", "").strip()
    voice = request.form.get("voice")
    resolution = request.form.get("resolution") or "720x1280"

    if not files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    output_files = []

    for file in files:
        filename = f"{uuid4()}_{file.filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Se houver narração, gerar TTS
        if text:
            tts_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid4()}.mp3")
            communicate = edge_tts.Communicate(text, voice)
            communicate.save(tts_path)
        else:
            tts_path = None

        # Gerar nome do output
        out_filename = f"processed_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], out_filename)

        # FFmpeg: escala + TTS
        cmd = [
            "ffmpeg",
            "-y",
            "-i", upload_path,
        ]

        if tts_path:
            cmd += ["-i", tts_path, "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0"]
        else:
            cmd += ["-c:a", "aac"]

        # Scale
        width, height = resolution.split("x")
        cmd += ["-vf", f"scale={width}:{height}", "-c:v", "libx264", "-b:v", "2M", output_path]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_files.append(out_filename)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Erro ao processar vídeo {filename}: {e}"}), 500

    return jsonify({"files": output_files})

# Download individual
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

# Download zip
from zipfile import ZipFile
@app.route("/download_all", methods=["POST"])
def download_all():
    files = request.json.get("files", [])
    if not files:
        return jsonify({"error": "Nenhum arquivo para baixar"}), 400

    zip_name = f"videos_{uuid4()}.zip"
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], zip_name)

    with ZipFile(zip_path, 'w') as zipf:
        for f in files:
            file_path = os.path.join(app.config['OUTPUT_FOLDER'], f)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=f)

    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
