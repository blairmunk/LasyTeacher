/**
 * Веб-генератор документов для школьной базы заданий
 * ИСПРАВЛЕНО: правильная обработка параметров для быстрых кнопок
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

        // ИСПРАВЛЕНО: Правильное определение answerType для быстрых кнопок
        const withAnswers = button.dataset.withAnswers === '1';
        let answerType;
        
        if (withAnswers) {
            answerType = 'with_answers';  // Для кнопок "PDF + ответы"
        } else {
            answerType = 'tasks_only';    // Для обычных кнопок
        }

        // Получаем параметры из data-атрибутов кнопки
        const params = {
            workId: button.dataset.workId,
            type: button.dataset.type || 'pdf',
            answerType: answerType,       // ИСПРАВЛЕНО: правильный тип
            withAnswers: withAnswers,     // Для совместимости
            format: button.dataset.format || 'A4',
            variantSelection: 'all'       // Быстрые кнопки всегда генерируют все варианты
        };

        console.log('⚡ Быстрая генерация с параметрами:', params);

        await this.generateDocument(params, button);
    }

    async handleAdvancedGeneration(form) {
        if (this.isGenerating) {
            this.showAlert('Генерация уже выполняется, подождите...', 'warning');
            return;
        }

        const formData = new FormData(form);
        
        // РАСШИРЕННЫЕ параметры
        const params = {
            workId: formData.get('work_id'),
            type: formData.get('generator_type'),
            answerType: formData.get('answer_type'), // tasks_only, with_answers, with_short_solutions, with_full_solutions
            format: formData.get('format'),
            variantSelection: formData.get('variant_selection') // all или ID варианта
        };

        // Преобразуем answer_type для совместимости
        params.withAnswers = params.answerType !== 'tasks_only';

        console.log('🔧 Расширенная генерация с параметрами:', params);

        await this.generateDocument(params, form.querySelector('button[type="submit"]'));
    }

    async generateDocument(params, triggerElement) {
        this.isGenerating = true;
        this.setLoadingState(triggerElement, true);

        try {
            console.log(`🌐 Веб-генерация ${params.type} для работы ${params.workId}`);
            
            // Формируем детальное сообщение
            let configMessage = `${params.type.toUpperCase()}`;
            if (params.format && params.type !== 'latex') {
                configMessage += ` (${params.format})`;
            }

            const answerMessages = {
                'tasks_only': '',
                'with_answers': ' • с ответами',
                'with_short_solutions': ' • с краткими решениями', 
                'with_full_solutions': ' • с полными решениями'
            };

            configMessage += answerMessages[params.answerType] || '';

            this.showAlert(`🔄 Генерируется ${configMessage}...`, 'info');

            const response = await fetch(`/works/ajax/generate/${params.workId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    generator_type: params.type,
                    with_answers: params.withAnswers ? '1' : '0',
                    format: params.format || 'A4',
                    answer_type: params.answerType,        // ИСПРАВЛЕНО: всегда передаем правильный тип
                    variant_selection: params.variantSelection || 'all'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert(`✅ ${data.message}`, 'success');
                this.displayResults(data.files);
                console.log(`✅ Генерация завершена: ${data.total_files} файлов`);
            } else {
                this.showAlert(`❌ ${data.error}`, 'danger');
            }

        } catch (error) {
            console.error('❌ Ошибка генерации:', error);
            this.showAlert(`🚨 Ошибка сети: ${error.message}`, 'danger');
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
        console.log(`📢 Показываем уведомление: ${message} (тип: ${type})`);
        
        // Используем существующую Django messages структуру
        let container = document.querySelector('.container');
        if (!container) {
            container = document.querySelector('main') || document.body;
        }
        
        // Удаляем предыдущие алерты от генератора
        const oldAlerts = document.querySelectorAll('.alert.generator-alert');
        oldAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show generator-alert mt-3`;
        alertDiv.innerHTML = `
            <i class="fas fa-info-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Вставляем в начало контейнера
        container.insertBefore(alertDiv, container.firstChild);

        // Увеличиваем время до 10 секунд для важных уведомлений  
        const timeout = type === 'success' ? 10000 : 7000;
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, timeout);
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
