# BPMN 2.0 — Telegram-бот регистрации на мероприятия

Три сквозных процесса покрывают жизненный цикл участника: регистрация,
удержание до события, обратная связь после него.

Исходники в нотации BPMN 2.0 лежат в [diagrams/](diagrams/) и открываются в
Camunda Modeler, bpmn.io, Visual Paradigm или любом инструменте, читающем
BPMN 2.0 XML. Схемы ниже сгенерированы из тех же моделей, что и `.bpmn`, —
разойтись они не могут.

## Соглашения нотации

| Элемент | Как читать |
|---|---|
| Дорожка (lane) | Кто владеет шагом: участник, бот, серверная логика, внешняя система |
| Прямоугольник | Задача. Синяя — ручная (user task), серая — автоматическая (service task), фиолетовая — отправка сообщения (send task) |
| Ромб | Исключающий шлюз: ровно одна исходящая ветка |
| Зелёный круг | Стартовое событие (сообщение или таймер) |
| Красный круг | Конечное событие — все ветки процесса завершены явно |

---

## 1. Регистрация участника

Основной процесс. Точка входа — deep link вида `t.me/bot?start=event_42`,
который организатор публикует в анонсе. Бот сразу знает, о каком мероприятии
идёт речь, — участник не выбирает событие из списка вручную. Это ключевое
решение для конверсии 85%: из воронки убран целый шаг.

**Файл:** [`diagrams/01-registration.bpmn`](diagrams/01-registration.bpmn)

<!-- diagram:01-registration -->
```mermaid
flowchart LR
    subgraph Lane_participant["Участник"]
        direction LR
        Start_deeplink(("Переход по deep link<br/>/start event_id"))
        T_tap["Нажать<br/>«Зарегистрироваться»"]
        T_form["Заполнить анкету:<br/>ФИО, e-mail, телефон"]
        End_done(("Регистрация завершена"))
    end
    subgraph Lane_bot["Telegram-бот (FSM)"]
        direction LR
        T_resolve["Определить мероприятие<br/>по deep link"]
        T_card["Показать карточку события<br/>и кнопку «Зарегистрироваться»"]
        T_waitlist["Предложить<br/>лист ожидания"]
        End_waitlist(("Заявка в листе ожидания"))
        G_profile{"Профиль заполнен?"}
        T_ticket["Отправить билет с QR-кодом<br/>и файл календаря"]
    end
    subgraph Lane_core["Сервис регистрации"]
        direction LR
        T_capacity["Проверить свободные места<br/>и дедлайн регистрации"]
        G_capacity{"Есть свободные места?"}
        T_validate["Валидировать поля<br/>и проверить дубли"]
        G_valid{"Данные корректны?"}
        T_create["Создать заявку<br/>и забронировать место"]
    end
    subgraph Lane_ext["Внешние системы"]
        direction LR
        T_crm["Записать участника<br/>в Google Sheets / Airtable"]
    end
    Start_deeplink --> T_resolve
    T_resolve --> T_capacity
    T_capacity --> G_capacity
    G_capacity -- "да" --> T_card
    G_capacity -- "нет" --> T_waitlist
    T_waitlist --> End_waitlist
    T_card --> T_tap
    T_tap --> G_profile
    G_profile -- "нет" --> T_form
    G_profile -- "да" --> T_create
    T_form --> T_validate
    T_validate --> G_valid
    G_valid -- "нет, вернуть на правку" --> T_form
    G_valid -- "да" --> T_create
    T_create --> T_crm
    T_crm --> T_ticket
    T_ticket --> End_done
    classDef evStart fill:#1f7a3f,stroke:#0f4523,color:#ffffff
    classDef evEnd fill:#8a1f1f,stroke:#4a0f0f,color:#ffffff
    classDef gw fill:#e0a800,stroke:#8a6800,color:#1a1a1a
    classDef userTask fill:#2b5d8a,stroke:#143349,color:#ffffff
    classDef svcTask fill:#3a3f4b,stroke:#1b1e24,color:#ffffff
    classDef msgTask fill:#5a3a7a,stroke:#2e1c40,color:#ffffff
    class Start_deeplink evStart
    class T_resolve,T_capacity,T_validate,T_create,T_crm svcTask
    class G_capacity,G_profile,G_valid gw
    class T_card,T_waitlist,T_ticket msgTask
    class End_waitlist,End_done evEnd
    class T_tap,T_form userTask
```
<!-- /diagram -->

