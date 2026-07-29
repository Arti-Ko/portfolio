workspace "EventBot" "Регистрация на мероприятия, напоминания и NPS-опросы внутри Telegram" {

    model {
        participant = person "Участник" "Регистрируется на мероприятия, подтверждает участие, оценивает событие."
        organizer = person "Организатор" "Заводит мероприятия, управляет списками, читает отчёты."

        telegram = softwareSystem "Telegram Bot API" "Доставка сообщений, inline-кнопки, deep links." {
            tags "External"
        }
        crm = softwareSystem "Google Sheets / Airtable" "CRM-учёт участников на стороне организатора." {
            tags "External"
        }

        eventbot = softwareSystem "EventBot" "Сквозная воронка участника: заявка, напоминание, обратная связь." {

            gateway = container "Bot Gateway" "Приём webhook-апдейтов, роутинг команд и callback-запросов." "Python, aiogram"
            api = container "Registration API" "Бизнес-логика заявок, вместимости, билетов и опросов." "Python, FastAPI" {
                catalog = component "Каталог мероприятий" "Карточка события, разбор deep link."
                capacity = component "Управление вместимостью" "Свободные места, дедлайн регистрации, лист ожидания."
                profile = component "Профиль участника" "Переиспользование данных между мероприятиями."
                validation = component "Валидация" "Формат полей, поиск дублей, нормализация телефона."
                registration = component "Заявки" "Создание, отмена и смена статуса заявки."
                ticket = component "Билеты" "Генерация QR-кода и файла календаря."
                notify = component "Диспетчер уведомлений" "Шаблоны сообщений и окна напоминаний."
                survey = component "NPS-опрос" "Шкала оценки, ветка детрактора, агрегация ответов."
                sync = component "Синхронизация с CRM" "Идемпотентная выгрузка участников."
            }
            fsm = container "FSM Store" "Состояние диалога и черновики анкет." "Redis" {
                tags "Database"
            }
            db = container "Основная БД" "Мероприятия, участники, заявки, ответы NPS." "PostgreSQL" {
                tags "Database"
            }
            scheduler = container "Планировщик" "Ежечасный тик, отбор окон напоминаний." "Celery Beat"
            worker = container "Пул воркеров" "Рассылки, синхронизация, повторы при сбоях." "Celery"
            analytics = container "Аналитический модуль" "Расчёт NPS и воронки регистрации." "Python, SQL"
            admin = container "Панель организатора" "Мероприятия, списки участников, отчёты." "Web"
        }

        # Контекст
        participant -> eventbot "Регистрируется, подтверждает участие, отвечает на опрос"
        organizer -> eventbot "Заводит мероприятия и выгружает отчёты"
        eventbot -> telegram "Отправляет сообщения и билеты" "HTTPS"
        telegram -> eventbot "Передаёт апдейты и нажатия кнопок" "Webhook, HTTPS"
        eventbot -> crm "Синхронизирует участников" "HTTPS"

        # Контейнеры
        participant -> telegram "Пишет боту"
        telegram -> gateway "Доставляет апдейт" "Webhook, HTTPS"
        gateway -> fsm "Читает и пишет состояние диалога"
        gateway -> api "Вызывает бизнес-операции" "REST"
        api -> db "Читает и пишет" "SQL"
        scheduler -> worker "Ставит задачи в очередь"
        worker -> api "Запрашивает данные рассылки" "REST"
        worker -> telegram "Отправляет сообщения" "HTTPS"
        worker -> crm "Выгружает участников пакетами" "HTTPS"
        analytics -> db "Читает" "SQL, только чтение"
        organizer -> admin "Работает в браузере" "HTTPS"
        admin -> api "Управляет мероприятиями" "REST"
        admin -> analytics "Запрашивает отчёты"

        # Компоненты
        gateway -> catalog "Показывает карточку события"
        gateway -> registration "Создаёт и отменяет заявки"
        gateway -> survey "Принимает оценку"
        worker -> notify "Забирает очередь напоминаний"
        worker -> sync "Запускает выгрузку"
        catalog -> capacity "Проверяет наличие мест"
        registration -> capacity "Бронирует и освобождает место"
        registration -> profile "Подтягивает сохранённые данные"
        registration -> validation "Проверяет анкету"
        registration -> ticket "Выпускает билет"
        registration -> notify "Планирует напоминания"
        capacity -> db "SQL"
        registration -> db "SQL"
        profile -> db "SQL"
        survey -> db "SQL"
        sync -> db "SQL"
    }

    views {
        systemContext eventbot "Context" "Уровень 1 — контекст системы" {
            include *
            autolayout lr
        }

        container eventbot "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component api "Components" "Уровень 3 — компоненты Registration API" {
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
