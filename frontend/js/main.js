function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}