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

    const files = await response.json()
    if (!Array.isArray(files)) {
        alert(files.error || "Erro ao processar vídeos")
        bar.style.width="0%"
        return
    }

    bar.style.width="100%"

    results.innerHTML = ""
    if (files.length === 1) {
        const video = document.createElement("video")
        video.src="/download?file="+files[0]
        video.controls=true
        video.width=300

        const link = document.createElement("a")
        link.href="/download?file="+files[0]
        link.innerText="⬇ Baixar"
        link.style.display="block"

        results.appendChild(video)
        results.appendChild(link)
    } else {
        const title = document.createElement("h3")
        title.innerText = "Vídeos processados:"
        results.appendChild(title)

        files.forEach(file=>{
            const container = document.createElement("div")
            const checkbox = document.createElement("input")
            checkbox.type = "checkbox"
            checkbox.value = file
            checkbox.classList.add("video-check")
            const label = document.createElement("span")
            label.innerText = " " + file
            container.appendChild(checkbox)
            container.appendChild(label)
            results.appendChild(container)
        })

        const selectAllBtn = document.createElement("button")
        selectAllBtn.innerText = "Selecionar Todos"
        selectAllBtn.type = "button"
        selectAllBtn.onclick = ()=> document.querySelectorAll(".video-check").forEach(cb=>cb.checked=true)

        const downloadSelectedBtn = document.createElement("button")
        downloadSelectedBtn.innerText = "Baixar Selecionados"
        downloadSelectedBtn.type = "button"
        downloadSelectedBtn.onclick = ()=> {
            document.querySelectorAll(".video-check").forEach(cb=>{
                if(cb.checked) window.open("/download?file="+cb.value,"_blank")
            })
        }

        const downloadAllBtn = document.createElement("button")
        downloadAllBtn.innerText = "Baixar Todos"
        downloadAllBtn.type = "button"
        downloadAllBtn.onclick = ()=> files.forEach(file=>window.open("/download?file="+file,"_blank"))

        results.appendChild(selectAllBtn)
        results.appendChild(downloadSelectedBtn)
        results.appendChild(downloadAllBtn)
    }
})
