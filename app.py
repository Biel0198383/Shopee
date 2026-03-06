from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
import zipfile
from io import BytesIO
import threading
import imageio_ffmpeg as ffmpeg

app = Flask(__name__, template_folder="templates")

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=2)  # 2 threads para processamento

# Jobs ativos
processing_jobs = {}

@app.route("/")
def index():
    return render_template("index.html")

def process_video(input_path, output_path, resolution):
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_path, "-y", "-i", input_path, "-c:v", "libx264", "-c:a", "aac"]

    if resolution:
        width, height = resolution.split("x")
        cmd += ["-vf", f"scale={width}:{height}"]

    subprocess.run(cmd, check=True, timeout=180)

@app.route("/process", methods=["POST"])
def process():
    if 'videos' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    files = request.files.getlist('videos')
    resolution = request.form.get("resolution") or ""
    shopee_mode = request.form.get("shopeeMode") == "true"

    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = []

    for file in files:
        if file.filename == "":
            continue

        uid = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{file.filename}")
        file.save(input_path)

        output_filename = f"processed_{file.filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Roda em background para não travar o worker
        executor.submit(process_video, input_path, output_path, resolution)

        processing_jobs[job_id].append(output_filename)

    return jsonify({"job_id": job_id, "files": processing_jobs[job_id]})

@app.route("/download")
def download():
    filename = request.args.get("file")
    if not filename:
        return "Arquivo não especificado", 400
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route("/download-all")
def download_all():
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for f in os.listdir(OUTPUT_FOLDER):
            path = os.path.join(OUTPUT_FOLDER, f)
            zf.write(path, arcname=f)
    memory_file.seek(0)
    return send_from_directory(OUTPUT_FOLDER, path=None, as_attachment=True, download_name="all_videos.zip")

@app.route("/preview-voice", methods=["POST"])
def preview_voice():
    voice = request.form.get("voice")
    # Placeholder Edge TTS - você substitui com sua função de TTS real
    from io import BytesIO
    dummy_audio = BytesIO()
    dummy_audio.write(b"")  # vazio só para placeholder
    dummy_audio.seek(0)
    return send_from_directory(".", "placeholder.mp3", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
