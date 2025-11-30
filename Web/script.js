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