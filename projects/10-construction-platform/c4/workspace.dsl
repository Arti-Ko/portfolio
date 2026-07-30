workspace "Платформа управления стройпроектами" "B2B-платформа полного цикла: ТЗ, закрытый тендер, этапы работ, эскроу и приёмка" {

    model {
        client = person "Клиент" "Создаёт техническое задание, выбирает подрядчика, принимает и оплачивает этапы."
        contractor = person "Подрядчик" "Получает приглашения в тендер, подаёт предложения, сдаёт этапы с отчётами."
        manager = person "Менеджер платформы" "Валидирует ТЗ, ведёт тендер, проверяет приёмку, инициирует выплаты."

        escrowProvider = softwareSystem "Эскроу-провайдер" "Блокировка средств и выплаты подрядчику." {
            tags "External"
        }
        registries = softwareSystem "Реестры" "Проверка компаний при аккредитации подрядчиков." {
            tags "External"
        }

        platform = softwareSystem "Платформа управления стройпроектами" "Единая система ведения строительного проекта от ТЗ до финальной выплаты." {

            clientapp = container "Кабинет клиента" "ТЗ, сравнение предложений, этапы, приёмка." "Web"
            contractorapp = container "Кабинет подрядчика" "Приглашения, подача предложений, сдача этапов." "Web"
            adminapp = container "Админ-панель менеджера" "Управление проектами, статусами и выплатами." "Web"
            api = container "Backend API" "Проекты, этапы, предложения, роли." "Backend"

            workflow = container "Движок состояний" "Допустимые переходы статусов проекта и этапа." "Backend" {
                projectStates = component "Состояния проекта" "Черновик, тендер, в работе, на приёмке, завершён."
                stageStates = component "Состояния этапа" "Шесть статусов и переходы между ними."
                guards = component "Условия перехода" "Кто и при каких условиях может выполнить переход."
                effects = component "Действия при переходе" "Блокировка средств, уведомления, запись в историю."
                rework = component "Возврат на доработку" "Новый цикл этапа с сохранением истории итераций."
            }

            finance = container "Финансовый модуль" "Блокировка средств, выплаты, сверка." "Backend"
            chat = container "Чат проекта" "Переписка клиента, подрядчика и платформы." "Backend"
            auditlog = container "История действий" "Кто, что и когда изменил в проекте." "Backend"

            maindb = container "Основная БД" "Проекты, этапы, предложения, участники." "PostgreSQL" {
                tags "Database"
            }
            filestore = container "Хранилище документов" "Чертежи, фотоотчёты, акты." "Объектное хранилище" {
                tags "Database"
            }
        }

        # Контекст
        client -> platform "Создаёт ТЗ, выбирает подрядчика, принимает этапы"
        contractor -> platform "Подаёт предложения и сдаёт работы"
        manager -> platform "Ведёт проект и управляет выплатами"
        platform -> escrowProvider "Блокирует средства и инициирует выплаты" "HTTPS"
        platform -> registries "Проверяет подрядчиков при аккредитации" "HTTPS"

        # Контейнеры
        client -> clientapp "Работает в браузере" "HTTPS"
        contractor -> contractorapp "Работает в браузере" "HTTPS"
        manager -> adminapp "Работает в браузере" "HTTPS"
        clientapp -> api "Запросы клиента" "REST"
        contractorapp -> api "Запросы подрядчика" "REST"
        adminapp -> api "Запросы менеджера" "REST"
        api -> workflow "Проверяет допустимость перехода"
        api -> maindb "Читает и пишет" "SQL"
        api -> filestore "Сохраняет документы и отчёты"
        api -> chat "Обеспечивает переписку по проекту"
        api -> auditlog "Пишет каждое изменение"
        api -> finance "Инициирует финансовые операции"
        finance -> escrowProvider "Блокировка и выплата" "HTTPS"

        # Компоненты
        api -> projectStates "Запрашивает переход статуса проекта"
        api -> stageStates "Запрашивает переход статуса этапа"
        projectStates -> guards "Проверяет права и условия"
        stageStates -> guards "Проверяет права и условия"
        guards -> effects "Запускает действия перехода"
        effects -> finance "Блокирует или выплачивает средства"
        effects -> auditlog "Фиксирует переход"
        stageStates -> rework "Открывает новый цикл этапа"
        rework -> stageStates "Возвращает этап в работу"
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

        component workflow "WorkflowComponents" "Уровень 3 — компоненты движка состояний" {
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
