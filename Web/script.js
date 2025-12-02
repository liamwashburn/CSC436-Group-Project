function showToast(message) {
        const toast = document.getElementById('success-toast');
        if (toast) {
            toast.querySelector('span').innerText = message;
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
}


const strand = document.getElementById("strand");
const colors = ["red", "yellow", "blue", "green",, "purple"];

function renderBulbs() {
    strand.innerHTML = "";

    const bulbWidth = 32;
    const minGap = 40;
    const neededWidth = bulbWidth + minGap;

    const count = Math.floor(window.innerWidth / neededWidth);

    for (let i = 0; i < count; i++) {
        const b = document.createElement("div");
        b.className = "bulb";
        b.style.background = colors[i % colors.length];
        strand.appendChild(b);
    }
}

renderBulbs();
window.addEventListener("resize", renderBulbs);
