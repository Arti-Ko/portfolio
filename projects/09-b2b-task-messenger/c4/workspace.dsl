workspace "Мессенджер клиентских задач" "Веб-мессенджер с двусторонней интеграцией с CRM: два канала над одной сущностью задачи" {

    model {
        client = person "Клиент" "Ставит задачи в привычном мессенджере и оценивает работу."
        employee = person "Сотрудник" "Выполняет задачи в веб-интерфейсе."
        manager = person "Руководитель" "Следит за соблюдением нормативов."
        admin = person "Администратор" "Управляет ролями и настройками."

        telegram = softwareSystem "Telegram" "Привычный канал клиента." {
            tags "External"
        }
        crm = softwareSystem "Корпоративная CRM" "Сделки и клиентская база." {
            tags "External"
        }
        pushservice = softwareSystem "Сервисы push-уведомлений" "Доставка уведомлений на устройства." {
            tags "External"
        }

        messenger = softwareSystem "Мессенджер задач" "Чаты, задачи, оценки и синхронизация с CRM." {

            spa = container "Веб-приложение" "Чаты, задачи, личный кабинет." "SPA"

            gateway = container "Real-time шлюз" "Постоянные соединения, присутствие, доставка событий." "Backend" {
                connections = component "Менеджер соединений" "Установка, heartbeat, переподключение."
                connAuth = component "Аутентификация соединения" "Проверка токена при подключении и разрыв при отзыве доступа."
                subscriptions = component "Подписки на каналы" "Кто на какие чаты подписан."
                fanout = component "Рассылка событий" "Доставка события подписчикам чата."
                presence = component "Присутствие" "Онлайн, печатает, прочитано."
                backlog = component "Догрузка пропущенного" "Сообщения за время отключения клиента."
            }

            botconnector = container "Бот-коннектор" "Приём апдейтов и отправка сообщений в мессенджер." "Backend"
            api = container "Backend API" "Задачи, чаты, роли, оценки, нормативы." "Backend"
            syncservice = container "Служба синхронизации" "Исходящий журнал и разрешение конфликтов с CRM." "Backend"

            maindb = container "Основная БД" "Задачи, сообщения, пользователи, история статусов." "PostgreSQL" {
                tags "Database"
            }
            cache = container "Кеш и присутствие" "Онлайн-статусы и очереди доставки." "Redis" {
                tags "Database"
            }
            filestore = container "Хранилище вложений" "Файлы и изображения из чатов." "Объектное хранилище" {
                tags "Database"
            }
        }

        # Контекст
        client -> telegram "Ставит задачи и получает ответы"
        telegram -> messenger "Передаёт апдейты"
        messenger -> telegram "Отправляет сообщения клиенту"
        employee -> messenger "Выполняет задачи"
        manager -> messenger "Смотрит нормативы и эскалации"
        admin -> messenger "Управляет ролями"
        messenger -> crm "Двусторонний обмен по сделкам"
        messenger -> pushservice "Отправляет уведомления"

        # Контейнеры
        employee -> spa "Работает с задачами" "HTTPS"
        manager -> spa "Смотрит отчёты" "HTTPS"
        spa -> api "Запросы данных и операций" "REST"
        spa -> gateway "Постоянное соединение" "WebSocket"
        telegram -> botconnector "Доставляет апдейт" "Webhook"
        botconnector -> api "Вызывает операции по задаче" "REST"
        botconnector -> telegram "Отправляет сообщение" "HTTPS"
        api -> maindb "Читает и пишет" "SQL"
        api -> filestore "Сохраняет и отдаёт вложения"
        api -> gateway "Публикует события для доставки"
        api -> syncservice "Ставит событие на синхронизацию"
        gateway -> cache "Хранит присутствие и очереди"
        syncservice -> crm "Обмен данными" "HTTPS"
        syncservice -> maindb "Читает исходящий журнал" "SQL"
        api -> pushservice "Отправляет уведомление офлайн-пользователю"

        # Компоненты
        spa -> connections "Устанавливает соединение" "WebSocket"
        connections -> connAuth "Проверяет токен"
        connAuth -> subscriptions "Подписывает на доступные чаты"
        api -> fanout "Передаёт новое событие"
        fanout -> subscriptions "Определяет получателей"
        subscriptions -> spa "Доставляет событие"
        connections -> presence "Обновляет статус пользователя"
        presence -> cache "Хранит онлайн-статусы"
        connections -> backlog "Запрашивает пропущенное при переподключении"
        backlog -> cache "Читает очередь недоставленного"
    }

    views {
        systemContext messenger "Context" "Уровень 1 — контекст" {
            include *
            autolayout lr
        }

        container messenger "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component gateway "GatewayComponents" "Уровень 3 — компоненты real-time шлюза" {
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
