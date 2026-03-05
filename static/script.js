// Seleciona elementos do HTML
const videoInput = document.getElementById("videoInput");   // seu input de vídeo
const audioInput = document.getElementById("audioInput");   // input opcional de narração
const sendBtn = document.getElementById("sendBtn");         // botão de enviar
const previewVideo = document.getElementById("preview");   // elemento <video> para preview (opcional)

sendBtn.addEventListener("click", async () => {
    if (!videoInput.files[0]) {
        alert("Selecione um vídeo!");
        return;
    }

    const formData = new FormData();
    formData.append("file", videoInput.files[0]);  // vídeo
    if (audioInput.files[0]) {
        formData.append("audio", audioInput.files[0]); // narração opcional
    }

    try {
        // Envia para o Flask
        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const text = await response.text();
            alert("Erro no processamento: " + text);
            return;
        }

        // Recebe o vídeo processado
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Cria link para download automático
        const a = document.createElement("a");
        a.href = url;
        a.download = "video_processado.mp4";
        document.body.appendChild(a);
        a.click();
        a.remove();

        // Mostra preview no site (opcional)
        if (previewVideo) {
            previewVideo.src = url;
            previewVideo.load();
            previewVideo.play();
        }

    } catch (err) {
        console.error(err);
        alert("Erro ao enviar vídeo.");
    }
});
