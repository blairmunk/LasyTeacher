function updateSubtopics(topicId) {
    const subtopicSelect = document.getElementById('id_subtopic');
    
    if (!topicId) {
        subtopicSelect.innerHTML = '<option value="">--- Сначала выберите тему ---</option>';
        return;
    }
    
    // Показываем загрузку
    subtopicSelect.innerHTML = '<option value="">--- Загрузка... ---</option>';
    
    // AJAX запрос для получения подтем
    fetch(`/tasks/ajax/load-subtopics/?topic_id=${topicId}`)
        .then(response => response.json())
        .then(data => {
            subtopicSelect.innerHTML = '<option value="">--- Выберите подтему (необязательно) ---</option>';
            
            data.subtopics.forEach(subtopic => {
                const option = document.createElement('option');
                option.value = subtopic.id;
                option.textContent = subtopic.name;
                subtopicSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка загрузки подтем:', error);
            subtopicSelect.innerHTML = '<option value="">--- Ошибка загрузки ---</option>';
        });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const topicSelect = document.getElementById('id_topic');
    if (topicSelect && topicSelect.value) {
        // Если тема уже выбрана (при редактировании) - загружаем подтемы
        updateSubtopics(topicSelect.value);
    }
});
