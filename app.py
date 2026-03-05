import os
import uuid
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
AUDIO_FOLDER = "audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():

    files = request.files.getlist("videos")
    text = request.form.get("text")
    voice = request.form.get("voice")
    resolution = request.form.get("resolution")

    results = []

    audio_file = None

    if text and voice:

        audio_file = os.path.join(AUDIO_FOLDER, f"{uuid.uuid4()}.mp3")

        subprocess.run([
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", audio_file
        ])

    for file in files:

        video_id = str(uuid.uuid4())

        input_path = os.path.join(UPLOAD_FOLDER, video_id + ".mp4")
        output_path = os.path.join(OUTPUT_FOLDER, video_id + ".mp4")

        file.save(input_path)

        cmd = ["ffmpeg", "-y", "-i", input_path]

        if audio_file:
            cmd += ["-i", audio_file, "-map", "0:v", "-map", "1:a"]
        else:
            cmd += ["-map", "0:v", "-map", "0:a?"]

        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac"
        ]

        if resolution:
            w, h = resolution.split("x")

            cmd += [
                "-vf",
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2"
            ]

        cmd.append(output_path)

        subprocess.run(cmd)

        results.append({
            "file": video_id + ".mp4"
        })

    return jsonify(results)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


@app.route("/preview-voice", methods=["POST"])
def preview_voice():

    data = request.get_json()

    text = data.get("text", "Teste de voz")
    voice = data.get("voice")

    audio_file = os.path.join(AUDIO_FOLDER, "preview.mp3")

    subprocess.run([
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--write-media", audio_file
    ])

    return jsonify({
        "url": "/audio/preview.mp3"
    })


@app.route("/audio/<filename>")
def audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
