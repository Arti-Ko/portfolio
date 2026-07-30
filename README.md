# Портфолио бизнес-аналитика

Проектная документация: BPMN 2.0-модели процессов, архитектура по C4,
пользовательские истории с критериями приёмки и формальные варианты
использования.

Все BPMN-диаграммы лежат исходниками в формате BPMN 2.0 XML — открываются в
Camunda Modeler и bpmn.io. Все схемы в документах генерируются из тех же
моделей, поэтому не могут разойтись с исходниками.

---

## Проекты

### [1. Telegram-бот регистрации на мероприятия](projects/01-telegram-event-bot/)

`BOTS` · Telegram Bot API, Python, SQL, Google Sheets API

Автоматизация сбора заявок, напоминаний и NPS-опросов внутри Telegram.
Пользователь не покидает мессенджер от анонса до обратной связи.

**10 000+** участников · **85%** конверсия в завершённую регистрацию

[BPMN](projects/01-telegram-event-bot/bpmn.md) ·
[C4](projects/01-telegram-event-bot/c4.md) ·
[User Stories](projects/01-telegram-event-bot/user-stories.md) ·
[Use Cases](projects/01-telegram-event-bot/use-cases.md)

---

### [2. Сервис AI-озвучки видеоконтента](projects/02-ai-dubbing/)

`MEDIA` · TTS/STT API, Python, REST API, FFmpeg, Figma

Автоматический дубляж: распознавание, перевод, фонетическая коррекция, синтез
и сведение в одном пайплайне. Ручная работа остаётся там, где автоматика
объективно не справляется, и система честно сообщает, где именно.

**−75%** стоимости производства · **12** языков

[BPMN](projects/02-ai-dubbing/bpmn.md) ·
[C4](projects/02-ai-dubbing/c4.md) ·
[User Stories](projects/02-ai-dubbing/user-stories.md) ·
[Use Cases](projects/02-ai-dubbing/use-cases.md)

---

### [3. Анонимизатор медицинских данных](projects/03-medical-anonymizer/)

`MEDTECH` · NLP/Python, REST API, SQL, Confluence

NLP-сервис обезличивания ПДн в медицинских документах. Встраивается в
документооборот МИС, соответствует ФЗ-152, GDPR и HIPAA Safe Harbor.

**0** инцидентов утечки · **99.9%** полнота распознавания идентификаторов

[BPMN](projects/03-medical-anonymizer/bpmn.md) ·
[C4](projects/03-medical-anonymizer/c4.md) ·
[User Stories](projects/03-medical-anonymizer/user-stories.md) ·
[Use Cases](projects/03-medical-anonymizer/use-cases.md) ·
[Тестовая матрица](projects/03-medical-anonymizer/test-matrix.md) ·
[Соответствие требованиям](projects/03-medical-anonymizer/compliance.md)

---

### [4. Fantasy Football — SportTech](projects/04-sporttech-fantasy/)

`SPORTTECH` · user flow, продуктовая аналитика

Приложение фэнтези-футбола: сборка состава в рамках бюджета, начисление очков
по реальной статистике матчей, мини-лиги. Документация построена на основе
user flow-диаграммы со свимлейнами и закрывает пробелы, найденные при её
разборе.

[User Flow](projects/04-sporttech-fantasy/user-flow.md) ·
[User Stories](projects/04-sporttech-fantasy/user-stories.md) ·
[Use Cases](projects/04-sporttech-fantasy/use-cases.md)

---

### [5. Enterprise AI-помощники для страховой компании](projects/05-enterprise-ai-assistants/)

`ENTERPRISE / INSURTECH` · on-premises LLM, RAG, граф знаний, OCR

Четыре параллельных AI-продукта в закрытом контуре: поиск по нормативной
базе, согласование медицинских назначений, паспорт проверки контрагентов,
помощник по закупкам. Жёсткое ограничение — никакого облачного ИИ,
только локальные модели.

**~45 млн ₽** бюджет программы · **4** продукта · **~2000** документов в базе знаний

[BPMN](projects/05-enterprise-ai-assistants/bpmn.md) ·
[C4](projects/05-enterprise-ai-assistants/c4.md) ·
[User Stories](projects/05-enterprise-ai-assistants/user-stories.md) ·
[Use Cases](projects/05-enterprise-ai-assistants/use-cases.md) ·
[Модель угроз](projects/05-enterprise-ai-assistants/threat-model.md)

---

### [6. ЭТП для морских грузоперевозок](projects/06-maritime-etp/)

`LOGISTICS / MARITIME` · двухэтапные торги, электронная подпись, AIS

Электронная торговая площадка для перевозок в арктической акватории:
предотбор по ледовому классу и допускам, ценовые торги среди допущенных,
отслеживание судна по AIS, полный отказ от бумажных документов.

**4** роли участников · **3** этапа поставки · цель — сделка без единого бумажного документа

[BPMN](projects/06-maritime-etp/bpmn.md) ·
[C4](projects/06-maritime-etp/c4.md) ·
[User Stories](projects/06-maritime-etp/user-stories.md) ·
[Use Cases](projects/06-maritime-etp/use-cases.md) ·
[План поставки](projects/06-maritime-etp/delivery-plan.md)

---

### [7. HR-платформа массового найма](projects/07-mass-hiring-platform/)

`HR-TECH / ENTERPRISE` · интеграционная архитектура, событийная шина

Внутренний портал найма самозанятых и ИП для крупной экосистемы. Шесть
внешних интеграций, из которых ни одна не должна ронять воронку;
дополнительный контур медконтроля и допуска для водителей.

