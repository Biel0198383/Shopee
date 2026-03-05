# app.py
from flask import Flask, request, jsonify, send_file, render_template
import os
import subprocess
import uuid
import imageio_ffmpeg as ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ----------------------------
# Rotas existentes do seu site
# ----------------------------

@app.route("/")
def index():
    # Mantém seu HTML principal, se você usa templates
    return render_template("index.html")  # ou seu conteúdo atual

# Aqui você pode manter todas as outras rotas que já tinha
# Exemplo:
# @app.route("/sobre")
# def sobre():
#     return render_template("sobre.html")

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

    # Gera nomes únicos para evitar conflito
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{file.filename}")
    output_filename = f"processed_{unique_id}_{file.filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # Salva o arquivo enviado
    file.save(input_path)

    # Pega o caminho do executável FFmpeg fornecido pelo imageio-ffmpeg
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    # Monta comando FFmpeg
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
        # Remove arquivos temporários em caso de erro
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        return f"Erro ao processar vídeo: {e}", 500

    # Remove arquivo de input após processamento
    if os.path.exists(input_path):
        os.remove(input_path)

    # Retorna o vídeo processado
    response = send_file(output_path, as_attachment=True)

    # Limpeza do output após envio
    @response.call_on_close
    def cleanup():
        if os.path.exists(output_path):
            os.remove(output_path)

    return response

# ----------------------------
# Inicialização do app
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
