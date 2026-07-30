workspace "Портал массового найма" "Внутренняя HR-платформа для найма самозанятых и ИП: две дочерние компании, шесть интеграций, 80 тысяч пользователей" {

    model {
        candidate = person "Кандидат" "Заполняет анкету и проходит проверки."
        hrmanager = person "HR-менеджер" "Ведёт поток кандидатов и принимает решения."
        head = person "Руководитель отдела" "Утверждает найм в своём подразделении."
        bddSpecialist = person "Специалист по безопасности движения" "Оценивает профиль водителя и допуск."
        securityOfficer = person "Офицер безопасности" "Проверяет кандидатов и согласует допуск."
        mentor = person "Наставник" "Ведёт адаптацию вышедших на работу."

        taxapi = softwareSystem "Налоговые API" "Публичный и внутренний интерфейсы проверки статуса." {
            tags "External"
        }
        crm = softwareSystem "CRM" "Двусторонний обмен данными по кандидатам." {
            tags "External"
        }
        medpartner = softwareSystem "Медицинский партнёр" "Запись на осмотр и выдача заключений." {
            tags "External"
        }
        eventbus = softwareSystem "Событийная шина" "Точки работы и историческая миграция данных." {
            tags "External"
        }
        secretstore = softwareSystem "Секрет-хранилище" "Ключи шифрования и доступ к персональным данным." {
            tags "External"
        }

        portal = softwareSystem "Портал массового найма" "Единая воронка кандидата для двух дочерних компаний." {

            candidateUi = container "Кабинет кандидата" "Анкета из шести блоков и статус заявки." "Web"
            hrUi = container "Рабочее место HR" "Поток кандидатов, решения, отчёты." "Web"
            api = container "Backend API" "Анкеты, статусы, ролевая модель, права доступа." "Backend"
            funnel = container "Движок воронки" "Состояния заявки и ветвление по дочерней компании." "Backend"
            checks = container "Служба проверок" "Налоговый статус, служба безопасности, документы." "Backend"
            clearance = container "Контур допуска" "Медицинский контроль и профиль безопасности движения." "Backend"

            integration = container "Интеграционный слой" "Адаптеры внешних систем, очереди, повторы, лимиты." "Backend" {
                queue = component "Очередь задач" "Приоритеты, повторы, экспоненциальная задержка."
                limiter = component "Ограничитель скорости" "Соблюдение лимита вызовов каждого источника."
                breaker = component "Предохранитель" "Отключение источника при серии отказов."
                taxAdapter = component "Адаптер налоговых API" "Публичный и внутренний интерфейсы за единым контрактом."
                crmAdapter = component "Адаптер CRM" "Двусторонний обмен и разрешение конфликтов."
                medAdapter = component "Адаптер медпартнёра" "Запись на осмотр и приём заключений."
                publisher = component "Публикация событий" "Исходящие события найма."
                outbox = component "Исходящий журнал" "Гарантия доставки событий."
            }

            maindb = container "Основная БД" "Кандидаты, заявки, шаги, решения." "PostgreSQL с секционированием" {
                tags "Database"
            }
            docstore = container "Хранилище документов" "Сканы и заключения в зашифрованном виде." "Объектное хранилище" {
                tags "Database"
            }
        }

        # Контекст
        candidate -> portal "Подаёт анкету и следит за статусом"
        hrmanager -> portal "Ведёт поток кандидатов"
        head -> portal "Утверждает найм"
        bddSpecialist -> portal "Оценивает допуск водителя"
        securityOfficer -> portal "Проверяет кандидатов"
        mentor -> portal "Ведёт адаптацию"
        portal -> taxapi "Проверяет налоговый статус" "HTTPS"
        portal -> crm "Обменивается данными по кандидатам" "HTTPS"
        portal -> medpartner "Получает медицинские заключения" "HTTPS"
        portal -> eventbus "Публикует и читает события"
        portal -> secretstore "Получает ключи доступа"

        # Контейнеры
        candidate -> candidateUi "Заполняет анкету" "HTTPS"
        hrmanager -> hrUi "Работает с потоком" "HTTPS"
        bddSpecialist -> hrUi "Оценивает профиль водителя" "HTTPS"
        securityOfficer -> hrUi "Проводит проверку" "HTTPS"
        candidateUi -> api "Запросы кандидата" "REST"
        hrUi -> api "Запросы сотрудника" "REST"
        api -> maindb "Читает и пишет" "SQL"
        api -> docstore "Сохраняет и выдаёт документы"
        api -> secretstore "Получает ключи шифрования"
        api -> funnel "Управляет состоянием заявки"
        funnel -> checks "Запускает проверки"
        funnel -> clearance "Запускает контур допуска"
        checks -> integration "Обращается к внешним источникам"
        clearance -> integration "Обращается к медицинскому партнёру"
        integration -> taxapi "Проверка статуса" "HTTPS"
        integration -> crm "Обмен данными" "HTTPS"
        integration -> medpartner "Запись и заключения" "HTTPS"
        integration -> eventbus "Публикация событий"

        # Компоненты
        checks -> queue "Ставит задачу проверки"
        clearance -> queue "Ставит задачу медосмотра"
        queue -> limiter "Передаёт задачу с учётом приоритета"
        limiter -> breaker "Пропускает в пределах лимита"
        breaker -> taxAdapter "Вызывает при доступном источнике"
        breaker -> crmAdapter "Вызывает при доступном источнике"
        breaker -> medAdapter "Вызывает при доступном источнике"
        taxAdapter -> taxapi "Запрос статуса" "HTTPS"
        crmAdapter -> crm "Обмен данными" "HTTPS"
        medAdapter -> medpartner "Запись и приём заключений" "HTTPS"
        api -> outbox "Пишет событие в одной транзакции с данными"
        publisher -> outbox "Читает неопубликованные события"
        publisher -> eventbus "Публикует событие"
    }

    views {
        systemContext portal "Context" "Уровень 1 — контекст" {
            include *
            autolayout lr
        }

        container portal "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component integration "IntegrationComponents" "Уровень 3 — компоненты интеграционного слоя" {
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
