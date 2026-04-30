async function sendToBackend(port, payload) {
    const url = `http://127.0.0.1:${port}/process`;
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Сервер недоступен:', error);
        alert(`Не удалось подключиться к серверу на порту ${port}. Проверьте, что сервер запущен.`);
        return null;
    }
}