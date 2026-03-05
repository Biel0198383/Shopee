# app.py
from flask import Flask, request, send_file, jsonify, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg
import tempfile
import traceback

app = Flask(__name__)

# -------------------------
# Pastas temporárias Railway
# -------------------------
TMP_DIR = tempfile.gettempdir()
UPLOAD_FOLDER = os.path.join(TMP_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(TMP_DIR, "outputs")
PREVIEW_FOLDER = os.path.join(TMP_DIR, "previews")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

# -------------------------
# Rotas
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")  # mantém seu HTML

# Preview de voz (narração)
@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    try:
        voice = request.form.get("voice")
        text = request.form.get("text", "Olá")  # Texto default se estiver vazio

        # Aqui você implementaria a síntese de voz com Azure/TTS/etc
        # Para exemplo simples, apenas retornamos um arquivo dummy
        preview_path = os.path.join(TMP_DIR, f"preview_{uuid.uuid4()}.wav")
        # Gera arquivo WAV dummy (silêncio)
        with open(preview_path, "wb") as f:
            f.write(b"\0" * 44100)  # 1s de silêncio
        return send_file(preview_path, mimetype="audio/wav")
    except Exception as e:
        print(traceback.format_exc())
        return f"Erro interno: {e}", 500

# Processamento de vídeo
@app.route("/process", methods=["POST"])
def process():
    try:
        if "file" not in request.files:
            return "Nenhum arquivo enviado", 400

        files = request.files.getlist("file")  # suporta múltiplos vídeos
        shopeeMode = request.form.get("shopeeMode") == "true"
        resolution = request.form.get("resolution", None)
        cut_audio = "cutAudio" in request.form
        text = request.form.get("text", "")
        voice = request.form.get("voice", None)

        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        output_files = []

        for file in files:
            if file.filename == "":
                continue
            unique_id = str(uuid.uuid4())
            input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
            output_path = os.path.join(OUTPUT_FOLDER, f"processed_{unique_id}_{file.filename}")

            file.save(input_path)

            # Monta comando FFmpeg
            cmd = [ffmpeg_path, "-y", "-i", input_path]

            # Ajuste de resolução
            if resolution:
                width, height = resolution.split("x")
                cmd += ["-vf", f"scale={width}:{height}"]

            # Codec
            cmd += ["-c:v", "libx264", "-c:a", "aac"]

            # Narração (dummy placeholder)
            if voice and text.strip():
                # Aqui você adicionaria a narração real
                pass  # placeholder

            # Se cortar áudio
            if cut_audio:
                cmd += ["-shortest"]

            cmd += [output_path]

            subprocess.run(cmd, check=True)
            output_files.append(output_path)

            # Limpeza do input
            if os.path.exists(input_path):
                os.remove(input_path)

        # Para simplificar, retornamos o **primeiro vídeo processado** como blob
        if output_files:
            return send_file(output_files[0], as_attachment=True)

        return "Nenhum vídeo processado", 400

    except Exception as e:
        print(traceback.format_exc())
        return f"Erro interno: {e}", 500

# -------------------------
# Inicialização
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
