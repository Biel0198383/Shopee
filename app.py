from flask import Flask, request, jsonify, send_file, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    files = request.files.getlist("videos")
    if not files:
        return jsonify({"error":"Nenhum arquivo enviado"}), 400

    shopeeMode = request.form.get("shopeeMode") == "true"
    resolution = request.form.get("resolution")
    cutAudio = request.form.get("cutAudio") == "true"

    output_files = []

    for file in files:
        filename = f"{uuid.uuid4()}_{file.filename}"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        output_filename = f"processed_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        cmd = [ffmpeg.get_ffmpeg_exe(), "-y", "-i", input_path]

        if resolution:
            width, height = resolution.split("x")
            cmd += ["-vf", f"scale={width}:{height}"]

        cmd += ["-c:v", "libx264", "-c:a", "aac", output_path]

        try:
            # Timeout de 180s por vídeo pra evitar travar o worker
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        except subprocess.TimeoutExpired:
            return jsonify({"error": f"Tempo limite excedido para {file.filename}"}), 500
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Erro ao processar {file.filename}: {e}"}), 500

        output_files.append(output_filename)

    return jsonify(output_files)

@app.route("/preview/<filename>")
def preview(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename))

@app.route("/download")
def download():
    file = request.args.get("file")
    if not file:
        return "Arquivo não encontrado", 404
    path = os.path.join(OUTPUT_FOLDER, file)
    if not os.path.exists(path):
        return "Arquivo não existe", 404
    return send_file(path, as_attachment=True)

@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    # Aqui você integra com Edge TTS ou outra TTS que usar
    return "Preview de voz não implementado", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
