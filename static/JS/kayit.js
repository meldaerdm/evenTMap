document.querySelector("form").addEventListener("submit", function (e) {
    const password = document.querySelector('input[name="password"]').value;

    if (password.length < 6) {
        e.preventDefault(); 
        alert("Şifre en az 6 karakter olmalı!");
    }
});

