workspace "Анонимизатор медицинских данных" "NLP-сервис обезличивания ПДн в медицинских документах: ФЗ-152, GDPR, HIPAA Safe Harbor" {

    model {
        doctor = person "Врач" "Работает в МИС; сервис обезличивания для него прозрачен."
        dpo = person "Оператор ПДн" "Верифицирует спорную разметку и согласует раскрытие данных."
        researcher = person "Исследователь" "Получает обезличенные документы для анализа."
        security = person "Служба безопасности" "Расследует инциденты по аудит-логу."

        mis = softwareSystem "МИС" "Медицинская информационная система — источник документов." {
            tags "External"
        }
        idp = softwareSystem "Корпоративный IdP" "Аутентификация и права сотрудников." {
            tags "External"
        }
        siem = softwareSystem "SIEM" "Централизованный сбор событий безопасности." {
            tags "External"
        }

        anonymizer = softwareSystem "Анонимизатор" "Распознавание, маскирование и аудит операций с ПДн." {

            gateway = container "API-шлюз" "mTLS, проверка токена, валидация схемы, лимиты запросов." "Python, FastAPI"

            pipeline = container "NLP-пайплайн" "Извлечение текста, NER, классификация, маскирование." "Python" {
                extract = component "Извлечение текста" "PDF, DOCX, HL7 v2, FHIR, простой текст."
                normalize = component "Нормализация" "Кодировки, переносы, структура документа."
                ner = component "NER-модель" "ФИО, даты, адреса, организации, контакты."
                rules = component "Правила и словари" "СНИЛС, полис ОМС, номера карт, телефоны."
                context = component "Контекстный анализ" "Различение врача и пациента, даты рождения и приёма."
                classify = component "Классификация" "Категории ФЗ-152 и 18 идентификаторов HIPAA."
                confidence = component "Оценка уверенности" "Порог передачи случая оператору ПДн."
                mask = component "Маскирование" "Стратегия по типу: замена, сдвиг дат, обобщение."
                tokenize = component "Токенизация" "Устойчивые псевдонимы в пределах документа."
            }

            verifier = container "Контрольный верификатор" "Независимый поиск остаточных ПДн другим методом." "Python"
            console = container "Консоль оператора" "Верификация разметки, карантин, согласование раскрытий." "Web"
            reid = container "Сервис деанонимизации" "Выборочное раскрытие токен-мапы по согласованному запросу." "Python"

            docdb = container "Хранилище документов" "Обезличенные тексты, разметка, метаданные." "PostgreSQL" {
                tags "Database"
            }
            vault = container "Хранилище токен-мапы" "Соответствие токен и реальное значение, отдельный контур." "PostgreSQL" {
                tags "Vault"
            }
            audit = container "Аудит-лог" "Неизменяемые записи операций с ПДн, цепочка хешей." "Append-only" {
                tags "Database"
            }
        }

        # Контекст
        doctor -> mis "Создаёт медицинские документы"
        mis -> anonymizer "Отправляет документ на обезличивание" "REST, mTLS"
        anonymizer -> mis "Возвращает обезличенный документ" "REST"
        dpo -> anonymizer "Верифицирует разметку и согласует раскрытие"
        researcher -> anonymizer "Запрашивает обезличенные данные"
        anonymizer -> siem "Передаёт события безопасности"
        security -> siem "Расследует инциденты"
        anonymizer -> idp "Проверяет права сотрудников" "OIDC"

        # Контейнеры
        mis -> gateway "POST /anonymize" "REST, mTLS"
        gateway -> pipeline "Передаёт документ на обработку"
        gateway -> audit "Пишет событие обращения"
        gateway -> idp "Проверяет токен" "OIDC"
        pipeline -> docdb "Сохраняет обезличенный текст и разметку" "SQL"
        pipeline -> vault "Сохраняет соответствия токенов" "SQL"
        pipeline -> verifier "Запускает контрольную проверку"
        pipeline -> audit "Пишет событие обработки"
        verifier -> docdb "Читает результат обезличивания" "SQL"
        dpo -> console "Работает в браузере" "HTTPS"
        console -> docdb "Читает и правит разметку" "SQL"
        console -> reid "Инициирует согласованное раскрытие"
        reid -> vault "Читает только разрешённые поля" "SQL"
        reid -> audit "Пишет факт раскрытия"
        audit -> siem "Экспортирует события" "Syslog"
        researcher -> docdb "Получает выгрузку обезличенных документов"

        # Компоненты
        gateway -> extract "Передаёт документ"
        extract -> normalize "Передаёт сырой текст"
        normalize -> ner "Передаёт нормализованный текст"
        normalize -> rules "Передаёт нормализованный текст"
        ner -> context "Передаёт найденные сущности"
        rules -> context "Передаёт найденные сущности"
        context -> classify "Передаёт разрешённые сущности"
        classify -> confidence "Передаёт классифицированные сущности"
        confidence -> mask "Передаёт сущности выше порога"
        confidence -> console "Отправляет спорные случаи оператору"
        mask -> tokenize "Передаёт сущности под псевдонимизацию"
        mask -> docdb "Записывает обезличенный текст"
        tokenize -> vault "Записывает соответствия"
    }

    views {
        systemContext anonymizer "Context" "Уровень 1 — контекст системы" {
            include *
            autolayout lr
        }

        container anonymizer "Containers" "Уровень 2 — контейнеры и контуры хранения" {
            include *
            autolayout lr
        }

        component pipeline "PipelineComponents" "Уровень 3 — компоненты NLP-пайплайна" {
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
            element "Vault" {
                shape Cylinder
                background #6b2d2d
                color #ffffff
            }
            element "External" {
                background #4a4f5a
                color #ffffff
            }
        }
    }
}
