const form = document.getElementById("form")
const bar = document.getElementById("bar")
const results = document.getElementById("results")
const shopeeBtn = document.getElementById("shopee")
const previewVoiceBtn = document.getElementById("previewVoice")
const voicePlayer = document.getElementById("voicePlayer")

let shopeeMode = false

shopeeBtn.addEventListener("click", ()=>{
    shopeeMode = !shopeeMode
    shopeeBtn.innerText = shopeeMode ? "⚡ Modo Shopee ATIVO" : "⚡ Modo Shopee"
})

previewVoiceBtn.addEventListener("click", async ()=>{
    const voice = document.querySelector("select[name='voice']").value
    const text = document.querySelector("textarea[name='text']").value
    if(!text.trim()){
        alert("Digite algum texto para ouvir a voz")
        return
    }

    const data = new FormData()
    data.append("voice", voice)
    data.append("text", text)

    const response = await fetch("/preview-voice", {
        method: "POST",
        body: data
    })

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

    const response = await fetch("/process",{
        method:"POST",
        body:data
    })

    bar.style.width="70%"

    if(!response.ok){
        const err = await response.json()
        alert(err.error || "Erro ao processar vídeos")
        bar.style.width="0%"
        return
    }

    const files = await response.json()
    if(!Array.isArray(files)){
        alert("Erro inesperado")
        bar.style.width="0%"
        return
    }

    bar.style.width="100%"

    results.innerHTML = ""

    files.forEach(file=>{
        const container = document.createElement("div")
        container.style.marginBottom="20px"

        const video = document.createElement("video")
        video.src = "/download?file="+file
        video.controls = true
        video.width = 400
        container.appendChild(video)

        const link = document.createElement("a")
        link.href = "/download?file="+file
        link.innerText = "⬇ Baixar"
        link.style.display="block"
        link.style.marginTop="5px"
        container.appendChild(link)

        results.appendChild(container)
    })

    // Botão baixar todos
    if(files.length > 1){
        const downloadAllBtn = document.createElement("button")
        downloadAllBtn.innerText = "⬇ Baixar Todos"
        downloadAllBtn.type = "button"
        downloadAllBtn.onclick = ()=>{
            files.forEach(file=>{
                window.open("/download?file="+file, "_blank")
            })
        }
        results.appendChild(downloadAllBtn)
    }
})
