let ws;
let mediaRecorder;

function startMic() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    ws = new WebSocket("ws://127.0.0.1:8080/ws/subtitles");
    ws.onmessage = e => {
      const d = JSON.parse(e.data);
      document.getElementById("subs").innerHTML =
        `<p>${d.original}</p><p><b>${d.translated}</b></p>`;
    };

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => ws.send(e.data);
    mediaRecorder.start(1000);
  });
}
