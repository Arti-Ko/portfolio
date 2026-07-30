workspace "Платформа AI-помощников" "Четыре on-premises AI-продукта в закрытом контуре страховой компании" {

    model {
        employee = person "Сотрудник" "Ищет норму в базе, готовит закупочную документацию."
        doctor = person "Врач-эксперт" "Согласует спорные медицинские назначения."
        security = person "Сотрудник службы безопасности" "Проверяет контрагентов перед сделкой."
        aiadmin = person "Администратор ИИ" "Ведёт базу знаний, модели и пороги."

        directory = softwareSystem "Служба каталога" "Аутентификация сотрудников и группы доступа." {
            tags "External"
        }
        docflow = softwareSystem "СЭД" "Хранит нормативные акты и их редакции." {
            tags "External"
        }
        coresystems = softwareSystem "Учётные системы" "Полисы, договоры, контрагенты, решения." {
            tags "External"
        }
        registries = softwareSystem "Государственные реестры" "Более 30 источников для проверки контрагентов." {
            tags "External"
        }
        clinics = softwareSystem "Клиники" "Присылают протоколы медицинских назначений." {
            tags "External"
        }

        platform = softwareSystem "Платформа AI-помощников" "Общая платформа для четырёх AI-продуктов." {

            ui = container "Единый веб-интерфейс" "Четыре продукта с общей авторизацией." "SPA"
            gateway = container "API-шлюз" "Аутентификация, квоты запросов, аудит обращений." "Python"

            orchestrator = container "Оркестратор сценариев" "Шаги сценария, вызовы инструментов, ветвление." "Агентный фреймворк" {
                router = component "Маршрутизатор сценариев" "Определяет продукт и сценарий обработки."
                acl = component "Фильтр доступа" "Сужает область поиска по группам пользователя."
                retrieve = component "Извлечение" "Гибридный поиск и переранжирование фрагментов."
                contextbuilder = component "Сборка контекста" "Бюджет токенов и приоритет фрагментов."
                guard = component "Защита промпта" "Фильтрация инъекций и изоляция инструкций от данных."
                grounding = component "Проверка обоснованности" "Сверка утверждений ответа с источниками."
                citation = component "Формирование ссылок" "Пункт, редакция и дата документа."
            }

            inference = container "Инференс-сервис" "Локальные модели, очередь и приоритеты запросов." "GPU-кластер"
            indexer = container "Служба индексации" "Парсинг, OCR, нарезка на фрагменты, эмбеддинги." "Python"
            rules = container "Движок правил" "Детерминированные клинические проверки." "Python"
            connectors = container "Коннекторы реестров" "Опрос источников и нормализация ответов." "Python"

            vectordb = container "Векторная база" "Фрагменты документов и их эмбеддинги." "Vector DB" {
                tags "Database"
            }
            ftsindex = container "Полнотекстовый индекс" "Точные совпадения: номера приказов, коды." "Search index" {
                tags "Database"
            }
            knowledgegraph = container "Граф знаний" "МКБ-10 и клинические рекомендации с версиями." "Graph DB" {
                tags "Database"
            }
            auditlog = container "Журнал" "Запросы, использованные источники, решения." "PostgreSQL" {
                tags "Database"
            }
        }

        # Контекст
        employee -> platform "Задаёт вопросы по базе, готовит закупки"
        doctor -> platform "Разбирает спорные назначения"
        security -> platform "Запрашивает паспорт проверки контрагента"
        aiadmin -> platform "Ведёт базу знаний и конфигурацию моделей"
        clinics -> platform "Присылают протоколы назначений"
        platform -> directory "Проверяет права" "LDAP"
        platform -> docflow "Забирает документы и редакции"
        platform -> coresystems "Читает данные и пишет решения"
        platform -> registries "Опрашивает источники" "HTTPS"

        # Контейнеры
        employee -> ui "Работает в браузере" "HTTPS"
        doctor -> ui "Разбирает спорные случаи" "HTTPS"
        ui -> gateway "Запросы пользователя" "REST"
        gateway -> directory "Проверяет группы доступа" "LDAP"
        gateway -> orchestrator "Передаёт сценарий"
        gateway -> auditlog "Пишет событие обращения"
        orchestrator -> inference "Отправляет промпт и контекст"
        orchestrator -> vectordb "Векторный поиск"
        orchestrator -> ftsindex "Полнотекстовый поиск"
        orchestrator -> rules "Запускает проверку правил"
        orchestrator -> connectors "Опрашивает реестры"
        orchestrator -> auditlog "Пишет использованные источники"
        rules -> knowledgegraph "Запрашивает онтологию и версии рекомендаций"
        connectors -> registries "Запрашивает данные" "HTTPS"
        indexer -> docflow "Забирает документы"
        indexer -> vectordb "Пишет фрагменты"
        indexer -> ftsindex "Пишет термины"
        aiadmin -> indexer "Запускает переиндексацию"

        # Компоненты
        gateway -> router "Передаёт запрос"
        router -> acl "Определяет область поиска"
        acl -> retrieve "Передаёт разрешённую область"
        retrieve -> vectordb "Векторный поиск"
        retrieve -> ftsindex "Полнотекстовый поиск"
        retrieve -> contextbuilder "Передаёт отобранные фрагменты"
        contextbuilder -> guard "Передаёт собранный контекст"
        guard -> inference "Отправляет защищённый промпт"
        inference -> grounding "Возвращает ответ"
        grounding -> citation "Передаёт подтверждённые утверждения"
        citation -> auditlog "Фиксирует источники ответа"
    }

    views {
        systemContext platform "Context" "Уровень 1 — контекст" {
            include *
            autolayout lr
        }

        container platform "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component orchestrator "OrchestratorComponents" "Уровень 3 — компоненты оркестратора" {
            include *
            autolayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #2b5d8a
                color #ffffff
            }
            element "Software System" {
                background #1a4d7a
                color #ffffff
            }
            element "Container" {
                background #2f3542
                color #ffffff
            }
            element "Component" {
                background #2f3542
                color #ffffff
            }
            element "Database" {
                shape Cylinder
                background #3d5a3d
                color #ffffff
            }
            element "External" {
                background #4a4f5a
                color #ffffff
            }
        }
    }
}