### Решения, зашитые в модель

**Проверка вместимости идёт до показа карточки.** Участник не должен узнавать
об отсутствии мест после того, как заполнил анкету, — это главный источник
негатива и брошенных заявок. Если мест нет, бот сразу предлагает лист ожидания
как альтернативу, а не как отказ.

**Профиль переиспользуется между мероприятиями.** Шлюз «Профиль заполнен?»
пропускает повторного участника мимо анкеты сразу к бронированию. На втором и
последующих событиях регистрация укладывается в два нажатия.

**Валидация возвращает на правку конкретного поля, а не всей формы.** Обратная
связь от шлюза «Данные корректны?» ведёт в задачу заполнения анкеты, где FSM
хранит уже введённые значения. Пользователь исправляет только e-mail, а не
вводит имя и телефон заново.

**Место бронируется до синхронизации с CRM.** Google Sheets и Airtable —
внешние системы с квотами и таймаутами; их недоступность не должна ломать
регистрацию. Заявка фиксируется в собственной БД, синхронизация идёт следом и
при сбое уходит в очередь на повтор.

---

## 2. Автоматические напоминания

Процесс запускается по таймеру, а не по событию пользователя. Планировщик
раз в час забирает заявки, попадающие в окна T-24 ч и T-1 ч.

**Файл:** [`diagrams/02-reminders.bpmn`](diagrams/02-reminders.bpmn)

<!-- diagram:02-reminders -->
```mermaid
flowchart LR
    subgraph Lane_sched["Планировщик"]
        direction LR
        Start_tick(("Ежечасный запуск<br/>по расписанию"))
        T_select["Отобрать заявки в окне<br/>T-24 ч и T-1 ч"]
        G_any{"Есть адресаты?"}
        T_queue["Сформировать очередь<br/>с учётом лимитов Telegram"]
        End_empty(("Рассылка не требуется"))
        T_release["Освободить место и пригласить<br/>первого из листа ожидания"]
        T_confirm["Проставить статус<br/>«подтвердил» в CRM"]
        End_released(("Место переиспользовано"))
        End_confirmed(("Участие подтверждено"))
    end
    subgraph Lane_bot["Telegram-бот"]
        direction LR
        T_send["Отправить напоминание<br/>с кнопками «Буду» / «Не приду»"]
        G_decline{"Участник отказался?"}
    end
    subgraph Lane_participant["Участник"]
        direction LR
        T_answer["Ответить на напоминание"]
    end
    Start_tick --> T_select
    T_select --> G_any
    G_any -- "да" --> T_queue
    G_any -- "нет" --> End_empty
    T_queue --> T_send
    T_send --> T_answer
    T_answer --> G_decline
    G_decline -- "да" --> T_release
    G_decline -- "нет" --> T_confirm
    T_release --> End_released
    T_confirm --> End_confirmed
    classDef evStart fill:#1f7a3f,stroke:#0f4523,color:#ffffff
    classDef evEnd fill:#8a1f1f,stroke:#4a0f0f,color:#ffffff
    classDef gw fill:#e0a800,stroke:#8a6800,color:#1a1a1a
    classDef userTask fill:#2b5d8a,stroke:#143349,color:#ffffff
    classDef svcTask fill:#3a3f4b,stroke:#1b1e24,color:#ffffff
    classDef msgTask fill:#5a3a7a,stroke:#2e1c40,color:#ffffff
    class Start_tick evStart
    class T_select,T_queue,T_release,T_confirm svcTask
    class G_any,G_decline gw
    class End_empty,End_released,End_confirmed evEnd
    class T_send msgTask
    class T_answer userTask
```
<!-- /diagram -->

### Решения, зашитые в модель

