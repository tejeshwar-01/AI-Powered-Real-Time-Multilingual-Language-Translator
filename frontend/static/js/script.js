document.addEventListener("DOMContentLoaded", () => {

let socket=null,audioContext=null,processor=null,micStream=null;

const startBtn=document.getElementById("startBtn");
const stopBtn=document.getElementById("stopBtn");
const modeSelect=document.getElementById("modeSelect");
const langSelect=document.getElementById("langSelect");
const textInput=document.getElementById("textInput");
const translateBtn=document.getElementById("translateTextBtn");

const inputDisplay=document.getElementById("inputDisplay");
const outputDisplay=document.getElementById("outputDisplay");
const detectedLang=document.getElementById("detectedLang");
const confidenceBar=document.getElementById("confidenceBar");
const loading=document.getElementById("loading");

function animateConfidence(value){
    confidenceBar.value=0;
    let c=0,step=value/15;
    const anim=setInterval(()=>{
        c+=step;
        confidenceBar.value=c;
        if(c>=value)clearInterval(anim);
    },16);
}

function initSocket(){
    if(socket && socket.readyState===1) return;
    socket=new WebSocket(
        `${location.protocol==="https:"?"wss":"ws"}://${location.host}/ws/stream`
    );
    socket.onmessage=e=>{
        const d=JSON.parse(e.data);
        loading.classList.add("hidden");
        inputDisplay.innerText=d.original||"—";
        detectedLang.innerText=`Detected: ${(d.source_lang||"en").toUpperCase()}`;
        outputDisplay.innerText=d.translated||"—";
        animateConfidence(d.confidence||1);
    };
}

modeSelect.onchange=()=>{
    document.getElementById("voiceSection")
        .classList.toggle("hidden",modeSelect.value!=="voice");
    document.getElementById("textSection")
        .classList.toggle("hidden",modeSelect.value==="voice");
};

translateBtn.onclick=async()=>{
    if(!textInput.value.trim())return;

    translateBtn.disabled=true;
    loading.classList.remove("hidden");

    const res=await fetch("/translate-text",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            text:textInput.value.trim(),
            lang:langSelect.value
        })
    });

    const data=await res.json();
    outputDisplay.innerText=data.translated;
    detectedLang.innerText=`Latency: ${data.latency_ms} ms`;

    loading.classList.add("hidden");
    translateBtn.disabled=false;
};

startBtn.onclick=async()=>{
    initSocket();
    startBtn.disabled=true;
    stopBtn.disabled=false;

    audioContext=new AudioContext({sampleRate:16000});
    micStream=await navigator.mediaDevices.getUserMedia({audio:true});

    const source=audioContext.createMediaStreamSource(micStream);
    processor=audioContext.createScriptProcessor(1024,1,1);

    processor.onaudioprocess=e=>{
        if(!socket||socket.readyState!==1)return;
        const input=e.inputBuffer.getChannelData(0);
        const pcm=new Int16Array(input.length);
        for(let i=0;i<input.length;i++){
            pcm[i]=Math.max(-1,Math.min(1,input[i]))*0x7fff;
        }
        socket.send(pcm.buffer);
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
};

stopBtn.onclick=()=>{
    startBtn.disabled=false;
    stopBtn.disabled=true;
    processor?.disconnect();
    micStream?.getTracks().forEach(t=>t.stop());
};

});
