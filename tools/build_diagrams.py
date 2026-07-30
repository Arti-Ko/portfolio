"""Описание BPMN-моделей портфолио и генерация .bpmn файлов.

Запуск:  python3 tools/build_diagrams.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import re  # noqa: E402

from bpmn_gen import End, Flow, Gateway, Lane, Model, Start, Task, render  # noqa: E402
from mermaid_gen import to_mermaid  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Проект 1 — Telegram-бот регистрации на мероприятия
# --------------------------------------------------------------------------

registration = Model(
    id="event_registration",
    name="Регистрация участника на мероприятие",
    pool_name="Регистрация на мероприятие через Telegram",
    documentation=(
        "Основной сквозной процесс: от перехода по deep link до выдачи "
        "электронного билета. Целевая конверсия из открытия карточки "
        "в завершённую регистрацию — 85%."
    ),
    lanes=[
        Lane("Lane_participant", "Участник", rows=1),
        Lane("Lane_bot", "Telegram-бот (FSM)", rows=2),
        Lane("Lane_core", "Сервис регистрации", rows=1),
        Lane("Lane_ext", "Внешние системы", rows=1),
    ],
    nodes=[
        Start("Start_deeplink", "Переход по deep link\n/start event_id", "Lane_participant", 0, kind="message"),
        Task("T_resolve", "Определить мероприятие\nпо deep link", "Lane_bot", 1, kind="service"),
        Task("T_capacity", "Проверить свободные места\nи дедлайн регистрации", "Lane_core", 2, kind="service"),
        Gateway("G_capacity", "Есть свободные места?", "Lane_core", 3),
        Task("T_card", "Показать карточку события\nи кнопку «Зарегистрироваться»", "Lane_bot", 4, kind="send"),
        Task("T_waitlist", "Предложить\nлист ожидания", "Lane_bot", 4, row=1, kind="send"),
        End("End_waitlist", "Заявка в листе ожидания", "Lane_bot", 5, row=1),
        Task("T_tap", "Нажать\n«Зарегистрироваться»", "Lane_participant", 5, kind="user"),
        Gateway("G_profile", "Профиль заполнен?", "Lane_bot", 6),
        Task("T_form", "Заполнить анкету:\nФИО, e-mail, телефон", "Lane_participant", 7, kind="user"),
        Task("T_validate", "Валидировать поля\nи проверить дубли", "Lane_core", 8, kind="service"),
        Gateway("G_valid", "Данные корректны?", "Lane_core", 9),
        Task("T_create", "Создать заявку\nи забронировать место", "Lane_core", 10, kind="service"),
        Task("T_crm", "Записать участника\nв Google Sheets / Airtable", "Lane_ext", 11, kind="service"),
        Task("T_ticket", "Отправить билет с QR-кодом\nи файл календаря", "Lane_bot", 12, kind="send"),
        End("End_done", "Регистрация завершена", "Lane_participant", 13, kind="message"),
    ],
    flows=[
        Flow("Start_deeplink", "T_resolve"),
        Flow("T_resolve", "T_capacity"),
        Flow("T_capacity", "G_capacity"),
        Flow("G_capacity", "T_card", "да"),
        Flow("G_capacity", "T_waitlist", "нет"),
        Flow("T_waitlist", "End_waitlist"),
        Flow("T_card", "T_tap"),
        Flow("T_tap", "G_profile"),
        Flow("G_profile", "T_form", "нет"),
        Flow("G_profile", "T_create", "да"),
        Flow("T_form", "T_validate"),
        Flow("T_validate", "G_valid"),
        Flow("G_valid", "T_form", "нет, вернуть на правку"),
        Flow("G_valid", "T_create", "да"),
        Flow("T_create", "T_crm"),
        Flow("T_crm", "T_ticket"),
        Flow("T_ticket", "End_done"),
    ],
)

reminders = Model(
    id="event_reminders",
    name="Автоматические напоминания о мероприятии",
    pool_name="Напоминания за 24 ч и 1 ч до события",
    documentation=(
        "Планировщик раз в час отбирает подтверждённые заявки, попадающие "
        "в окно напоминания, и рассылает сообщения с кнопками подтверждения. "
        "Отказ освобождает место и запускает добор из листа ожидания."
    ),
    lanes=[
        Lane("Lane_sched", "Планировщик", rows=2),
        Lane("Lane_bot", "Telegram-бот", rows=1),
        Lane("Lane_participant", "Участник", rows=1),
    ],
    nodes=[
        Start("Start_tick", "Ежечасный запуск\nпо расписанию", "Lane_sched", 0, kind="timer"),
        Task("T_select", "Отобрать заявки в окне\nT-24 ч и T-1 ч", "Lane_sched", 1, kind="service"),
        Gateway("G_any", "Есть адресаты?", "Lane_sched", 2),
        End("End_empty", "Рассылка не требуется", "Lane_sched", 3, row=1),
        Task("T_queue", "Сформировать очередь\nс учётом лимитов Telegram", "Lane_sched", 3, kind="service"),
        Task("T_send", "Отправить напоминание\nс кнопками «Буду» / «Не приду»", "Lane_bot", 4, kind="send"),
        Task("T_answer", "Ответить на напоминание", "Lane_participant", 5, kind="user"),
        Gateway("G_decline", "Участник отказался?", "Lane_bot", 6),
        Task("T_release", "Освободить место и пригласить\nпервого из листа ожидания", "Lane_sched", 7, kind="service"),
        Task("T_confirm", "Проставить статус\n«подтвердил» в CRM", "Lane_sched", 7, row=1, kind="service"),
        End("End_released", "Место переиспользовано", "Lane_sched", 8),
        End("End_confirmed", "Участие подтверждено", "Lane_sched", 8, row=1),
    ],
    flows=[
        Flow("Start_tick", "T_select"),
        Flow("T_select", "G_any"),
        Flow("G_any", "T_queue", "да"),
        Flow("G_any", "End_empty", "нет"),
        Flow("T_queue", "T_send"),
        Flow("T_send", "T_answer"),
        Flow("T_answer", "G_decline"),
        Flow("G_decline", "T_release", "да"),
        Flow("G_decline", "T_confirm", "нет"),
        Flow("T_release", "End_released"),
        Flow("T_confirm", "End_confirmed"),
    ],
)

nps = Model(
    id="event_nps",
    name="Пост-ивентный NPS-опрос",
    pool_name="Сбор обратной связи после мероприятия",
    documentation=(
        "Через 2 часа после окончания события бот запрашивает оценку по шкале "
        "0–10. Детракторы (0–6) получают уточняющий вопрос, ответы попадают "
        "в сводный отчёт по мероприятиям."
    ),
    lanes=[
        Lane("Lane_sched", "Планировщик", rows=1),
        Lane("Lane_bot", "Telegram-бот", rows=2),
        Lane("Lane_participant", "Участник", rows=1),
        Lane("Lane_analytics", "Аналитический модуль", rows=1),
    ],
    nodes=[
        Start("Start_after", "T+2 ч после\nокончания события", "Lane_sched", 0, kind="timer"),
        Task("T_audience", "Отобрать участников\nсо статусом «пришёл»", "Lane_sched", 1, kind="service"),
        Task("T_ask", "Отправить опрос:\nоценка 0–10", "Lane_bot", 2, kind="send"),
        Task("T_rate", "Поставить оценку", "Lane_participant", 3, kind="user"),
        Gateway("G_detractor", "Оценка ≤ 6?", "Lane_bot", 4),
        Task("T_thanks", "Поблагодарить и предложить\nближайшее событие", "Lane_bot", 5, kind="send"),
        Task("T_probe", "Запросить комментарий:\nчто улучшить", "Lane_bot", 5, row=1, kind="send"),
        Task("T_comment", "Написать комментарий", "Lane_participant", 6, kind="user"),
        Task("T_store", "Сохранить ответ\nи связать с мероприятием", "Lane_analytics", 7, kind="service"),
        Task("T_recalc", "Пересчитать NPS\nи обновить сводный отчёт", "Lane_analytics", 8, kind="service"),
        End("End_report", "Отчёт обновлён", "Lane_analytics", 9),
    ],
    flows=[
        Flow("Start_after", "T_audience"),
        Flow("T_audience", "T_ask"),
        Flow("T_ask", "T_rate"),
        Flow("T_rate", "G_detractor"),
        Flow("G_detractor", "T_thanks", "нет"),
        Flow("G_detractor", "T_probe", "да"),
        Flow("T_probe", "T_comment"),
        Flow("T_comment", "T_store"),
        Flow("T_thanks", "T_store"),
        Flow("T_store", "T_recalc"),
        Flow("T_recalc", "End_report"),
    ],
)


# --------------------------------------------------------------------------
# Проект 2 — Сервис AI-озвучки
# --------------------------------------------------------------------------

dubbing = Model(
    id="dubbing_pipeline",
    name="Автоматический дубляж видео",
    pool_name="Пайплайн AI-озвучки",
    documentation=(
        "Сквозной пайплайн STT → MT → фонетическая коррекция → TTS → сведение. "
        "Автоматический контроль качества отсекает выпуски с рассинхроном "
        "и высоким WER до публикации."
    ),
    lanes=[
        Lane("Lane_producer", "Продюсер", rows=1),
        Lane("Lane_orch", "Оркестратор пайплайна", rows=2),
        Lane("Lane_ai", "AI-провайдеры (STT / MT / TTS)", rows=1),
        Lane("Lane_host", "Видеохостинг", rows=1),
    ],
    nodes=[
        Start("Start_task", "Поставлена задача\nна дубляж", "Lane_producer", 0, kind="message"),
        Task("T_pick", "Выбрать видео\nи целевые языки", "Lane_producer", 1, kind="user"),
        Task("T_fetch", "Скачать исходник\nчерез API хостинга", "Lane_orch", 2, kind="service"),
        Task("T_demux", "Извлечь аудио (FFmpeg)\nи нормализовать уровень", "Lane_orch", 3, kind="service"),
        Task("T_stt", "Распознать речь\nи тайм-коды (STT)", "Lane_ai", 4, kind="service"),
        Task("T_mt", "Перевести транскрипт\nна целевой язык", "Lane_ai", 5, kind="service"),
        Task("T_phonetic", "Применить глоссарий\nи фонетическую коррекцию", "Lane_orch", 6, kind="service"),
        Task("T_tts", "Синтезировать речь (TTS)\nпо тайм-кодам", "Lane_ai", 7, kind="service"),
        Task("T_mix", "Свести дорожку: длительность,\nгромкость, фон", "Lane_orch", 8, kind="service"),
        Task("T_qc", "Автоконтроль: WER,\nрассинхрон, клиппинг", "Lane_orch", 9, kind="service"),
        Gateway("G_qc", "Метрики в допуске?", "Lane_orch", 10),
        Task("T_rework", "Создать задачу\nна ручную правку", "Lane_orch", 11, row=1, kind="service"),
        End("End_rework", "Передано редактору", "Lane_orch", 12, row=1, kind="message"),
        Task("T_upload", "Загрузить дорожку\nи заменить аудио", "Lane_host", 11, kind="service"),
        Task("T_notify", "Уведомить продюсера\nо готовности", "Lane_orch", 12, kind="send"),
        End("End_published", "Дубляж опубликован", "Lane_producer", 13),
    ],
    flows=[
        Flow("Start_task", "T_pick"),
        Flow("T_pick", "T_fetch"),
        Flow("T_fetch", "T_demux"),
        Flow("T_demux", "T_stt"),
        Flow("T_stt", "T_mt"),
        Flow("T_mt", "T_phonetic"),
        Flow("T_phonetic", "T_tts"),
        Flow("T_tts", "T_mix"),
        Flow("T_mix", "T_qc"),
        Flow("T_qc", "G_qc"),
        Flow("G_qc", "T_upload", "да"),
        Flow("G_qc", "T_rework", "нет"),
        Flow("T_rework", "End_rework"),
        Flow("T_upload", "T_notify"),
        Flow("T_notify", "End_published"),
    ],
)

editor_review = Model(
    id="dubbing_review",
    name="Ручная правка и приёмка озвучки",
    pool_name="Редактирование и контроль качества дубляжа",
    documentation=(
        "Процесс запускается, когда автоконтроль отклонил выпуск. Редактор "
        "правит причину дефекта, пересинтезируются только затронутые сегменты, "
        "приёмка идёт по MOS-тесту."
    ),
    lanes=[
        Lane("Lane_editor", "Технический редактор", rows=3),
        Lane("Lane_orch", "Оркестратор пайплайна", rows=2),
        Lane("Lane_producer", "Продюсер", rows=1),
    ],
    nodes=[
        Start("Start_rework", "Поступила задача\nна правку", "Lane_editor", 0, kind="message"),
        Task("T_listen", "Прослушать сегменты\nс низкой метрикой", "Lane_editor", 1, kind="user"),
        Gateway("G_defect", "Тип дефекта?", "Lane_editor", 2),
        Task("T_fix_text", "Исправить перевод\nи глоссарий терминов", "Lane_editor", 3, kind="user"),
        Task("T_fix_phon", "Задать транскрипцию\n(SSML / фонемы)", "Lane_editor", 3, row=1, kind="user"),
        Task("T_fix_time", "Скорректировать тайм-коды\nи темп речи", "Lane_editor", 3, row=2, kind="user"),
        Task("T_resynth", "Пересинтезировать\nтолько изменённые сегменты", "Lane_orch", 4, kind="service"),
        Task("T_remix", "Пересобрать дорожку\nи обновить превью", "Lane_orch", 5, kind="service"),
        Task("T_mos", "Собрать оценки MOS\nна выборке сегментов", "Lane_editor", 6, kind="user"),
        Gateway("G_mos", "MOS ≥ 4.0?", "Lane_editor", 7),
        Task("T_escalate", "Сменить голос / провайдера\nи перезапустить пайплайн", "Lane_orch", 8, row=1, kind="service"),
        End("End_escalated", "Требуется смена\nконфигурации", "Lane_orch", 9, row=1),
        Task("T_accept", "Согласовать\nфинальную дорожку", "Lane_producer", 8, kind="user"),
        Task("T_publish", "Опубликовать\nпринятую версию", "Lane_orch", 9, kind="service"),
        End("End_accepted", "Дубляж принят", "Lane_producer", 10),
    ],
    flows=[
        Flow("Start_rework", "T_listen"),
        Flow("T_listen", "G_defect"),
        Flow("G_defect", "T_fix_text", "перевод"),
        Flow("G_defect", "T_fix_phon", "произношение"),
        Flow("G_defect", "T_fix_time", "тайминг"),
        Flow("T_fix_text", "T_resynth"),
        Flow("T_fix_phon", "T_resynth"),
        Flow("T_fix_time", "T_resynth"),
        Flow("T_resynth", "T_remix"),
        Flow("T_remix", "T_mos"),
        Flow("T_mos", "G_mos"),
        Flow("G_mos", "T_accept", "да"),
        Flow("G_mos", "T_escalate", "нет"),
        Flow("T_escalate", "End_escalated"),
        Flow("T_accept", "T_publish"),
        Flow("T_publish", "End_accepted"),
    ],
)


# --------------------------------------------------------------------------
# Проект 3 — Анонимизатор медицинских данных
# --------------------------------------------------------------------------

anonymization = Model(
    id="phi_anonymization",
    name="Обезличивание медицинского документа",
    pool_name="Сервис обезличивания ПДн",
    documentation=(
        "Документ приходит из МИС по защищённому каналу. Пайплайн распознаёт "
        "и маскирует ПДн, контрольный прогон ищет остаточные идентификаторы, "
        "любое действие фиксируется в неизменяемом аудит-логе."
    ),
    lanes=[
        Lane("Lane_mis", "МИС (система-источник)", rows=1),
        Lane("Lane_api", "API-шлюз", rows=2),
        Lane("Lane_nlp", "NLP-пайплайн", rows=1),
        Lane("Lane_dpo", "Оператор ПДн", rows=2),
        Lane("Lane_store", "Хранилище и аудит", rows=1),
    ],
    nodes=[
        Start("Start_doc", "Документ отправлен\nна обезличивание", "Lane_mis", 0, kind="message"),
        Task("T_auth", "Аутентифицировать запрос:\nmTLS, токен, схема", "Lane_api", 1, kind="service"),
        Gateway("G_auth", "Запрос легитимен?", "Lane_api", 2),
        Task("T_reject", "Вернуть 403\nи зафиксировать инцидент", "Lane_api", 3, row=1, kind="service"),
        End("End_rejected", "Запрос отклонён", "Lane_api", 4, row=1, kind="error"),
        Task("T_extract", "Извлечь текст:\nPDF / DOCX / HL7 / FHIR", "Lane_nlp", 3, kind="service"),
        Task("T_ner", "Распознать ПДн: ФИО, даты,\nадреса, СНИЛС, полис", "Lane_nlp", 4, kind="service"),
        Task("T_classify", "Классифицировать по ФЗ-152\nи HIPAA Safe Harbor", "Lane_nlp", 5, kind="service"),
        Gateway("G_conf", "Уверенность ≥ порога?", "Lane_nlp", 6),
        Task("T_manual", "Верифицировать разметку\nвручную", "Lane_dpo", 7, kind="user"),
        Task("T_mask", "Маскировать и псевдонимизировать,\nсохранить токен-мапу", "Lane_nlp", 8, kind="service"),
        Task("T_recheck", "Контрольный прогон:\nпоиск остаточных ПДн", "Lane_nlp", 9, kind="service"),
        Gateway("G_residual", "Найдены остаточные ПДн?", "Lane_nlp", 10),
        Task("T_quarantine", "Отправить в карантин\nна ручную обработку", "Lane_dpo", 11, row=1, kind="user"),
        End("End_quarantine", "Документ в карантине", "Lane_dpo", 12, row=1),
        Task("T_store", "Сохранить документ и токен-мапу\nв раздельных контурах", "Lane_store", 11, kind="service"),
        Task("T_audit", "Записать событие\nв неизменяемый аудит-лог", "Lane_store", 12, kind="service"),
        Task("T_return", "Вернуть обезличенный\nдокумент в МИС", "Lane_api", 13, kind="send"),
        End("End_done", "Документ обезличен", "Lane_mis", 14, kind="message"),
    ],
    flows=[
        Flow("Start_doc", "T_auth"),
        Flow("T_auth", "G_auth"),
        Flow("G_auth", "T_extract", "да"),
        Flow("G_auth", "T_reject", "нет"),
        Flow("T_reject", "End_rejected"),
        Flow("T_extract", "T_ner"),
        Flow("T_ner", "T_classify"),
        Flow("T_classify", "G_conf"),
        Flow("G_conf", "T_mask", "да"),
        Flow("G_conf", "T_manual", "нет"),
        Flow("T_manual", "T_mask"),
        Flow("T_mask", "T_recheck"),
        Flow("T_recheck", "G_residual"),
        Flow("G_residual", "T_store", "нет"),
        Flow("G_residual", "T_quarantine", "да"),
        Flow("T_quarantine", "End_quarantine"),
        Flow("T_store", "T_audit"),
        Flow("T_audit", "T_return"),
        Flow("T_return", "End_done"),
    ],
)

reidentification = Model(
    id="phi_reidentification",
    name="Обратная идентификация по обоснованному запросу",
    pool_name="Раскрытие обезличенных данных",
    documentation=(
        "Единственный легальный путь связать обезличенный документ с субъектом. "
        "Требует правового основания и согласования двумя ролями (принцип «четырёх глаз»), "
        "выдача ограничена по TTL и полностью логируется."
    ),
    lanes=[
        Lane("Lane_req", "Инициатор запроса", rows=1),
        Lane("Lane_dpo", "Оператор ПДн", rows=2),
        Lane("Lane_svc", "Сервис деанонимизации", rows=1),
        Lane("Lane_audit", "Аудит", rows=1),
    ],
    nodes=[
        Start("Start_req", "Поступил запрос\nна раскрытие", "Lane_req", 0, kind="message"),
        Task("T_form", "Указать правовое основание\nи перечень полей", "Lane_req", 1, kind="user"),
        Task("T_check", "Проверить основание\nи полномочия заявителя", "Lane_dpo", 2, kind="user"),
        Gateway("G_basis", "Основание достаточно?", "Lane_dpo", 3),
        Task("T_deny", "Отклонить запрос\nс мотивировкой", "Lane_dpo", 4, row=1, kind="send"),
        End("End_denied", "Запрос отклонён", "Lane_dpo", 5, row=1),
        Task("T_approve", "Согласовать раскрытие\nвторым approver", "Lane_dpo", 4, kind="user"),
        Gateway("G_approve", "Второе согласование\nполучено?", "Lane_dpo", 5),
        End("End_noapprove", "Раскрытие\nне согласовано", "Lane_dpo", 6, row=1),
        Task("T_reveal", "Раскрыть токен-мапу\nтолько по указанным полям", "Lane_svc", 6, kind="service"),
        Task("T_ttl", "Сформировать выдачу\nс ограниченным TTL", "Lane_svc", 7, kind="service"),
        Task("T_log", "Зафиксировать: кто, что,\nзачем, когда", "Lane_audit", 8, kind="service"),
        Task("T_deliver", "Передать данные\nпо защищённому каналу", "Lane_svc", 9, kind="send"),
        End("End_revealed", "Данные раскрыты\nи зафиксированы", "Lane_req", 10),
    ],
    flows=[
        Flow("Start_req", "T_form"),
        Flow("T_form", "T_check"),
        Flow("T_check", "G_basis"),
        Flow("G_basis", "T_approve", "да"),
        Flow("G_basis", "T_deny", "нет"),
        Flow("T_deny", "End_denied"),
        Flow("T_approve", "G_approve"),
        Flow("G_approve", "T_reveal", "да"),
        Flow("G_approve", "End_noapprove", "нет"),
        Flow("T_reveal", "T_ttl"),
        Flow("T_ttl", "T_log"),
        Flow("T_log", "T_deliver"),
        Flow("T_deliver", "End_revealed"),
    ],
)


# --------------------------------------------------------------------------
# Проект 5 — Enterprise AI-помощники (on-premises LLM)
# --------------------------------------------------------------------------

rag_query = Model(
    id="rag_query",
    name="Ответ на вопрос по нормативной базе",
    pool_name="AI-Librarium: поиск по локальным нормативным актам",
    documentation=(
        "Сотрудник задаёт вопрос на естественном языке, система отвечает "
        "с обязательными ссылками на пункты ЛНА. Ответ без подтверждённого "
        "источника не выдаётся как утверждение."
    ),
    lanes=[
        Lane("Lane_emp", "Сотрудник", rows=1),
        Lane("Lane_orch", "Оркестратор (LangGraph)", rows=2),
        Lane("Lane_search", "Поисковый слой", rows=1),
        Lane("Lane_llm", "LLM-контур (on-premises)", rows=2),
        Lane("Lane_audit", "Журнал", rows=1),
    ],
    nodes=[
        Start("Start_q", "Сотрудник задаёт\nвопрос", "Lane_emp", 0, kind="message"),
        Task("T_auth", "Определить права\nчерез Active Directory", "Lane_orch", 1, kind="service"),
        Gateway("G_scope", "Доступны все\nразделы базы?", "Lane_orch", 2),
        Task("T_narrow", "Сузить область поиска\nдо доступных документов", "Lane_orch", 3, row=1, kind="service"),
        Task("T_hybrid", "Гибридный поиск:\nвекторный + BM25", "Lane_search", 4, kind="service"),
        Task("T_rerank", "Переранжировать\nи отобрать топ-K фрагментов", "Lane_search", 5, kind="service"),
        Gateway("G_found", "Есть релевантные\nфрагменты?", "Lane_orch", 6),
        Task("T_nofound", "Сообщить, что ответа\nв базе нет", "Lane_orch", 7, row=1, kind="send"),
        End("End_nofound", "Ответ не найден", "Lane_orch", 8, row=1),
        Task("T_prompt", "Собрать промпт\nс цитатами и ограничениями", "Lane_llm", 7, kind="service"),
        Task("T_generate", "Сгенерировать ответ\nлокальной моделью", "Lane_llm", 8, kind="service"),
        Task("T_ground", "Проверить опору\nкаждого утверждения на источник", "Lane_llm", 9, kind="service"),
        Gateway("G_ground", "Все утверждения\nподтверждены?", "Lane_llm", 10),
        Task("T_flag", "Выдать только цитаты\nбез обобщения", "Lane_llm", 11, row=1, kind="send"),
        End("End_partial", "Ответ с оговоркой", "Lane_llm", 12, row=1),
        Task("T_answer", "Показать ответ\nсо ссылками на пункты ЛНА", "Lane_orch", 11, kind="send"),
        Task("T_log", "Записать вопрос, источники\nи ответ в журнал", "Lane_audit", 12, kind="service"),
        End("End_done", "Сотрудник\nполучил ответ", "Lane_emp", 13),
    ],
    flows=[
        Flow("Start_q", "T_auth"),
        Flow("T_auth", "G_scope"),
        Flow("G_scope", "T_hybrid", "да"),
        Flow("G_scope", "T_narrow", "нет"),
        Flow("T_narrow", "T_hybrid"),
        Flow("T_hybrid", "T_rerank"),
        Flow("T_rerank", "G_found"),
        Flow("G_found", "T_prompt", "да"),
        Flow("G_found", "T_nofound", "нет"),
        Flow("T_nofound", "End_nofound"),
        Flow("T_prompt", "T_generate"),
        Flow("T_generate", "T_ground"),
        Flow("T_ground", "G_ground"),
        Flow("G_ground", "T_answer", "да"),
        Flow("G_ground", "T_flag", "нет"),
        Flow("T_flag", "End_partial"),
        Flow("T_answer", "T_log"),
        Flow("T_log", "End_done"),
    ],
)

medical_approval = Model(
    id="medical_approval",
    name="Согласование медицинского назначения",
    pool_name="Проверка протокола клиники на соответствие правилам",
    documentation=(
        "Протокол из клиники проверяется на соответствие клиническим "
        "рекомендациям и условиям полиса. Спорные случаи уходят "
        "врачу-эксперту: автомат не отказывает в лечении единолично."
    ),
    lanes=[
        Lane("Lane_clinic", "Клиника", rows=1),
        Lane("Lane_ocr", "Распознавание документа", rows=1),
        Lane("Lane_rules", "Клинический движок", rows=2),
        Lane("Lane_expert", "Врач-эксперт", rows=1),
        Lane("Lane_reg", "Учётная система", rows=1),
    ],
    nodes=[
        Start("Start_protocol", "Клиника прислала\nпротокол назначения", "Lane_clinic", 0, kind="message"),
        Task("T_ocr", "Распознать документ\nс сохранением структуры", "Lane_ocr", 1, kind="service"),
        Task("T_ner", "Извлечь диагнозы,\nуслуги, назначения", "Lane_ocr", 2, kind="service"),
        Gateway("G_quality", "Качество распознавания\nдостаточное?", "Lane_ocr", 3),
        Task("T_manual_read", "Прочитать документ\nвручную", "Lane_expert", 4, kind="user"),
        Task("T_map", "Сопоставить с МКБ-10\nи клиническими рекомендациями", "Lane_rules", 5, kind="service"),
        Task("T_check", "Проверить назначение\nпо правилам и полису", "Lane_rules", 6, kind="service"),
        Gateway("G_verdict", "Соответствует\nправилам?", "Lane_rules", 7),
        Task("T_approve", "Сформировать решение\nо согласовании", "Lane_rules", 8, kind="service"),
        Task("T_reject", "Сформировать\nмотивированный отказ", "Lane_rules", 8, row=1, kind="service"),
        Task("T_expert", "Передать случай\nврачу-эксперту", "Lane_expert", 8, kind="send"),
        Task("T_decide", "Принять решение\nпо спорному случаю", "Lane_expert", 9, kind="user"),
        Task("T_record", "Зафиксировать решение\nи обоснование", "Lane_reg", 10, kind="service"),
        Task("T_notify", "Отправить решение\nв клинику", "Lane_reg", 11, kind="send"),
        End("End_done", "Клиника\nполучила решение", "Lane_clinic", 12, kind="message"),
    ],
    flows=[
        Flow("Start_protocol", "T_ocr"),
        Flow("T_ocr", "T_ner"),
        Flow("T_ner", "G_quality"),
        Flow("G_quality", "T_map", "да"),
        Flow("G_quality", "T_manual_read", "нет"),
        Flow("T_manual_read", "T_map"),
        Flow("T_map", "T_check"),
        Flow("T_check", "G_verdict"),
        Flow("G_verdict", "T_approve", "да"),
        Flow("G_verdict", "T_reject", "нет"),
        Flow("G_verdict", "T_expert", "спорно"),
        Flow("T_expert", "T_decide"),
        Flow("T_approve", "T_record"),
        Flow("T_reject", "T_record"),
        Flow("T_decide", "T_record"),
        Flow("T_record", "T_notify"),
        Flow("T_notify", "End_done"),
    ],
)


# --------------------------------------------------------------------------
# Проект 6 — ЭТП морских грузоперевозок
# --------------------------------------------------------------------------

two_stage_auction = Model(
    id="two_stage_auction",
    name="Двухэтапные торги на перевозку",
    pool_name="ЭТП: предотбор и финальные торги",
    documentation=(
        "Двухэтапная модель: сначала допуск участников по формальным "
        "критериям, затем ценовые торги только среди допущенных. "
        "Цена не может победить над отсутствием ледового класса."
    ),
    lanes=[
        Lane("Lane_cargo", "Грузовладелец", rows=1),
        Lane("Lane_etp", "ЭТП", rows=2),
        Lane("Lane_ship", "Судовладелец", rows=1),
        Lane("Lane_ext", "Внешние сервисы", rows=1),
    ],
    nodes=[
        Start("Start_need", "Возникла потребность\nв перевозке", "Lane_cargo", 0),
        Task("T_lot", "Сформировать лот:\nгруз, маршрут, окно", "Lane_cargo", 1, kind="user"),
        Task("T_publish", "Опубликовать лот\nи открыть предотбор", "Lane_etp", 2, kind="service"),
        Task("T_apply", "Подать заявку\nна предотбор", "Lane_ship", 3, kind="user"),
        Task("T_verify", "Проверить компанию,\nдопуски и ледовый класс", "Lane_etp", 4, kind="service"),
        Gateway("G_pass", "Предотбор пройден?", "Lane_etp", 5),
        Task("T_admit", "Допустить\nк финальным торгам", "Lane_etp", 6, kind="service"),
        Task("T_refuse", "Отклонить\nс указанием причины", "Lane_etp", 6, row=1, kind="send"),
        End("End_refused", "Участник не допущен", "Lane_etp", 7, row=1),
        Gateway("G_enough", "Допущенных\nдостаточно?", "Lane_etp", 8),
        Task("T_fail", "Признать торги\nнесостоявшимися", "Lane_etp", 9, row=1, kind="service"),
        End("End_failed", "Торги\nне состоялись", "Lane_etp", 10, row=1),
        Task("T_auction", "Запустить\nфинальные торги", "Lane_etp", 9, kind="service"),
        Task("T_bid", "Подавать\nценовые предложения", "Lane_ship", 10, kind="user"),
        Task("T_close", "Закрыть торги по таймеру\nи определить победителя", "Lane_etp", 11, kind="service"),
        Task("T_contract", "Сформировать проект\nдоговора перевозки", "Lane_etp", 12, kind="service"),
        Task("T_sign", "Подписать документы\nэлектронной подписью", "Lane_ext", 13, kind="service"),
        Task("T_register", "Зарегистрировать сделку\nи открыть отслеживание", "Lane_etp", 14, kind="service"),
        End("End_deal", "Сделка заключена", "Lane_cargo", 15, kind="message"),
    ],
    flows=[
        Flow("Start_need", "T_lot"),
        Flow("T_lot", "T_publish"),
        Flow("T_publish", "T_apply"),
        Flow("T_apply", "T_verify"),
        Flow("T_verify", "G_pass"),
        Flow("G_pass", "T_admit", "да"),
        Flow("G_pass", "T_refuse", "нет"),
        Flow("T_refuse", "End_refused"),
        Flow("T_admit", "G_enough"),
        Flow("G_enough", "T_auction", "да"),
        Flow("G_enough", "T_fail", "нет"),
        Flow("T_fail", "End_failed"),
        Flow("T_auction", "T_bid"),
        Flow("T_bid", "T_close"),
        Flow("T_close", "T_contract"),
        Flow("T_contract", "T_sign"),
        Flow("T_sign", "T_register"),
        Flow("T_register", "End_deal"),
    ],
)

voyage_tracking = Model(
    id="voyage_tracking",
    name="Рейс и безбумажное закрытие сделки",
    pool_name="ЭТП: исполнение перевозки",
    documentation=(
        "От погрузки до закрытия сделки без единого бумажного документа. "
        "Положение судна приходит по AIS, юридически значимые документы "
        "подписываются электронной подписью."
    ),
    lanes=[
        Lane("Lane_ship", "Судовладелец", rows=1),
        Lane("Lane_port", "Порт и терминал", rows=1),
        Lane("Lane_etp", "ЭТП", rows=2),
        Lane("Lane_ext", "AIS и электронная подпись", rows=1),
        Lane("Lane_cargo", "Грузовладелец", rows=1),
    ],
    nodes=[
        Start("Start_load", "Судно подано\nпод погрузку", "Lane_ship", 0, kind="message"),
        Task("T_slot", "Подтвердить слот\nи начать погрузку", "Lane_port", 1, kind="user"),
        Task("T_bol", "Сформировать коносамент\nпо факту погрузки", "Lane_etp", 2, kind="service"),
        Task("T_sign_bol", "Подписать коносамент\nэлектронной подписью", "Lane_ext", 3, kind="service"),
        Task("T_ais", "Передавать координаты\nсудна по AIS", "Lane_ext", 4, kind="service"),
        Task("T_track", "Обновлять положение\nна карте", "Lane_etp", 5, kind="service"),
        Task("T_watch", "Следить за рейсом\nв личном кабинете", "Lane_cargo", 6, kind="user"),
        Gateway("G_dev", "Отклонение\nот маршрута или срока?", "Lane_etp", 7),
        Task("T_alert", "Уведомить стороны\nи зафиксировать событие", "Lane_etp", 8, row=1, kind="send"),
        Task("T_arrive", "Принять судно\nи разгрузить", "Lane_port", 9, kind="user"),
        Task("T_act", "Сформировать акт\nприёма-передачи", "Lane_port", 10, kind="service"),
        Task("T_sign_act", "Подписать акт\nэлектронной подписью", "Lane_ext", 11, kind="service"),
        Task("T_close", "Закрыть сделку\nи обновить рейтинги", "Lane_etp", 12, kind="service"),
        End("End_done", "Перевозка закрыта\nбез бумаги", "Lane_cargo", 13),
    ],
    flows=[
        Flow("Start_load", "T_slot"),
        Flow("T_slot", "T_bol"),
        Flow("T_bol", "T_sign_bol"),
        Flow("T_sign_bol", "T_ais"),
        Flow("T_ais", "T_track"),
        Flow("T_track", "T_watch"),
        Flow("T_watch", "G_dev"),
        Flow("G_dev", "T_arrive", "нет"),
        Flow("G_dev", "T_alert", "да"),
        Flow("T_alert", "T_arrive"),
        Flow("T_arrive", "T_act"),
        Flow("T_act", "T_sign_act"),
        Flow("T_sign_act", "T_close"),
        Flow("T_close", "End_done"),
    ],
)


# --------------------------------------------------------------------------
# Проект 7 — HR-платформа массового найма
# --------------------------------------------------------------------------

candidate_journey = Model(
    id="candidate_journey",
    name="Путь кандидата от анкеты до трудоустройства",
    pool_name="Массовый найм самозанятых и ИП",
    documentation=(
        "Единая воронка для тысяч кандидатов с проверкой налогового статуса "
        "и службы безопасности. Логистическое направление уходит "
        "в дополнительный контур допуска."
    ),
    lanes=[
        Lane("Lane_cand", "Кандидат", rows=1),
        Lane("Lane_portal", "Портал найма", rows=1),
        Lane("Lane_checks", "Проверки", rows=2),
        Lane("Lane_hr", "HR и руководитель", rows=2),
        Lane("Lane_ext", "Внешние системы", rows=1),
    ],
    nodes=[
        Start("Start_apply", "Кандидат\nоткрыл анкету", "Lane_cand", 0, kind="message"),
        Task("T_personal", "Заполнить\nперсональные данные", "Lane_cand", 1, kind="user"),
        Task("T_form", "Выбрать форму занятости:\nсамозанятый или ИП", "Lane_cand", 2, kind="user"),
        Task("T_docs", "Запросить документы\nпо выбранной форме", "Lane_portal", 3, kind="send"),
        Task("T_upload", "Загрузить документы", "Lane_cand", 4, kind="user"),
        Task("T_fns", "Проверить налоговый статус\nв ФНС", "Lane_checks", 5, kind="service"),
        Gateway("G_status", "Статус\nподтверждён?", "Lane_checks", 6),
        Task("T_help", "Показать инструкцию\nпо регистрации статуса", "Lane_checks", 7, row=1, kind="send"),
        End("End_pending", "Кандидат вне воронки\nдо регистрации", "Lane_checks", 8, row=1),
        Task("T_sb", "Проверка\nслужбы безопасности", "Lane_checks", 7, kind="service"),
        Gateway("G_sb", "Проверка\nпройдена?", "Lane_checks", 8),
        Task("T_reject", "Отказать\nс фиксацией причины", "Lane_checks", 9, row=1, kind="send"),
        End("End_rejected", "Кандидат отклонён", "Lane_checks", 10, row=1),
        Task("T_test", "Выдать тест\nи назначить собеседование", "Lane_portal", 9, kind="send"),
        Task("T_pass", "Пройти тест\nи собеседование", "Lane_cand", 10, kind="user"),
        Gateway("G_branch", "Логистическое\nнаправление?", "Lane_hr", 11),
        Task("T_bdd", "Направить на медконтроль\nи проверку БДД", "Lane_hr", 12, row=1, kind="send"),
        End("End_to_med", "Передано\nв контур допуска", "Lane_hr", 13, row=1, kind="message"),
        Task("T_hire", "Оформить\nтрудоустройство", "Lane_portal", 12, kind="service"),
        Task("T_sync", "Синхронизировать\nс CRM и шиной событий", "Lane_ext", 13, kind="service"),
        End("End_hired", "Кандидат\nтрудоустроен", "Lane_cand", 14),
    ],
    flows=[
        Flow("Start_apply", "T_personal"),
        Flow("T_personal", "T_form"),
        Flow("T_form", "T_docs"),
        Flow("T_docs", "T_upload"),
        Flow("T_upload", "T_fns"),
        Flow("T_fns", "G_status"),
        Flow("G_status", "T_sb", "да"),
        Flow("G_status", "T_help", "нет"),
        Flow("T_help", "End_pending"),
        Flow("T_sb", "G_sb"),
        Flow("G_sb", "T_test", "да"),
        Flow("G_sb", "T_reject", "нет"),
        Flow("T_reject", "End_rejected"),
        Flow("T_test", "T_pass"),
        Flow("T_pass", "G_branch"),
        Flow("G_branch", "T_hire", "нет"),
        Flow("G_branch", "T_bdd", "да"),
        Flow("T_bdd", "End_to_med"),
        Flow("T_hire", "T_sync"),
        Flow("T_sync", "End_hired"),
    ],
)

driver_clearance = Model(
    id="driver_clearance",
    name="Медконтроль и проверка безопасности дорожного движения",
    pool_name="Допуск кандидата к работе на транспорте",
    documentation=(
        "Дополнительный контур для логистического направления. Медицинское "
        "заключение и профиль нарушений проверяются до открытия доступа "
        "к сменам, а не после первого рейса."
    ),
    lanes=[
        Lane("Lane_cand", "Кандидат", rows=1),
        Lane("Lane_portal", "Портал найма", rows=2),
        Lane("Lane_med", "Медицинский партнёр", rows=1),
        Lane("Lane_bdd", "Специалист БДД", rows=2),
        Lane("Lane_sb", "Служба безопасности", rows=1),
    ],
    nodes=[
        Start("Start_bdd", "Кандидат направлен\nна допуск", "Lane_cand", 0, kind="message"),
        Task("T_book", "Записать на медосмотр\nв партнёрской сети", "Lane_portal", 1, kind="service"),
        Task("T_visit", "Пройти медосмотр", "Lane_cand", 2, kind="user"),
        Task("T_result", "Передать заключение\nв портал", "Lane_med", 3, kind="service"),
        Gateway("G_med", "Заключение\nположительное?", "Lane_portal", 4),
        Task("T_med_no", "Зафиксировать отказ\nпо медицинским основаниям", "Lane_portal", 5, row=1, kind="send"),
        End("End_med_no", "Допуск не выдан", "Lane_portal", 6, row=1),
        Task("T_license", "Проверить удостоверение\nи стаж", "Lane_bdd", 5, kind="service"),
        Task("T_violations", "Запросить историю\nнарушений", "Lane_bdd", 6, kind="service"),
        Gateway("G_bdd", "Профиль риска\nдопустим?", "Lane_bdd", 7),
        Task("T_bdd_no", "Отказать в допуске\nк управлению", "Lane_bdd", 8, row=1, kind="send"),
        End("End_bdd_no", "Допуск\nк транспорту закрыт", "Lane_bdd", 9, row=1),
        Task("T_final", "Согласовать допуск", "Lane_sb", 8, kind="user"),
        Task("T_grant", "Открыть доступ к сменам\nи оформить трудоустройство", "Lane_portal", 9, kind="service"),
        End("End_ok", "Кандидат допущен\nк работе", "Lane_cand", 10),
    ],
    flows=[
        Flow("Start_bdd", "T_book"),
        Flow("T_book", "T_visit"),
        Flow("T_visit", "T_result"),
        Flow("T_result", "G_med"),
        Flow("G_med", "T_license", "да"),
        Flow("G_med", "T_med_no", "нет"),
        Flow("T_med_no", "End_med_no"),
        Flow("T_license", "T_violations"),
        Flow("T_violations", "G_bdd"),
        Flow("G_bdd", "T_final", "да"),
        Flow("G_bdd", "T_bdd_no", "нет"),
        Flow("T_bdd_no", "End_bdd_no"),
        Flow("T_final", "T_grant"),
        Flow("T_grant", "End_ok"),
    ],
)


# --------------------------------------------------------------------------
# Проект 8 — Трекер симптомов для онкопациентов
# --------------------------------------------------------------------------

symptom_tracking = Model(
    id="symptom_tracking",
    name="Ежедневный учёт симптомов и эскалация",
    pool_name="Трекер симптомов онкопациента",
    documentation=(
        "Пациент отмечает симптомы по шкале, система оценивает тяжесть и "
        "решает, достаточно ли рекомендации по самопомощи или нужно "
        "поднять флаг лечащему врачу."
    ),
    lanes=[
        Lane("Lane_pat", "Пациент", rows=1),
        Lane("Lane_app", "Приложение", rows=1),
        Lane("Lane_rules", "Модуль оценки", rows=1),
        Lane("Lane_doc", "Лечащий врач", rows=2),
    ],
    nodes=[
        Start("Start_open", "Пациент открыл\nдневник", "Lane_pat", 0, kind="message"),
        Task("T_log", "Отметить симптомы\nпо шкале", "Lane_pat", 1, kind="user"),
        Task("T_template", "Подставить шаблон\nпо нозологии", "Lane_app", 2, kind="service"),
        Task("T_grade", "Оценить степень тяжести\nпо клинической шкале", "Lane_rules", 3, kind="service"),
        Gateway("G_severity", "Тяжесть\nвыше порога?", "Lane_rules", 4),
        Task("T_advice", "Показать рекомендацию\nпо самопомощи", "Lane_app", 5, kind="send"),
        Task("T_notify_doc", "Поднять флаг\nлечащему врачу", "Lane_doc", 5, kind="send"),
        Task("T_review", "Посмотреть динамику\nсимптомов", "Lane_doc", 6, kind="user"),
        Gateway("G_action", "Требуется\nвмешательство?", "Lane_doc", 7),
        Task("T_contact", "Связаться с пациентом\nи скорректировать терапию", "Lane_doc", 8, kind="user"),
        Task("T_mark", "Отметить\nкак наблюдение", "Lane_doc", 8, row=1, kind="user"),
        Task("T_store", "Сохранить запись\nв дневнике", "Lane_app", 9, kind="service"),
        End("End_done", "Запись сохранена", "Lane_pat", 10),
    ],
    flows=[
        Flow("Start_open", "T_log"),
        Flow("T_log", "T_template"),
        Flow("T_template", "T_grade"),
        Flow("T_grade", "G_severity"),
        Flow("G_severity", "T_advice", "нет"),
        Flow("G_severity", "T_notify_doc", "да"),
        Flow("T_notify_doc", "T_review"),
        Flow("T_review", "G_action"),
        Flow("G_action", "T_contact", "да"),
        Flow("G_action", "T_mark", "нет"),
        Flow("T_advice", "T_store"),
        Flow("T_contact", "T_store"),
        Flow("T_mark", "T_store"),
        Flow("T_store", "End_done"),
    ],
)

medication_schedule = Model(
    id="medication_schedule",
    name="Календарь приёма препаратов",
    pool_name="Напоминания и учёт приверженности терапии",
    documentation=(
        "Схема приёма превращается в календарь с напоминаниями. Пропуски "
        "фиксируются и при накоплении становятся сигналом врачу: "
        "низкая приверженность терапии — клинически значимый факт."
    ),
    lanes=[
        Lane("Lane_doc", "Лечащий врач", rows=1),
        Lane("Lane_app", "Приложение", rows=2),
        Lane("Lane_sched", "Планировщик", rows=2),
        Lane("Lane_pat", "Пациент", rows=1),
    ],
    nodes=[
        Start("Start_plan", "Врач назначил\nсхему приёма", "Lane_doc", 0, kind="message"),
        Task("T_schedule", "Построить календарь\nприёмов", "Lane_app", 1, kind="service"),
        Task("T_tick", "Отследить наступление\nвремени приёма", "Lane_sched", 2, kind="service"),
        Task("T_remind", "Отправить\nнапоминание", "Lane_sched", 3, kind="send"),
        Task("T_confirm", "Отметить приём\nпрепарата", "Lane_pat", 4, kind="user"),
        Gateway("G_taken", "Приём\nподтверждён?", "Lane_app", 5),
        Task("T_mark_ok", "Зафиксировать приём", "Lane_app", 6, kind="service"),
        Task("T_repeat", "Повторить напоминание\nв пределах окна", "Lane_sched", 6, row=1, kind="send"),
        Task("T_wait", "Дождаться конца\nокна приёма", "Lane_sched", 7, row=1, kind="service"),
        Task("T_miss", "Зафиксировать пропуск\nи показать инструкцию", "Lane_app", 8, row=1, kind="service"),
        Task("T_stats", "Обновить статистику\nприверженности", "Lane_app", 9, kind="service"),
        Gateway("G_adherence", "Приверженность\nниже порога?", "Lane_app", 10),
        Task("T_flag", "Показать врачу сигнал\nо систематических пропусках", "Lane_doc", 11, kind="send"),
        End("End_flagged", "Врач уведомлён", "Lane_doc", 12),
        End("End_ok", "Календарь актуален", "Lane_pat", 11),
    ],
    flows=[
        Flow("Start_plan", "T_schedule"),
        Flow("T_schedule", "T_tick"),
        Flow("T_tick", "T_remind"),
        Flow("T_remind", "T_confirm"),
        Flow("T_confirm", "G_taken"),
        Flow("G_taken", "T_mark_ok", "да"),
        Flow("G_taken", "T_repeat", "нет"),
        Flow("T_repeat", "T_wait"),
        Flow("T_wait", "T_miss"),
        Flow("T_mark_ok", "T_stats"),
        Flow("T_miss", "T_stats"),
        Flow("T_stats", "G_adherence"),
        Flow("G_adherence", "T_flag", "да"),
        Flow("G_adherence", "End_ok", "нет"),
        Flow("T_flag", "End_flagged"),
    ],
)


# --------------------------------------------------------------------------
# Проект 9 — B2B веб-мессенджер клиентских задач
# --------------------------------------------------------------------------

task_lifecycle = Model(
    id="task_lifecycle",
    name="Жизненный цикл клиентской задачи",
    pool_name="Постановка, выполнение и оценка задачи",
    documentation=(
        "Клиент ставит задачу привычным способом — в мессенджере, "
        "сотрудник работает в веб-интерфейсе, а состояние задачи "
        "синхронизируется с CRM."
    ),
    lanes=[
        Lane("Lane_cli", "Клиент", rows=1),
        Lane("Lane_bot", "Telegram-бот", rows=1),
        Lane("Lane_msg", "Веб-мессенджер", rows=2),
        Lane("Lane_emp", "Сотрудник", rows=2),
        Lane("Lane_crm", "CRM", rows=1),
    ],
    nodes=[
        Start("Start_task", "Клиент ставит задачу\nв мессенджере", "Lane_cli", 0, kind="message"),
        Task("T_parse", "Разобрать заявку\nи определить тип", "Lane_bot", 1, kind="service"),
        Task("T_chat", "Создать чат задачи\nи подключить участников", "Lane_msg", 2, kind="service"),
        Task("T_deal", "Создать сделку", "Lane_crm", 3, kind="service"),
        Task("T_assign", "Назначить\nответственного", "Lane_msg", 4, kind="service"),
        Task("T_take", "Принять задачу\nв работу", "Lane_emp", 5, kind="user"),
        Task("T_timer", "Запустить таймер\nпо нормативу", "Lane_msg", 6, kind="service"),
        Task("T_work", "Выполнить задачу\nи приложить результат", "Lane_emp", 7, kind="user"),
        Gateway("G_sla", "Уложились\nв норматив?", "Lane_msg", 8),
        Task("T_escalate", "Эскалировать\nруководителю", "Lane_msg", 9, row=1, kind="send"),
        Task("T_review", "Проверить результат", "Lane_cli", 10, kind="user"),
        Gateway("G_accept", "Результат принят?", "Lane_cli", 11),
        Task("T_rework", "Вернуть задачу\nв работу", "Lane_emp", 12, row=1, kind="send"),
        End("End_rework", "Задача\nна доработке", "Lane_emp", 13, row=1),
        Task("T_rate", "Оценить работу\nсотрудника", "Lane_cli", 12, kind="user"),
        Task("T_close", "Закрыть сделку\nи записать оценку", "Lane_crm", 13, kind="service"),
        End("End_done", "Задача закрыта", "Lane_cli", 14),
    ],
    flows=[
        Flow("Start_task", "T_parse"),
        Flow("T_parse", "T_chat"),
        Flow("T_chat", "T_deal"),
        Flow("T_deal", "T_assign"),
        Flow("T_assign", "T_take"),
        Flow("T_take", "T_timer"),
        Flow("T_timer", "T_work"),
        Flow("T_work", "G_sla"),
        Flow("G_sla", "T_review", "да"),
        Flow("G_sla", "T_escalate", "нет"),
        Flow("T_escalate", "T_review"),
        Flow("T_review", "G_accept"),
        Flow("G_accept", "T_rate", "да"),
        Flow("G_accept", "T_rework", "нет"),
        Flow("T_rework", "End_rework"),
        Flow("T_rate", "T_close"),
        Flow("T_close", "End_done"),
    ],
)

crm_sync = Model(
    id="crm_sync",
    name="Двусторонняя синхронизация с CRM",
    pool_name="Обмен состоянием задачи между мессенджером и CRM",
    documentation=(
        "Исходящий журнал гарантирует, что изменение задачи и событие для "
        "CRM записываются вместе. Встречные изменения из CRM разрешаются "
        "по явному правилу приоритета."
    ),
    lanes=[
        Lane("Lane_msg", "Веб-мессенджер", rows=2),
        Lane("Lane_out", "Исходящий журнал", rows=1),
        Lane("Lane_adp", "Адаптер CRM", rows=2),
        Lane("Lane_crm", "CRM", rows=1),
    ],
    nodes=[
        Start("Start_change", "Изменилось состояние\nзадачи", "Lane_msg", 0, kind="message"),
        Task("T_write", "Записать изменение и событие\nв одной транзакции", "Lane_msg", 1, kind="service"),
        Task("T_store", "Сохранить событие\nдо подтверждения", "Lane_out", 2, kind="service"),
        Task("T_read", "Прочитать\nнеотправленные события", "Lane_adp", 3, kind="service"),
        Task("T_map", "Сопоставить поля\nс моделью CRM", "Lane_adp", 4, kind="service"),
        Task("T_push", "Обновить сделку", "Lane_crm", 5, kind="service"),
        Gateway("G_ok", "Обновление\nпринято?", "Lane_adp", 6),
        Task("T_ack", "Пометить событие\nдоставленным", "Lane_adp", 7, kind="service"),
        Task("T_retry", "Вернуть в очередь\nс нарастающей задержкой", "Lane_adp", 7, row=1, kind="service"),
        End("End_retry", "Повтор\nзапланирован", "Lane_adp", 8, row=1),
        Gateway("G_inbound", "Есть встречное\nизменение из CRM?", "Lane_adp", 8),
        Task("T_conflict", "Сравнить версии\nи применить приоритет", "Lane_adp", 9, kind="service"),
        Task("T_apply", "Применить изменение\nв мессенджере", "Lane_msg", 10, kind="service"),
        End("End_applied", "Состояния\nсогласованы", "Lane_msg", 11),
        End("End_synced", "Изменение\nдоставлено", "Lane_msg", 11, row=1),
    ],
    flows=[
        Flow("Start_change", "T_write"),
        Flow("T_write", "T_store"),
        Flow("T_store", "T_read"),
        Flow("T_read", "T_map"),
        Flow("T_map", "T_push"),
        Flow("T_push", "G_ok"),
        Flow("G_ok", "T_ack", "да"),
        Flow("G_ok", "T_retry", "нет"),
        Flow("T_retry", "End_retry"),
        Flow("T_ack", "G_inbound"),
        Flow("G_inbound", "T_conflict", "да"),
        Flow("G_inbound", "End_synced", "нет"),
        Flow("T_conflict", "T_apply"),
        Flow("T_apply", "End_applied"),
    ],
)


# --------------------------------------------------------------------------
# Проект 10 — B2B-платформа управления строительными проектами
# --------------------------------------------------------------------------

project_lifecycle = Model(
    id="construction_project",
    name="От технического задания до старта работ",
    pool_name="Закрытый тендер и выбор подрядчика",
    documentation=(
        "Платформа выступает управляемым посредником: подрядчиков "
        "приглашает менеджер вручную из аккредитованного пула, публичного "
        "доступа к тендеру нет."
    ),
    lanes=[
        Lane("Lane_cli", "Клиент", rows=1),
        Lane("Lane_mgr", "Менеджер платформы", rows=2),
        Lane("Lane_con", "Подрядчик", rows=1),
    ],
    nodes=[
        Start("Start_need", "У клиента появилась\nзадача", "Lane_cli", 0),
        Task("T_brief", "Создать ТЗ: описание,\nбюджет, сроки, файлы", "Lane_cli", 1, kind="user"),
        Task("T_validate", "Проверить\nи уточнить ТЗ", "Lane_mgr", 2, kind="user"),
        Gateway("G_ready", "ТЗ готово\nк тендеру?", "Lane_mgr", 3),
        Task("T_open", "Открыть\nзакрытый тендер", "Lane_mgr", 4, kind="service"),
        Task("T_clarify", "Вернуть клиенту\nна уточнение", "Lane_mgr", 4, row=1, kind="send"),
        End("End_draft", "ТЗ в черновике", "Lane_mgr", 5, row=1),
        Task("T_invite", "Пригласить аккредитованных\nподрядчиков", "Lane_mgr", 5, kind="send"),
        Task("T_bid", "Подать КП\nс разбивкой по этапам", "Lane_con", 6, kind="user"),
        Task("T_check", "Проверить полноту КП\nи адекватность смет", "Lane_mgr", 7, kind="user"),
        Task("T_compare", "Сравнить\nпредложения", "Lane_cli", 8, kind="user"),
        Task("T_choose", "Выбрать подрядчика", "Lane_cli", 9, kind="user"),
        Task("T_stages", "Сформировать таблицу этапов\nиз выбранного КП", "Lane_mgr", 10, kind="service"),
        End("End_started", "Проект переведён\nв работу", "Lane_cli", 11, kind="message"),
    ],
    flows=[
        Flow("Start_need", "T_brief"),
        Flow("T_brief", "T_validate"),
        Flow("T_validate", "G_ready"),
        Flow("G_ready", "T_open", "да"),
        Flow("G_ready", "T_clarify", "нет"),
        Flow("T_clarify", "End_draft"),
        Flow("T_open", "T_invite"),
        Flow("T_invite", "T_bid"),
        Flow("T_bid", "T_check"),
        Flow("T_check", "T_compare"),
        Flow("T_compare", "T_choose"),
        Flow("T_choose", "T_stages"),
        Flow("T_stages", "End_started"),
    ],
)

stage_acceptance = Model(
    id="stage_acceptance",
    name="Приёмка и оплата этапа",
    pool_name="Эскроу-цикл одного этапа работ",
    documentation=(
        "Деньги блокируются до начала работ и уходят подрядчику только "
        "после подтверждения приёмки клиентом. Выплату инициирует "
        "менеджер, а не автоматика."
    ),
    lanes=[
        Lane("Lane_cli", "Клиент", rows=1),
        Lane("Lane_esc", "Эскроу", rows=1),
        Lane("Lane_con", "Подрядчик", rows=1),
        Lane("Lane_mgr", "Менеджер платформы", rows=2),
    ],
    nodes=[
        Start("Start_stage", "Этап требует\nоплаты", "Lane_cli", 0, kind="message"),
        Task("T_pay", "Оплатить этап", "Lane_cli", 1, kind="user"),
        Task("T_hold", "Заблокировать средства\nна эскроу-счёте", "Lane_esc", 2, kind="service"),
        Task("T_start", "Начать работу\nпо этапу", "Lane_con", 3, kind="user"),
        Task("T_report", "Запросить приёмку\nс фото- и видеоотчётом", "Lane_con", 4, kind="user"),
        Task("T_check", "Проверить отчёт\nи соответствие объёму", "Lane_mgr", 5, kind="user"),
        Gateway("G_ok", "Отчёт принят\nменеджером?", "Lane_mgr", 6),
        Task("T_return", "Вернуть этап\nна доработку", "Lane_mgr", 7, row=1, kind="send"),
        End("End_rework", "Этап на доработке", "Lane_mgr", 8, row=1),
        Task("T_accept", "Подтвердить приёмку", "Lane_cli", 7, kind="user"),
        Task("T_release", "Инициировать выплату\nподрядчику", "Lane_mgr", 8, kind="user"),
        Task("T_payout", "Перевести средства\nиз эскроу", "Lane_esc", 9, kind="service"),
        Task("T_next", "Перевести проект\nк следующему этапу", "Lane_mgr", 10, kind="service"),
        End("End_stage", "Этап принят\nи оплачен", "Lane_cli", 11),
    ],
    flows=[
        Flow("Start_stage", "T_pay"),
        Flow("T_pay", "T_hold"),
        Flow("T_hold", "T_start"),
        Flow("T_start", "T_report"),
        Flow("T_report", "T_check"),
        Flow("T_check", "G_ok"),
        Flow("G_ok", "T_accept", "да"),
        Flow("G_ok", "T_return", "нет"),
        Flow("T_return", "End_rework"),
        Flow("T_accept", "T_release"),
        Flow("T_release", "T_payout"),
        Flow("T_payout", "T_next"),
        Flow("T_next", "End_stage"),
    ],
)


TARGETS = [
    ("01-telegram-event-bot", "01-registration.bpmn", registration),
    ("01-telegram-event-bot", "02-reminders.bpmn", reminders),
    ("01-telegram-event-bot", "03-nps-survey.bpmn", nps),
    ("02-ai-dubbing", "01-dubbing-pipeline.bpmn", dubbing),
    ("02-ai-dubbing", "02-editor-review.bpmn", editor_review),
    ("03-medical-anonymizer", "01-anonymization.bpmn", anonymization),
    ("03-medical-anonymizer", "02-reidentification.bpmn", reidentification),
    ("05-enterprise-ai-assistants", "01-rag-query.bpmn", rag_query),
    ("05-enterprise-ai-assistants", "02-medical-approval.bpmn", medical_approval),
    ("06-maritime-etp", "01-two-stage-auction.bpmn", two_stage_auction),
    ("06-maritime-etp", "02-voyage-tracking.bpmn", voyage_tracking),
    ("07-mass-hiring-platform", "01-candidate-journey.bpmn", candidate_journey),
    ("07-mass-hiring-platform", "02-driver-clearance.bpmn", driver_clearance),
    ("08-oncology-symptom-tracker", "01-symptom-tracking.bpmn", symptom_tracking),
    ("08-oncology-symptom-tracker", "02-medication-schedule.bpmn", medication_schedule),
    ("09-b2b-task-messenger", "01-task-lifecycle.bpmn", task_lifecycle),
    ("09-b2b-task-messenger", "02-crm-sync.bpmn", crm_sync),
    ("10-construction-platform", "01-project-lifecycle.bpmn", project_lifecycle),
    ("10-construction-platform", "02-stage-acceptance.bpmn", stage_acceptance),
]


def inject_previews(project: str, blocks: dict[str, str]) -> None:
    """Подставляет mermaid-превью в bpmn.md между маркерами <!-- diagram:slug -->."""
    doc = ROOT / "projects" / project / "bpmn.md"
    if not doc.exists():
        return
    text = doc.read_text(encoding="utf-8")
    for slug, mermaid in blocks.items():
        pattern = re.compile(
            rf"<!-- diagram:{re.escape(slug)} -->.*?<!-- /diagram -->",
            re.DOTALL,
        )
        if not pattern.search(text):
            continue
        block = (
            f"<!-- diagram:{slug} -->\n"
            f"```mermaid\n{mermaid}\n```\n"
            "<!-- /diagram -->"
        )
        text = pattern.sub(lambda _: block, text, count=1)
    doc.write_text(text, encoding="utf-8")


def main() -> None:
    previews: dict[str, dict[str, str]] = {}
    for project, filename, model in TARGETS:
        out_dir = ROOT / "projects" / project / "diagrams"
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = filename.removesuffix(".bpmn")

        (out_dir / filename).write_text(render(model), encoding="utf-8")
        mermaid = to_mermaid(model)
        (out_dir / f"{slug}.mmd").write_text(mermaid + "\n", encoding="utf-8")
        previews.setdefault(project, {})[slug] = mermaid

        print(f"projects/{project}/diagrams/{filename}  —  "
              f"{len(model.nodes)} элементов, {len(model.flows)} связей")

    for project, blocks in previews.items():
        inject_previews(project, blocks)


if __name__ == "__main__":
    main()
