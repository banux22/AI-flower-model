let stream = null;
let isCameraActive = false;

function openTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

document.getElementById('start-camera').addEventListener('click', async function() {
    try {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 1280 }
            } 
        });
        
        const video = document.getElementById('video');
        video.srcObject = stream;
        document.getElementById('capture-btn').disabled = false;
        this.disabled = true;
        this.textContent = 'Камера включена';
        isCameraActive = true;
        
        video.onloadedmetadata = function() {
            setupSquareOverlay();
        };
        
    } catch (err) {
        console.error('Ошибка доступа к камере:', err);
        alert('Не удалось получить доступ к камере. Проверьте разрешения.');
    }
});

function setupSquareOverlay() {
    const cameraContainer = document.querySelector('.camera-container');
    const oldOverlay = document.getElementById('square-overlay');
    if (oldOverlay) {
        oldOverlay.remove();
    }
    const overlay = document.createElement('div');
    overlay.id = 'square-overlay';
    overlay.innerHTML = '';
    
    cameraContainer.appendChild(overlay);
}

document.getElementById('capture-btn').addEventListener('click', function() {
    if (!isCameraActive) return;
    
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const preview = document.getElementById('preview');
    
    const size = Math.min(video.videoWidth, video.videoHeight);
    canvas.width = size;
    canvas.height = size;
    
    const context = canvas.getContext('2d');
    const x = (video.videoWidth - size) / 2;
    const y = (video.videoHeight - size) / 2;
    
    context.drawImage(video, x, y, size, size, 0, 0, size, size);
    
    preview.src = canvas.toDataURL('image/jpeg');
    document.getElementById('camera-preview').style.display = 'block';

    const overlay = document.getElementById('square-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
});

function retakePhoto() {
    document.getElementById('camera-preview').style.display = 'none';
    
    const overlay = document.getElementById('square-overlay');
    if (overlay) {
        overlay.style.display = 'block';
    }
}

async function uploadCapture() {
    const canvas = document.getElementById('canvas');
    const imageData = canvas.toDataURL('image/jpeg');
    
    await sendImageToServer(imageData, true);
}

document.getElementById('file-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('upload-preview-img');
            preview.src = e.target.result;
            document.getElementById('upload-preview').style.display = 'block';
            
            createSquarePreview(preview);
        };
        reader.readAsDataURL(file);
    }
});

function createSquarePreview(imgElement) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    imgElement.onload = function() {
        const originalWidth = imgElement.width;
        const originalHeight = imgElement.height;
        const size = 300;
        
        canvas.width = size;
        canvas.height = size;
        
        const scale = Math.min(size / originalWidth, size / originalHeight);
        const newWidth = originalWidth * scale;
        const newHeight = originalHeight * scale;
        
        const x = (size - newWidth) / 2;
        const y = (size - newHeight) / 2;
        
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, size, size);
        
        ctx.drawImage(imgElement, x, y, newWidth, newHeight);
        imgElement.src = canvas.toDataURL('image/jpeg');
    };
}

document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Пожалуйста, выберите файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('use_camera', 'false');
    
    await sendFormDataToServer(formData);
});

async function sendImageToServer(imageData, isCamera = false) {
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('image_data', imageData);
        
        const response = await fetch('/capture', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResults(result);
        } else {
            throw new Error(result.message || 'Произошла ошибка');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при обработке изображения: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function sendFormDataToServer(formData) {
    showLoading(true);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResults(result);
        } else {
            throw new Error(result.message || 'Произошла ошибка');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при загрузке файла: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showResults(result) {
    const resultsDiv = document.getElementById('results');
    const predictionDiv = document.getElementById('prediction-result');
    
    //заглушка для результатов, заменю на данные от модели
    predictionDiv.innerHTML = `
        <div class="result-item">
            <strong>Изображение обработано успешно!</strong>
            <p>Файл: ${result.filename}</p>
            <p>Путь: ${result.file_path}</p>
            ${result.prediction ? `
                <div class="prediction-info">
                    <h4>Результат распознавания:</h4>
                    <p><strong>Тип цветка:</strong> ${result.prediction.flower_type}</p>
                    <p><strong>Точность:</strong> ${(result.prediction.confidence * 100).toFixed(2)}%</p>
                </div>
            ` : '<p>ИИ модель пока не подключена</p>'}
        </div>
    `;
    
    resultsDiv.style.display = 'block';
    
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});