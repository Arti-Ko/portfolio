workspace "Трекер симптомов онкопациента" "Дневник симптомов, справочник и календарь препаратов в информационно-просветительском формате" {

    model {
        patient = person "Пациент" "Ведёт дневник симптомов и принимает препараты по схеме."
        doctor = person "Лечащий врач" "Видит динамику пациента между приёмами."
        editor = person "Медицинский редактор" "Ведёт справочник и шаблоны симптомов по нозологиям."

        pushservice = softwareSystem "Сервисы уведомлений" "Доставка напоминаний на устройство." {
            tags "External"
        }
        b2b = softwareSystem "B2B-потребители данных" "Обезличенная аналитика для фармы, страховых и клиник. За пределами MVP." {
            tags "External"
        }

        tracker = softwareSystem "Трекер симптомов" "Дневник, справочник и календарь приёма препаратов." {

            mobile = container "Мобильное приложение" "Дневник, календарь, справочник." "iOS, Android"
            web = container "Кабинет врача" "Динамика пациентов и флаги эскалации." "Web"
            api = container "Backend API" "Записи дневника, схемы приёма, доступы." "Backend"

            rules = container "Модуль оценки" "Шкалы тяжести и пороги эскалации." "Backend" {
                nozology = component "Профиль нозологии" "Какие симптомы отслеживаются при диагнозе."
                scale = component "Шкала тяжести" "Перевод ответа пациента в клиническую степень."
                threshold = component "Пороги эскалации" "Условия поднятия флага врачу."
                trend = component "Анализ динамики" "Ухудшение за период вместо разового пика."
                advice = component "Подбор справки" "Выбор статьи справочника без рекомендаций по лечению."
            }

            scheduler = container "Планировщик" "Окна приёма и напоминания." "Backend"
            content = container "Контентная служба" "Справочник и шаблоны симптомов." "Backend"

            db = container "БД" "Записи дневника, схемы приёма, приверженность." "PostgreSQL" {
                tags "Database"
            }
        }

        # Контекст
        patient -> tracker "Отмечает симптомы и приёмы препаратов"
        tracker -> patient "Показывает справочную информацию"
        doctor -> tracker "Смотрит динамику и флаги"
        editor -> tracker "Ведёт справочник и шаблоны"
        tracker -> pushservice "Отправляет напоминания"
        tracker -> b2b "Передаёт обезличенные данные — после MVP"

        # Контейнеры
        patient -> mobile "Ведёт дневник" "HTTPS"
        doctor -> web "Смотрит пациентов" "HTTPS"
        editor -> content "Редактирует контент" "HTTPS"
        mobile -> api "Запросы пациента" "REST"
        web -> api "Запросы врача" "REST"
        api -> db "Читает и пишет" "SQL"
        api -> rules "Оценивает запись дневника"
        api -> content "Запрашивает шаблоны и статьи"
        scheduler -> db "Читает схемы приёма" "SQL"
        scheduler -> pushservice "Ставит напоминания" "HTTPS"
        pushservice -> mobile "Доставляет уведомление"

        # Компоненты
        api -> nozology "Передаёт запись и диагноз"
        nozology -> scale "Передаёт применимый шаблон"
        scale -> threshold "Передаёт рассчитанную степень"
        threshold -> trend "Проверяет динамику за период"
        trend -> advice "Запрашивает подходящую статью"
        threshold -> db "Сохраняет факт эскалации" "SQL"
    }

    views {
        systemContext tracker "Context" "Уровень 1 — контекст" {
            include *
            autolayout lr
        }

        container tracker "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component rules "RulesComponents" "Уровень 3 — компоненты модуля оценки" {
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