**Ежечасный тик вместо задачи на каждую заявку.** Планировщик работает окнами:
это на порядок меньше запланированных задач, переживает рестарт сервиса и
корректно обрабатывает перенос мероприятия — время пересчитывается на лету.

**Напоминание — это не уведомление, а точка принятия решения.** Кнопки
«Буду» / «Не приду» превращают рассылку в инструмент управления явкой: отказ
за 24 часа освобождает место, и оно уходит первому в листе ожидания
автоматически.

**Отдельная ветка на пустую выборку.** Если адресатов нет, процесс завершается
явным конечным событием. В BPMN нет «просто ничего не произошло» — каждая
ветка должна иметь конец, иначе модель нельзя проверить на полноту.

---

## 3. Пост-ивентный NPS-опрос

Запускается через два часа после окончания мероприятия — участник уже дома,
впечатление ещё свежее.

**Файл:** [`diagrams/03-nps-survey.bpmn`](diagrams/03-nps-survey.bpmn)

<!-- diagram:03-nps-survey -->
```mermaid
flowchart LR
    subgraph Lane_sched["Планировщик"]
        direction LR
        Start_after(("T+2 ч после<br/>окончания события"))
        T_audience["Отобрать участников<br/>со статусом «пришёл»"]
    end
    subgraph Lane_bot["Telegram-бот"]
        direction LR
        T_ask["Отправить опрос:<br/>оценка 0–10"]
        G_detractor{"Оценка ≤ 6?"}
        T_thanks["Поблагодарить и предложить<br/>ближайшее событие"]
        T_probe["Запросить комментарий:<br/>что улучшить"]
    end
    subgraph Lane_participant["Участник"]
        direction LR
        T_rate["Поставить оценку"]
        T_comment["Написать комментарий"]
    end
    subgraph Lane_analytics["Аналитический модуль"]
        direction LR
        T_store["Сохранить ответ<br/>и связать с мероприятием"]
        T_recalc["Пересчитать NPS<br/>и обновить сводный отчёт"]
        End_report(("Отчёт обновлён"))
    end
    Start_after --> T_audience
    T_audience --> T_ask
    T_ask --> T_rate
    T_rate --> G_detractor
    G_detractor -- "нет" --> T_thanks
    G_detractor -- "да" --> T_probe
    T_probe --> T_comment
    T_comment --> T_store
    T_thanks --> T_store
    T_store --> T_recalc
    T_recalc --> End_report
    classDef evStart fill:#1f7a3f,stroke:#0f4523,color:#ffffff
    classDef evEnd fill:#8a1f1f,stroke:#4a0f0f,color:#ffffff
    classDef gw fill:#e0a800,stroke:#8a6800,color:#1a1a1a
    classDef userTask fill:#2b5d8a,stroke:#143349,color:#ffffff
    classDef svcTask fill:#3a3f4b,stroke:#1b1e24,color:#ffffff
    classDef msgTask fill:#5a3a7a,stroke:#2e1c40,color:#ffffff
    class Start_after evStart
    class T_audience,T_store,T_recalc svcTask
    class T_ask,T_thanks,T_probe msgTask
    class T_rate,T_comment userTask
    class G_detractor gw
    class End_report evEnd
```
<!-- /diagram -->

### Решения, зашитые в модель

**Опрос уходит только тем, кто пришёл.** Рассылать NPS всем
зарегистрированным — значит смешивать оценку мероприятия с досадой тех, кто не
дошёл, и получить бесполезное среднее.

**Уточняющий вопрос — только детракторам.** Ветка «оценка ≤ 6» просит
комментарий, промоутерам вместо этого предлагается следующее событие. Так
качественная обратная связь собирается там, где она информативна, а лояльные
участники сразу возвращаются в воронку.

**Один вопрос — один экран.** Оценка ставится нажатием inline-кнопки, а не
вводом текста: это разница между 60% и 15% ответивших.

---

## Как открыть исходники

```bash
# bpmn.io — онлайн, ничего ставить не нужно
open https://demo.bpmn.io/   # затем перетащить .bpmn в окно

# Camunda Modeler — десктоп
brew install --cask camunda-modeler
```

Перегенерация моделей после правки:

```bash
python3 tools/build_diagrams.py
```
