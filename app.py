# app.py
from flask import Flask, request, send_file
import os
import subprocess
import imageio_ffmpeg as ffmpeg
import uuid  # Para nomes de arquivos únicos
import shutil  # Para limpar pastas temporárias

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

# Cria pastas caso não existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "Bem-vindo ao app!"

@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return "Nenhum arquivo enviado", 400

    file = request.files['file']
    if file.filename == "":
        return "Arquivo sem nome", 400

    # Gera nomes únicos para evitar conflitos
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
    output_filename = f"processed_{unique_id}_{file.filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # Salva arquivo enviado
    file.save(input_path)

    # Pega o executável FFmpeg fornecido pelo imageio-ffmpeg
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    # Comando FFmpeg
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        output_path
    ]

    # Executa FFmpeg com tratamento de erro
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        # Remove arquivos temporários se der erro
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        return f"Erro ao processar vídeo: {e}", 500

    # Limpa arquivo de input após processamento
    if os.path.exists(input_path):
        os.remove(input_path)

    # Retorna o vídeo processado
    response = send_file(output_path, as_attachment=True)

    # Opcional: limpa o output depois de enviar (evita acumular arquivos)
    @response.call_on_close
    def cleanup():
        if os.path.exists(output_path):
            os.remove(output_path)

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