**80 000** пользователей · **100** запросов в секунду · **6** интеграций

[BPMN](projects/07-mass-hiring-platform/bpmn.md) ·
[C4](projects/07-mass-hiring-platform/c4.md) ·
[User Stories](projects/07-mass-hiring-platform/user-stories.md) ·
[Use Cases](projects/07-mass-hiring-platform/use-cases.md) ·
[ADR](projects/07-mass-hiring-platform/adr-event-bus.md)

---

### [8. Трекер симптомов для онкопациентов](projects/08-oncology-symptom-tracker/)

`HEALTHTECH` · discovery, регуляторный анализ, финансовая модель

Мобильное приложение для онкопациентов: дневник симптомов, справочник,
календарь препаратов. Discovery-фаза: доказательная база, размер рынка,
регуляторная развилка «медизделие или нет», модель монетизации.

**+5 месяцев** жизни по данным исследований · **4,4 млн** пациентов на учёте

[Discovery](projects/08-oncology-symptom-tracker/discovery.md) ·
[BPMN](projects/08-oncology-symptom-tracker/bpmn.md) ·
[C4](projects/08-oncology-symptom-tracker/c4.md) ·
[User Stories](projects/08-oncology-symptom-tracker/user-stories.md) ·
[Use Cases](projects/08-oncology-symptom-tracker/use-cases.md)

---

### [9. B2B веб-мессенджер клиентских задач](projects/09-b2b-task-messenger/)

`B2B SAAS` · real-time, интеграция с CRM, 152-ФЗ

Веб-мессенджер задач с двусторонней синхронизацией с CRM. Ключевой вывод
анализа: клиент остаётся в привычном мессенджере, а веб решает задачу
сотрудников — два канала над одной сущностью.

**3 000** параллельных сессий · **37** вопросов discovery-вопросника

[Вопросник](projects/09-b2b-task-messenger/discovery-questions.md) ·
[BPMN](projects/09-b2b-task-messenger/bpmn.md) ·
[C4](projects/09-b2b-task-messenger/c4.md) ·
[User Stories](projects/09-b2b-task-messenger/user-stories.md) ·
[Use Cases](projects/09-b2b-task-messenger/use-cases.md)

---

### [10. B2B-платформа управления стройпроектами](projects/10-construction-platform/)

`B2B / CONSTRUCTION` · работа с противоречивыми требованиями

Платформа полного цикла: ТЗ, закрытый тендер, этапы работ, эскроу,
приёмка. Главный артефакт — журнал приведения противоречивого RFP к
одной непротиворечивой версии.

**20** разрешённых противоречий требований · **3** роли с разными интерфейсами

[Журнал решений](projects/10-construction-platform/requirements-log.md) ·
[BPMN](projects/10-construction-platform/bpmn.md) ·
[C4](projects/10-construction-platform/c4.md) ·
[User Stories](projects/10-construction-platform/user-stories.md) ·
[Use Cases](projects/10-construction-platform/use-cases.md)

---

## Что где лежит

```
projects/
├── 01-telegram-event-bot/
│   ├── README.md          — контекст, цели, результат
│   ├── bpmn.md            — процессы с разбором проектных решений
│   ├── c4.md              — контекст, контейнеры, компоненты, модель данных
│   ├── user-stories.md    — эпики, истории, критерии приёмки в Gherkin
│   ├── use-cases.md       — формальные UC в нотации Коберна
│   ├── diagrams/          — исходники .bpmn и .mmd
│   └── c4/workspace.dsl   — Structurizr DSL
├── 02-ai-dubbing/         — та же структура
├── 03-medical-anonymizer/ — + test-matrix.md, compliance.md
├── 04-sporttech-fantasy/  — user-flow.md вместо bpmn/c4
├── 05-enterprise-ai-assistants/ — + threat-model.md
├── 06-maritime-etp/       — + delivery-plan.md
├── 07-mass-hiring-platform/     — + adr-event-bus.md
├── 08-oncology-symptom-tracker/ — + discovery.md
├── 09-b2b-task-messenger/       — + discovery-questions.md
└── 10-construction-platform/    — + requirements-log.md
tools/                     — генератор BPMN и Mermaid из моделей
```

## Как читать диаграммы

**BPMN** — схемы в документах видны прямо на GitHub. Для работы с исходниками:

```bash
open https://demo.bpmn.io/           # перетащить .bpmn в окно браузера
brew install --cask camunda-modeler  # десктопный редактор
```

**C4** — уровни контекста, контейнеров и компонентов отрисованы в документах.
Машиночитаемые исходники в Structurizr DSL:

```bash
docker run -it --rm -p 8080:8080 \
  -v "$PWD/projects/01-telegram-event-bot/c4:/usr/local/structurizr" \
  structurizr/lite
```

## Как устроена генерация

BPMN-модели описаны декларативно в [`tools/build_diagrams.py`](tools/build_diagrams.py):
дорожки, узлы в сетке «дорожка × колонка», связи. Из одного описания
генерируются два представления — валидный BPMN 2.0 XML с раскладкой (BPMNDI)
и Mermaid-схема, которая подставляется в `bpmn.md` между маркерами.

Поэтому картинка в документе и файл для моделлера не могут разойтись: они
собираются из одного источника.

```bash
python3 tools/build_diagrams.py
```

Зависимостей нет — только стандартная библиотека Python 3.10+.

Все девятнадцать моделей проверены парсером `bpmn-moddle` (тот же, что использует
bpmn.io) на уникальность идентификаторов, полноту дорожек, связность графа и
наличие DI-элементов для каждого узла и связи.
