const form = document.getElementById("form")
const bar = document.getElementById("bar")
const results = document.getElementById("results")
const shopeeBtn = document.getElementById("shopee")
const previewVoiceBtn = document.getElementById("previewVoice")
const voicePlayer = document.getElementById("voicePlayer")
const downloadAllBtn = document.getElementById("downloadAllBtn")

let shopeeMode = false

shopeeBtn.addEventListener("click", ()=>{
    shopeeMode = !shopeeMode
    shopeeBtn.innerText = shopeeMode ? "⚡ Modo Shopee ATIVO" : "⚡ Modo Shopee"
})

previewVoiceBtn.addEventListener("click", async ()=>{
    const voice = document.querySelector("select[name='voice']").value
    const text = document.querySelector("textarea[name='text']").value
    const data = new FormData()
    data.append("voice", voice)
    data.append("text", text)

    const response = await fetch("/preview-voice", { method: "POST", body: data })
    if(!response.ok){
        alert("Erro ao gerar prévia da voz")
        return
    }

    const blob = await response.blob()
    const audioURL = URL.createObjectURL(blob)
    voicePlayer.src = audioURL
    voicePlayer.style.display = "block"
    voicePlayer.play()
})

form.addEventListener("submit", async (e)=>{
    e.preventDefault()
    bar.style.width="10%"
    results.innerHTML=""

    const data = new FormData(form)
    data.append("shopeeMode", shopeeMode)

    const response = await fetch("/process",{ method:"POST", body:data })
    bar.style.width="70%"

    if(!response.ok){
        const text = await response.text()
        alert(text)
        bar.style.width="0%"
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
    link.innerText = "⬇ Baixar"
    link.download = "processed_video.mp4"
    link.style.display="block"

    results.appendChild(video)
    results.appendChild(link)
    bar.style.width="100%"
})

// Botão Baixar Todos (abre todos os vídeos processados)
downloadAllBtn.addEventListener("click", ()=>{
    document.querySelectorAll(".video-check").forEach(cb=>{
        if(cb.checked){
            window.open("/download?file="+cb.value,"_blank")
        }
    })
})
