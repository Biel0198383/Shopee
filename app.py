from flask import Flask, request, send_file, render_template
import os
import uuid
import subprocess
import tempfile
import traceback
import edge_tts
import asyncio
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

# -------------------------
# Pastas temporárias
# -------------------------
TMP_DIR = tempfile.gettempdir()
UPLOAD_FOLDER = os.path.join(TMP_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(TMP_DIR, "outputs")
PREVIEW_FOLDER = os.path.join(TMP_DIR, "previews")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

FFMPEG_PATH = ffmpeg.get_ffmpeg_exe()

# -------------------------
# Rotas
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")

# Preview de voz
@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    try:
        text = request.form.get("text", "")
        voice = request.form.get("voice", "pt-BR-FranciscaNeural")
        preview_path = os.path.join(PREVIEW_FOLDER, f"preview_{uuid.uuid4()}.mp3")

        if not text.strip():
            return "Nenhum texto enviado", 400

        communicate = edge_tts.Communicate(text, voice)
        asyncio.run(communicate.save(preview_path))

        return send_file(preview_path, mimetype="audio/mpeg")
    except Exception as e:
        print(traceback.format_exc())
        return f"Erro interno: {e}", 500

# Processamento de vídeo
@app.route("/process", methods=["POST"])
def process():
    try:
        files = request.files.getlist("file")
        if not files:
            return "Nenhum arquivo enviado", 400

        shopeeMode = request.form.get("shopeeMode") == "true"
        cut_audio = "cutAudio" in request.form
        text = request.form.get("text", "")
        voice = request.form.get("voice", None)

        output_files = []

        for file in files:
            if not file.filename:
                continue

            unique_id = str(uuid.uuid4())
            input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
            output_path = os.path.join(OUTPUT_FOLDER, f"processed_{unique_id}_{file.filename}")

            file.save(input_path)

            # FFmpeg comando base: força 720p + bitrate 1.5M
            cmd = [FFMPEG_PATH, "-y", "-i", input_path]

            # Sempre escala para 720p vertical
            cmd += ["-vf", "scale=720:1280"]

            # Codec + bitrate
            cmd += ["-c:v", "libx264", "-b:v", "1.5M", "-c:a", "aac"]

            # Adiciona TTS se houver
            if voice and text.strip():
                tts_file = os.path.join(PREVIEW_FOLDER, f"tts_{uuid.uuid4()}.mp3")
                communicate = edge_tts.Communicate(text, voice)
                asyncio.run(communicate.save(tts_file))
                # Sobrepõe áudio do vídeo com TTS
                cmd = [FFMPEG_PATH, "-y", "-i", input_path, "-i", tts_file,
                       "-c:v", "libx264", "-b:v", "1.5M", "-c:a", "aac", "-shortest", output_path]
            elif cut_audio:
                cmd += ["-shortest", output_path]
            else:
                cmd += [output_path]

            subprocess.run(cmd, check=True)
            output_files.append(output_path)

            # Limpeza input
            if os.path.exists(input_path):
                os.remove(input_path)

        # Retorna o primeiro vídeo processado
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
