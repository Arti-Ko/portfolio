workspace "DubStudio" "Автоматический дубляж видеоконтента на 12 языков: STT, перевод, фонетическая коррекция, TTS" {

    model {
        producer = person "Продюсер" "Ставит задачу на дубляж и принимает готовую дорожку."
        editor = person "Технический редактор" "Правит перевод, транскрипции и тайминги отклонённых выпусков."
        assessor = person "Асессор" "Оценивает естественность звучания в MOS-тесте."

        hosting = softwareSystem "Видеохостинг" "Хранит исходные видео и принимает готовые аудиодорожки." {
            tags "External"
        }
        sttProvider = softwareSystem "STT-провайдер" "Распознавание речи с тайм-кодами." {
            tags "External"
        }
        mtProvider = softwareSystem "MT-провайдер" "Машинный перевод транскрипта." {
            tags "External"
        }
        ttsProvider = softwareSystem "TTS-провайдер" "Синтез речи с поддержкой SSML." {
            tags "External"
        }

        dubstudio = softwareSystem "DubStudio" "Пайплайн автоматического дубляжа с контролем качества." {

            webapp = container "Веб-редактор озвучки" "Сегменты, транскрипции, прослушивание, ручные правки." "SPA"
            api = container "Backend API" "Проекты, выпуски, сегменты, права доступа." "Python, FastAPI"

            orchestrator = container "Оркестратор пайплайна" "Шаги пайплайна, состояние выпуска, повторы и компенсация." "Python, очередь задач" {
                statemachine = component "Машина состояний выпуска" "Переходы между шагами и точки возобновления."
                segmenter = component "Сегментатор" "Разбиение транскрипта по фразам и паузам."
                glossary = component "Применение глоссария" "Термины, имена собственные, аббревиатуры."
                ssml = component "Генератор SSML" "Транскрипции, паузы, ударения, темп."
                timing = component "Выравнивание тайминга" "Сжатие и растяжение под исходную длительность."
                mixer = component "Сведение дорожки" "Громкость, фон, склейка сегментов."
            }

            adapters = container "Адаптеры провайдеров" "Единый контракт поверх разных API, ретраи и лимиты." "Python"
            audio = container "Аудио-процессор" "Демукс, нормализация, сведение, тайминг." "Python, FFmpeg"
            phonetics = container "Модуль фонетики" "Глоссарий и правила транскрипции." "Python"

            qc = container "Контроль качества" "Автоматические метрики и MOS-приёмка." "Python" {
                wer = component "Расчёт WER" "Обратное распознавание синтезированной дорожки."
                drift = component "Детектор рассинхрона" "Отклонение тайм-кодов от исходных."
                loudness = component "Проверка громкости" "LUFS, клиппинг, длинные паузы."
                mos = component "MOS-тест" "Выборка сегментов и сбор оценок асессоров."
                verdict = component "Вердикт приёмки" "Сводный порог по всем метрикам."
            }

            db = container "БД" "Проекты, выпуски, сегменты, глоссарий, метрики." "PostgreSQL" {
                tags "Database"
            }
            storage = container "Объектное хранилище" "Аудио, готовые дорожки, превью." "S3-совместимое" {
                tags "Database"
            }
        }

        # Контекст
        producer -> dubstudio "Ставит задачу и принимает результат"
        editor -> dubstudio "Правит дефекты озвучки"
        assessor -> dubstudio "Ставит оценки MOS"
        dubstudio -> hosting "Скачивает исходник, публикует дорожку" "HTTPS"
        dubstudio -> sttProvider "Отправляет аудио на распознавание" "HTTPS"
        dubstudio -> mtProvider "Отправляет транскрипт на перевод" "HTTPS"
        dubstudio -> ttsProvider "Отправляет размеченный текст на синтез" "HTTPS"

        # Контейнеры
        producer -> webapp "Работает в браузере" "HTTPS"
        editor -> webapp "Правит сегменты" "HTTPS"
        webapp -> api "Запросы данных и операций" "REST"
        api -> db "Читает и пишет" "SQL"
        api -> orchestrator "Ставит задачи пайплайна"
        orchestrator -> audio "Извлечение, сведение, тайминг"
        orchestrator -> phonetics "Применение глоссария и транскрипций"
        orchestrator -> adapters "Вызовы STT, MT и TTS"
        orchestrator -> qc "Запуск проверок качества"
        orchestrator -> hosting "Скачивание и публикация" "HTTPS"
        orchestrator -> db "Хранит состояние выпуска" "SQL"
        adapters -> sttProvider "Распознавание" "HTTPS"
        adapters -> mtProvider "Перевод" "HTTPS"
        adapters -> ttsProvider "Синтез" "HTTPS"
        audio -> storage "Читает и пишет аудио"
        qc -> db "Пишет метрики" "SQL"

        # Компоненты оркестратора
        api -> statemachine "Создаёт выпуск"
        statemachine -> segmenter "Разбивает транскрипт"
        segmenter -> glossary "Передаёт сегменты"
        glossary -> ssml "Передаёт размеченный текст"
        ssml -> adapters "Отправляет на синтез"
        adapters -> timing "Возвращает аудио сегментов"
        timing -> mixer "Передаёт выровненные сегменты"
        mixer -> storage "Сохраняет дорожку"

        # Компоненты контроля качества
        statemachine -> wer "Запускает расчёт"
        statemachine -> drift "Запускает расчёт"
        statemachine -> loudness "Запускает расчёт"
        wer -> verdict "Передаёт значение"
        drift -> verdict "Передаёт значение"
        loudness -> verdict "Передаёт значение"
        mos -> verdict "Передаёт среднюю оценку"
        verdict -> statemachine "Возвращает решение приёмки"
        assessor -> mos "Ставит оценки"
    }

    views {
        systemContext dubstudio "Context" "Уровень 1 — контекст системы" {
            include *
            autolayout lr
        }

        container dubstudio "Containers" "Уровень 2 — контейнеры" {
            include *
            autolayout lr
        }

        component orchestrator "OrchestratorComponents" "Уровень 3 — компоненты оркестратора" {
            include *
            autolayout lr
        }

        component qc "QualityComponents" "Уровень 3 — компоненты контроля качества" {
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
