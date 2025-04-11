document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('secretForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (username === 'Administrator' && password === 'nimdA') {
            window.location.href = '/admin';
        } else {
            window.location.href = '/other';
        }
    });
});