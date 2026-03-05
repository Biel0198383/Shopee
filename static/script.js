// ================================
// Shopee Video Processor JS - Corrigido
// ================================

const form = document.getElementById("form")
const bar = document.getElementById("bar")
const results = document.getElementById("results")
const shopeeBtn = document.getElementById("shopee")
const previewVoiceBtn = document.getElementById("previewVoice")
const voicePlayer = document.getElementById("voicePlayer")

let shopeeMode = false

shopeeBtn.addEventListener("click", () => {
    shopeeMode = !shopeeMode
    shopeeBtn.innerText = shopeeMode ? "⚡ Modo Shopee ATIVO" : "⚡ Modo Shopee"
})

previewVoiceBtn.addEventListener("click", async () => {
    const voice = document.querySelector("select[name='voice']").value
    const data = new FormData()
    data.append("voice", voice)

    const response = await fetch("/preview-voice", {
        method: "POST",
        body: data
    })

    if (!response.ok) {
        alert("Erro ao gerar prévia da voz")
        return
    }

    const blob = await response.blob()
    const audioURL = URL.createObjectURL(blob)

    voicePlayer.src = audioURL
    voicePlayer.style.display = "block"
    voicePlayer.play()
})

form.addEventListener("submit", async (e) => {
    e.preventDefault()
    bar.style.width = "10%"
    results.innerHTML = ""

    const data = new FormData(form)
    data.append("shopeeMode", shopeeMode)

    let response
    try {
        response = await fetch("/process", {
            method: "POST",
            body: data
        })
    } catch (err) {
        alert("Erro ao enviar vídeo.")
        console.error(err)
        bar.style.width = "0%"
        return
    }

    bar.style.width = "70%"

    if (!response.ok) {
        const text = await response.text()
        alert(text || "Erro ao processar vídeo")
        bar.style.width = "0%"
        return
    }

    // Recebe o vídeo processado como blob
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)

    bar.style.width = "100%"

    // Limpa resultados antes de adicionar novo vídeo
    results.innerHTML = ""

    // Cria preview do vídeo
    const video = document.createElement("video")
    video.src = url
    video.controls = true
    video.width = 300

    // Cria link para download
    const link = document.createElement("a")
    link.href = url
    link.download = "video_processado.mp4"
    link.innerText = "⬇ Baixar"
    link.style.display = "block"

    results.appendChild(video)
    results.appendChild(link)

    // Se você quiser manter múltiplos vídeos como antes, você pode adaptar aqui
    // usando um array de blobs, mas para a versão atual, só processa um vídeo por vez
})
