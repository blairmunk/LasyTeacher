/**
 * Веб-генератор документов для школьной базы заданий
 * Интегрируется с существующим Bootstrap 5 интерфейсом
 */

class DocumentGenerator {
    constructor() {
        this.isGenerating = false;
        this.initEventListeners();
    }

    initEventListeners() {
        // Делегирование событий для динамических кнопок
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-generate-doc')) {
                e.preventDefault();
                this.handleGenerateClick(e.target);
            }
        });

        // Обработка формы расширенной генерации
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#advanced-generation-form')) {
                e.preventDefault();
                this.handleAdvancedGeneration(e.target);
            }
        });
    }

    async handleGenerateClick(button) {
        if (this.isGenerating) {
            this.showAlert('Генерация уже выполняется, подождите...', 'warning');
            return;
        }

        // Получаем параметры из data-атрибутов кнопки
        const params = {
            workId: button.dataset.workId,
            type: button.dataset.type || 'pdf',
            withAnswers: button.dataset.withAnswers === '1',
            format: button.dataset.format || 'A4'
        };

        await this.generateDocument(params, button);
    }

    async handleAdvancedGeneration(form) {
        if (this.isGenerating) {
            this.showAlert('Генерация уже выполняется, подождите...', 'warning');
            return;
        }

        const formData = new FormData(form);
        const params = {
            workId: formData.get('work_id'),
            type: formData.get('generator_type'),
            withAnswers: formData.get('with_answers') === '1',
            format: formData.get('format')
        };

        await this.generateDocument(params, form.querySelector('button[type="submit"]'));
    }

    async generateDocument(params, triggerElement) {
        this.isGenerating = true;
        this.setLoadingState(triggerElement, true);

        try {
            console.log(`🌐 Веб-генерация ${params.type} для работы ${params.workId}`);

            const response = await fetch(`/works/ajax/generate/${params.workId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    generator_type: params.type,
                    with_answers: params.withAnswers ? '1' : '0',
                    format: params.format
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert(data.message, 'success');
                this.displayResults(data.files);
                console.log(`✅ Генерация завершена: ${data.total_files} файлов`);
            } else {
                this.showAlert(`Ошибка: ${data.error}`, 'danger');
            }

        } catch (error) {
            console.error('❌ Ошибка генерации:', error);
            this.showAlert(`Ошибка сети: ${error.message}`, 'danger');
        } finally {
            this.isGenerating = false;
            this.setLoadingState(triggerElement, false);
        }
    }

    displayResults(files) {
        if (!files || files.length === 0) return;

        // Найти или создать контейнер результатов
        let resultsContainer = document.getElementById('generation-results');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'generation-results';
            resultsContainer.className = 'mt-4';
            
            // Вставляем после блока генерации
            const genBlock = document.querySelector('.document-generation-block');
            genBlock.parentNode.insertBefore(resultsContainer, genBlock.nextSibling);
        }

        // Создаем HTML с файлами
        let html = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-file-download"></i> Созданные документы</h6>
                </div>
                <div class="card-body">
                    <div class="list-group list-group-flush">
        `;

        files.forEach(file => {
            const iconClass = this.getFileIcon(file.name);
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <i class="${iconClass} me-2"></i>
                        <strong>${file.name}</strong>
                        <br><small class="text-muted">Размер: ${file.size}</small>
                    </div>
                    <a href="${file.download_url}" class="btn btn-outline-primary btn-sm" target="_blank">
                        <i class="fas fa-download"></i> Скачать
                    </a>
                </div>
            `;
        });

        html += `
                    </div>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = html;
    }

    getFileIcon(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        const icons = {
            'pdf': 'fas fa-file-pdf text-danger',
            'html': 'fas fa-file-code text-info', 
            'tex': 'fas fa-file-alt text-success',
            'latex': 'fas fa-file-alt text-success'
        };
        return icons[extension] || 'fas fa-file';
    }

    setLoadingState(element, isLoading) {
        if (!element) return;

        if (isLoading) {
            element.disabled = true;
            element.dataset.originalHTML = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Генерируется...';
        } else {
            element.disabled = false;
            element.innerHTML = element.dataset.originalHTML || element.innerHTML;
        }
    }

    showAlert(message, type = 'info') {
        // Используем существующую Django messages структуру
        const container = document.querySelector('.container');
        
        // Удаляем предыдущие алерты от генератора
        const oldAlerts = document.querySelectorAll('.alert.generator-alert');
        oldAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show generator-alert`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Вставляем сразу после навбара
        const firstChild = container.firstElementChild;
        container.insertBefore(alertDiv, firstChild);

        // Автоматически убираем через 7 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 7000);
    }

    getCSRFToken() {
        // Получаем CSRF токен из мета-тега или cookie
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.content ||
               this.getCookie('csrftoken');
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.documentGenerator = new DocumentGenerator();
    console.log('📱 Веб-генератор документов инициализирован');
});
