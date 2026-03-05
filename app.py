# app.py
from flask import Flask, request, send_file, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
PREVIEW_FOLDER = "previews"

# Cria pastas caso não existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

@app.route("/")
def index():
    # Mantém seu template principal
    return render_template("index.html")  # ajuste se necessário

# ----------------------------
# Rota de processamento de vídeo
# ----------------------------
@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == "":
        return "Arquivo sem nome", 400

    # Gera nomes únicos
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
    output_filename = f"processed_{unique_id}_{file.filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    preview_path = os.path.join(PREVIEW_FOLDER, f"preview_{unique_id}.mp4")

    # Salva arquivo enviado
    file.save(input_path)

    # Caminho do executável FFmpeg
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    # ---------- Ajusta resolução e adiciona narração (se houver) ----------
    audio_file = request.files.get("audio")  # se tiver narração enviada
    cmd = [ffmpeg_path, "-y", "-i", input_path]

    if audio_file:
        # Salva narração temporária
        audio_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_audio.wav")
        audio_file.save(audio_path)
        cmd += ["-i", audio_path]  # adiciona como segunda entrada

    # Define filtros e codecs
    cmd += [
        "-vf", "scale=720:-2",  # ajuste de resolução
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest" if audio_file else "",
        output_path
    ]
    # Remove strings vazias
    cmd = [c for c in cmd if c != ""]

    # Executa ffmpeg
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        # Limpeza em caso de erro
        if os.path.exists(input_path): os.remove(input_path)
        if audio_file and os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(output_path): os.remove(output_path)
        return f"Erro ao processar vídeo: {e}", 500

    # Limpa arquivos temporários
    if os.path.exists(input_path): os.remove(input_path)
    if audio_file and os.path.exists(audio_path): os.remove(audio_path)

    # ---------- Gera preview de 10 segundos ----------
    cmd_preview = [
        ffmpeg_path,
        "-y",
        "-i", output_path,
        "-t", "10",
        "-vf", "scale=320:-2",
        preview_path
    ]
    try:
        subprocess.run(cmd_preview, check=True)
    except subprocess.CalledProcessError:
        preview_path = None  # se falhar, não quebra o app

    # ---------- Retorna arquivo final ----------
    response = send_file(output_path, as_attachment=True)

    # Limpa output e preview depois do envio
    @response.call_on_close
    def cleanup():
        if os.path.exists(output_path): os.remove(output_path)
        if preview_path and os.path.exists(preview_path): os.remove(preview_path)

    return response

# ----------------------------
# Inicialização do app
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
