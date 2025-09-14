async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML += `<div class="p-2 bg-gray-200 rounded my-1"><b>Sen:</b> ${message}</div>`;

    input.value = "";

    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });

    const data = await response.json();
    if (data.reply) {
        chatBox.innerHTML += `<div class="p-2 bg-red-100 rounded my-1"><b>Bot:</b> ${data.reply}</div>`;
    } else {
        chatBox.innerHTML += `<div class="p-2 bg-red-200 rounded my-1">⚠️ Hata: ${data.error}</div>`;
    }
}
