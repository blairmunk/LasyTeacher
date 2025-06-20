// Простой JavaScript для админки Django - точно такой же как в пользовательском интерфейсе
document.addEventListener('DOMContentLoaded', function() {
    const topicSelect = document.getElementById('id_topic');
    const subtopicSelect = document.getElementById('id_subtopic');
    
    if (topicSelect && subtopicSelect) {
        topicSelect.addEventListener('change', function() {
            const topicId = this.value;
            
            // Очищаем список подтем
            subtopicSelect.innerHTML = '<option value="">--- Загрузка... ---</option>';
            
            if (topicId) {
                // ИСПОЛЬЗУЕМ ТОТ ЖЕ ENDPOINT что работает в пользовательском интерфейсе
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
            } else {
                subtopicSelect.innerHTML = '<option value="">--- Выберите подтему (необязательно) ---</option>';
            }
        });
    }
});
