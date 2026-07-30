workspace "ЭТП морских грузоперевозок" "Электронная торговая площадка: двухэтапные торги, отслеживание судов, безбумажный документооборот" {

    model {
        cargoOwner = person "Грузовладелец" "Публикует лоты на перевозку и следит за грузом."
        shipOwner = person "Судовладелец" "Участвует в торгах и ведёт рейсы."
        portAuthority = person "Администрация порта" "Подтверждает слоты захода."
        terminalOwner = person "Владелец терминала" "Фиксирует погрузку и разгрузку."

        aisProvider = softwareSystem "Поставщик данных AIS" "Координаты судов в реальном времени." {
            tags "External"
        }
        ca = softwareSystem "Удостоверяющий центр" "Квалифицированная электронная подпись." {
            tags "External"
        }
        registries = softwareSystem "Реестры" "Компании, суда, ледовые классы, допуски, страховое покрытие." {
            tags "External"
        }
        charts = softwareSystem "Картографический сервис" "Морские карты и ледовая обстановка." {
            tags "External"
        }

        etp = softwareSystem "ЭТП морских перевозок" "Торги, документооборот и отслеживание рейса." {

            web = container "Веб-портал" "Лоты, торги, документы, карта." "SPA"
            mobile = container "Мобильное приложение" "Оперативные действия: слот, погрузка, статус." "Mobile"
            api = container "Backend API" "Лоты, сделки, участники, права доступа." "Backend"

            auction = container "Тендерный движок" "Этапы процедуры, ставки, таймеры, определение победителя." "Backend" {
                lotLifecycle = component "Жизненный цикл лота" "Черновик, предотбор, торги, завершение."
                prequalification = component "Предотбор" "Приём заявок и проверка критериев допуска."
                bidding = component "Приём ставок" "Сериализация конкурентных ставок и валидация шага."
                timers = component "Таймеры этапов" "Сроки этапов и продление при ставке в конце."
                winnerSelection = component "Определение победителя" "Критерии и разрешение равенства предложений."
                protocolLog = component "Протокол процедуры" "Неизменяемая запись хода торгов."
            }

            verification = container "Служба проверки участников" "Реестры, допуски, ледовый класс, страховое покрытие." "Backend"
            documents = container "Документооборот" "Шаблоны, версии документов, маршруты подписания." "Backend"
            tracking = container "Служба отслеживания" "Приём AIS, история трека, детекция отклонений." "Backend"
            gis = container "ГИС-слой" "Морские карты и рендер позиций судов." "Backend"

            maindb = container "Основная БД" "Лоты, сделки, участники, документы." "PostgreSQL" {
                tags "Database"
            }
            trackdb = container "Хранилище треков" "Координаты судов во времени." "Time-series DB" {
                tags "Database"
            }
        }

        # Контекст
        cargoOwner -> etp "Публикует лоты и следит за грузом"
        shipOwner -> etp "Участвует в торгах и ведёт рейсы"
        portAuthority -> etp "Подтверждает слоты"
        terminalOwner -> etp "Фиксирует погрузку и разгрузку"
        etp -> aisProvider "Получает координаты судов"
        etp -> ca "Подписывает документы"
        etp -> registries "Проверяет участников и суда"
        etp -> charts "Отображает морскую обстановку"

        # Контейнеры
        cargoOwner -> web "Работает в браузере" "HTTPS"
        shipOwner -> web "Участвует в торгах" "HTTPS"
        shipOwner -> mobile "Оперативные действия по рейсу" "HTTPS"
        portAuthority -> mobile "Подтверждает слоты" "HTTPS"
        web -> api "Запросы данных и операций" "REST"
        mobile -> api "Запросы данных и операций" "REST"
        api -> maindb "Читает и пишет" "SQL"
        api -> auction "Операции процедуры торгов"
        api -> verification "Запускает проверку участника"
        api -> documents "Формирует и маршрутизирует документы"
        verification -> registries "Запрашивает данные" "HTTPS"
        documents -> ca "Отправляет на подписание" "HTTPS"
        tracking -> aisProvider "Принимает поток координат"
        tracking -> trackdb "Пишет точки трека"
        tracking -> api "Передаёт события отклонений"
        gis -> trackdb "Читает позиции"
        gis -> charts "Запрашивает подложку карт"
        web -> gis "Отображает карту"

        # Компоненты
        api -> lotLifecycle "Управляет состоянием лота"
        lotLifecycle -> prequalification "Открывает этап предотбора"
        prequalification -> verification "Проверяет участника и судно"
        lotLifecycle -> bidding "Открывает этап торгов"
        bidding -> timers "Продлевает этап при поздней ставке"
        timers -> winnerSelection "Закрывает торги по истечении срока"
        winnerSelection -> protocolLog "Фиксирует результат"
        protocolLog -> maindb "Сохраняет протокол" "SQL"
    }

    views {
        systemContext etp "Context" "Уровень 1 — контекст" {
            include *
            autolayout lr
        }

        container etp "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component auction "AuctionComponents" "Уровень 3 — компоненты тендерного движка" {
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
