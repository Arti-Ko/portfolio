# Портфолио системного аналитика

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
└── 04-sporttech-fantasy/  — user-flow.md вместо bpmn/c4
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

Все семь моделей проверены парсером `bpmn-moddle` (тот же, что использует
bpmn.io) на уникальность идентификаторов, полноту дорожек, связность графа и
наличие DI-элементов для каждого узла и связи.
