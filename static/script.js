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
    const data = new FormData()
    data.append("voice", voice)
    const response = await fetch("/preview-voice", {method:"POST", body:data})
    if(!response.ok){ alert("Erro ao gerar prévia da voz"); return }
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

    const response = await fetch("/process",{method:"POST", body:data})
    if(!response.ok){ alert("Erro ao processar"); return }
    const res = await response.json()
    const files = res.files

    bar.style.width="100%"

    files.forEach(file=>{
        const container = document.createElement("div")
        const video = document.createElement("video")
        video.src="/download?file="+file
        video.controls=true
        video.width=300
        const link = document.createElement("a")
        link.href="/download?file="+file
        link.innerText="⬇ Baixar"
        link.style.display="block"
        container.appendChild(video)
        container.appendChild(link)
        results.appendChild(container)
    })
})

downloadAllBtn.addEventListener("click", ()=>{
    window.open("/download-all","_blank")
})
