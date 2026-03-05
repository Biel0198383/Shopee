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
    const text = document.querySelector("textarea[name='text']").value
    if (!text.trim()) { alert("Digite algum texto para a narração"); return }

    const data = new FormData()
    data.append("voice", voice)
    data.append("text", text)

    try {
        const response = await fetch("/preview-voice", { method: "POST", body: data })
        if (!response.ok) { alert("Erro ao gerar prévia da voz"); return }

        const blob = await response.blob()
        const audioURL = URL.createObjectURL(blob)
        voicePlayer.src = audioURL
        voicePlayer.style.display = "block"
        voicePlayer.play()
    } catch (err) {
        console.error(err)
        alert("Erro ao gerar prévia da voz")
    }
})

form.addEventListener("submit", async (e) => {
    e.preventDefault()
    bar.style.width = "10%"
    results.innerHTML = ""

    const videoInput = document.getElementById("videoInput")
    if (!videoInput.files.length) { alert("Selecione pelo menos um vídeo"); return }

    const data = new FormData()
    for (let file of videoInput.files) data.append("file", file)
    data.append("shopeeMode", shopeeMode)
    data.append("text", document.querySelector("textarea[name='text']").value)
    data.append("voice", document.querySelector("select[name='voice']").value)
    data.append("resolution", document.querySelector("select[name='resolution']").value)
    if (document.getElementById("cutAudio").checked) data.append("cutAudio", "true")

    try {
        const response = await fetch("/process", { method: "POST", body: data })
        bar.style.width = "70%"
        if (!response.ok) {
            const text = await response.text()
            alert(text || "Erro ao processar vídeos")
            bar.style.width = "0%"
            return
        }

        const blob = await response.blob()
        const url = URL.createObjectURL(blob)

        const video = document.createElement("video")
        video.src = url
        video.controls = true
        video.width = 300

        const link = document.createElement("a")
        link.href = url
        link.download = "video_processado.mp4"
        link.innerText = "⬇ Baixar"
        link.style.display = "block"

        results.appendChild(video)
        results.appendChild(link)

        // Botão "Baixar Todos"
        const downloadAllBtn = document.createElement("button")
        downloadAllBtn.innerText = "Baixar Todos"
        downloadAllBtn.type = "button"
        downloadAllBtn.style.marginTop = "10px"
        downloadAllBtn.onclick = () => {
            const videos = results.querySelectorAll("video")
            videos.forEach((vid, i) => {
                const a = document.createElement("a")
                a.href = vid.src
                a.download = `video_processado_${i+1}.mp4`
                a.click()
            })
        }
        results.appendChild(downloadAllBtn)

        bar.style.width = "100%"
    } catch (err) {
        console.error(err)
        alert("Erro ao enviar vídeos")
        bar.style.width = "0%"
    }
})
