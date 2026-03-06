const form = document.getElementById("form");
const bar = document.getElementById("bar");
const results = document.getElementById("results");
const downloadAllBtn = document.getElementById("downloadAll");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const files = form.videos.files;
    if (!files.length) return alert("Nenhum arquivo selecionado");

    const formData = new FormData(form);
    bar.style.width = "0%";
    results.innerHTML = "";

    const res = await fetch("/process", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    if(data.error) return alert(data.error);

    let html = "";
    data.files.forEach(file=>{
        html += `<div>${file} - <a href="/download/${file}">⬇️ Baixar</a></div>`;
    });
    results.innerHTML = html;

    if(data.files.length>1){
        downloadAllBtn.style.display="block";
        downloadAllBtn.onclick = async ()=>{
            const r = await fetch("/download_all", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({files:data.files})
            });
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href=url;
            a.download="videos.zip";
            document.body.appendChild(a);
            a.click();
            a.remove();
        }
    }else{
        downloadAllBtn.style.display="none";
    }

    bar.style.width="100%";
});
