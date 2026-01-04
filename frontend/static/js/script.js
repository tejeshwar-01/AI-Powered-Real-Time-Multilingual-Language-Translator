document.addEventListener("DOMContentLoaded", () => {

    let socket = null;
    let audioContext = null;
    let processor = null;
    let micStream = null;

    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const modeSelect = document.getElementById("modeSelect");
    const langSelect = document.getElementById("langSelect");
    const textInput = document.getElementById("textInput");

    const inputDisplay = document.getElementById("inputDisplay");
    const outputDisplay = document.getElementById("outputDisplay");
    const detectedLang = document.getElementById("detectedLang");
    const confidenceBar = document.getElementById("confidenceBar");
    const loading = document.getElementById("loading");

    // ================= CONFIDENCE ANIMATION =================
    function animateConfidence(value) {
        confidenceBar.value = 0;
        let current = 0;
        const step = value / 15;

        const anim = setInterval(() => {
            current += step;
            confidenceBar.value = current;
            if (current >= value) clearInterval(anim);
        }, 16);
    }

    // ================= SOCKET =================
    function initSocket() {
        if (socket && socket.readyState === WebSocket.OPEN) return;

        socket = new WebSocket(
            `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/stream`
        );

        socket.onopen = () => {
            socket.send(JSON.stringify({
                type: "config",
                lang: langSelect.value
            }));
        };

        socket.onmessage = e => {
            const data = JSON.parse(e.data);
            loading.classList.add("hidden");

            inputDisplay.innerText = data.original || "—";
            detectedLang.innerText = `Detected: ${(data.source_lang || "en").toUpperCase()}`;

            if (data.fallback) {
                outputDisplay.innerText =
                    "⚠ This language is not supported yet.\nShowing original text.";
            } else {
                outputDisplay.innerText = data.translated || "—";
            }

            animateConfidence(data.confidence ?? 1);
        };

        socket.onclose = () => {
            socket = null;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        };
    }

    // ================= MODE SWITCH =================
    modeSelect.onchange = () => {
        document.getElementById("voiceSection")
            .classList.toggle("hidden", modeSelect.value !== "voice");
        document.getElementById("textSection")
            .classList.toggle("hidden", modeSelect.value === "voice");
    };

    // ================= TEXT =================
    document.getElementById("translateTextBtn").onclick = () => {
        if (!textInput.value.trim()) return;
        initSocket();
        loading.classList.remove("hidden");

        socket.send(JSON.stringify({
            type: "text_translate",
            text: textInput.value.trim(),
            lang: langSelect.value
        }));
    };

    // ================= VOICE =================
    startBtn.onclick = async () => {
        initSocket();
        loading.classList.remove("hidden");

        startBtn.disabled = true;
        stopBtn.disabled = false;

        audioContext = new AudioContext({ sampleRate: 16000 });
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        const source = audioContext.createMediaStreamSource(micStream);
        processor = audioContext.createScriptProcessor(1024, 1, 1);

        processor.onaudioprocess = e => {
            if (!socket || socket.readyState !== WebSocket.OPEN) return;

            const input = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(input.length);

            for (let i = 0; i < input.length; i++) {
                pcm16[i] = Math.max(-1, Math.min(1, input[i])) * 0x7fff;
            }

            socket.send(pcm16.buffer);
        };

        source.connect(processor);
        processor.connect(audioContext.destination);
    };

    stopBtn.onclick = () => {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        processor?.disconnect();
        micStream?.getTracks().forEach(t => t.stop());
    };
});
