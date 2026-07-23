# RENION — Технічна документація для розробників

**Версія:** v1.2.0  
**Дата:** 2026-07-23  

---

## Зміст

1. [Архітектурний огляд](#1-архітектурний-огляд)
2. [Структура проєкту](#2-структура-проєкту)
3. [Доменні сутності](#3-доменні-сутності)
4. [Події та шина](#4-події-та-шина)
5. [Сховище (Storage)](#5-сховище-storage)
6. [LLM Абстракція](#6-llm-абстракція)
7. [Платіжний шар](#7-платіжний-шар)
8. [Соціальний постинг](#8-соціальний-постинг)
9. [Веб-інтерфейс та шаблони](#9-веб-інтерфейс-та-шаблони)
10. [Планувальник](#10-планувальник)
11. [Як додати новий модуль](#11-як-додати-новий-модуль)

---

## 1. Архітектурний огляд

RENION побудовано за принципами **Clean Architecture** (чиста архітектура), що забезпечує:

- **Незалежність від фреймворків** — ядро не знає про FastAPI, SQLite тощо.
- **Тестованість** — бізнес-логіку можна тестувати без зовнішніх залежностей.
- **Замінність** — будь-який інфраструктурний компонент можна замінити.

### Шари:

| Шар | Призначення | Залежності |
|-----|-------------|------------|
| **domain/** | Сутності, інтерфейси, правила бізнесу | Жодних |
| **application/** | Use cases, координація об'єктів | Залежить від domain |
| **infrastructure/** | Реалізація зовнішніх сервісів (БД, LLM, платежі) | Залежить від domain та application |
| **interfaces/** | Точки входу (CLI, Web) | Залежить від application та infrastructure |

### Ключові патерни:

- **Об'єктна модель** — все є об'єктом (`AionObject`). Агенти, гіпотези, платежі — це різні типи об'єктів.
- **Event-Driven** — будь-яка зміна стану породжує подію (`Event`), яка публікується в шину.
- **Repository** — `Storage` інкапсулює доступ до даних.
- **Dependency Injection** — залежності передаються через конструктори.
- **Strategy** — різні провайдери (LLM, Payment) реалізують спільні інтерфейси.

---

## 2. Структура проєкту
src/
├── domain/ # Бізнес-сутності та інтерфейси
│ ├── object.py # AionObject
│ ├── event.py # Event
│ ├── payment.py # Payment, Transaction, Invoice
│ ├── social_post.py # SocialPost
│ ├── scan_job.py # ScanJob
│ └── interfaces/ # Абстракції для зовнішніх сервісів
│ ├── llm_provider.py # LLMProvider
│ └── payment_provider.py # PaymentProvider
│
├── application/ # Use cases
│ ├── analyzer.py # OpportunityAnalyzer (LLM аналіз)
│ ├── clustering.py # HypothesisClusterer
│ ├── market_estimator.py # MarketEstimator (TAM/SAM/SOM)
│ ├── landing_generator.py # LandingGenerator
│ ├── advertising.py # AdvertisingManager (реклама, заглушка)
│ ├── social_post_manager.py # SocialPostManager
│ ├── handlers.py # Обробники подій (ландинг, реклама, соцмережі)
│ ├── scan_runner.py # Спільна логіка сканування (для CLI та Web)
│ └── opportunity_hunter.py # Основний агент
│
├── infrastructure/ # Зовнішні сервіси
│ ├── storage.py # SQLite + aiosqlite
│ ├── event_bus.py # EventBus
│ ├── scheduler.py # APScheduler
│ ├── llm/ # LLM провайдери
│ │ ├── init.py # get_llm_provider()
│ │ ├── ollama_provider.py # OllamaProvider
│ │ └── groq_provider.py # GroqProvider
│ ├── payment/ # Платіжні провайдери
│ │ ├── simulated_provider.py # SimulatedProvider
│ │ └── stripe_provider.py # StripeProvider + Checkout
│ ├── social/ # Соціальні провайдери
│ │ ├── mastodon_poster.py # MastodonPoster
│ │ ├── twitter_poster.py # TwitterPoster
│ │ ├── reddit_poster.py # RedditPoster
│ │ └── ... # HackerNews, Medium
│ └── external/ # Зовнішні API
│ ├── rss_reader.py
│ ├── github_issues.py
│ └── jobs_reader.py
│
├── interfaces/ # Точки входу
│ ├── cli.py # CLI
│ └── web.py # FastAPI додаток
│
├── templates/ # HTML-шаблони
│ ├── landing_page.html # Головний лендинг RENION
│ ├── landing_template.html # Шаблон лендингу для гіпотези
│ ├── hypotheses.html # Список гіпотез (Jinja2)
│ └── hypothesis_detail.html # Деталі гіпотези (Jinja2)
│
├── config.py # Конфігурація джерел даних
└── locales/ # Файли перекладів (i18n) — опціонально
text


---

## 3. Доменні сутності

### 3.1. AionObject (`src/domain/object.py`)

Універсальний об'єкт — основа всього.

```python
@dataclass
class AionObject:
    type: str                         # Тип об'єкта (Hypothesis, Article, Payment, etc.)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    lifecycle: str = "active"         # active, archived, deleted
    history: List[str] = field(default_factory=list)  # IDs подій
    telemetry: Dict[str, Any] = field(default_factory=dict)

Використання: Будь-яка сутність у системі (гіпотеза, стаття, платіж, соціальний пост) зберігається як AionObject з відповідним type. Це дозволяє додавати нові типи без зміни ядра.
3.2. Event (src/domain/event.py)

Фіксує будь-яку зміну стану.
python

@dataclass
class Event:
    id: str
    object_id: str                    # ID об'єкта, до якого належить подія
    type: str                         # created, updated, deleted, article_fetched, hypothesis_generated
    payload: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    source: Optional[str] = None      # Компонент, який створив подію

3.3. Payment, Invoice, Transaction (src/domain/payment.py)

Економічний шар.
python

@dataclass
class Payment:
    amount: float
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"           # pending, completed, failed, refunded
    method: Optional[str] = None
    provider_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

@dataclass
class Invoice:
    object_id: str                    # ID гіпотези (або будь-якого об'єкта)
    amount: float
    currency: str = "USD"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "draft"             # draft, sent, paid, overdue, cancelled
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

3.4. SocialPost (src/domain/social_post.py)

Для соціальних публікацій.
python

@dataclass
class SocialPost:
    platform: str                     # twitter, mastodon, reddit, hackernews, medium
    content: str
    hypothesis_id: str
    status: str = "pending"           # pending, published, failed
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    platform_post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

3.5. ScanJob (src/domain/scan_job.py)

Для відстеження стану сканування.
python

@dataclass
class ScanJob:
    status: str = "idle"              # idle, running, completed, failed
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    hypotheses_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

4. Події та шина
4.1. EventBus (src/infrastructure/event_bus.py)

Асинхронна шина подій.
python

class EventBus:
    def __init__(self, storage):
        self.storage = storage
        self.handlers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self.queue: asyncio.Queue[Event] = asyncio.Queue()

    def subscribe(self, event_type: str, handler):
        """Підписати обробник на тип події."""
        ...

    async def publish(self, event: Event):
        """Опублікувати подію (зберігає в БД і ставить у чергу)."""
        ...

    async def run(self):
        """Запустити цикл обробки подій."""
        ...

Важливо: Після публікації події вона зберігається в БД (таблиця events), а потім обробляється асинхронно.
4.2. Основні типи подій
Тип події	Коли виникає	Обробники
article_fetched	Нова стаття збережена	(немає, тільки логування)
hypothesis_generated	Згенеровано нову гіпотезу	landing_handler, ad_handler, social_handler
ad_campaign_launched	Запущено рекламну кампанію	(немає, тільки логування)
5. Сховище (Storage)
5.1. Storage (src/infrastructure/storage.py)

Інкапсулює доступ до SQLite.

Методи:

    init() — створює таблиці.

    save_object(obj: AionObject) — зберегти/оновити об'єкт.

    get_object(object_id: str) -> Optional[Dict] — отримати об'єкт.

    get_object_by_metadata(key, value, object_type) -> Optional[Dict] — пошук за полем у metadata.

    save_event(event: Event) — зберегти подію.

    save_payment(payment: Payment) — зберегти платіж.

    get_payment(payment_id: str) -> Optional[Dict]

    get_payment_by_provider_reference(reference: str) -> Optional[Dict]

    update_payment_status(payment_id, status, completed_at)

    save_invoice(invoice: Invoice) — зберегти інвойс.

    get_invoice(invoice_id: str) -> Optional[Dict]

    update_invoice_status(invoice_id, status, payment_id, paid_at)

    save_scan_job(job: ScanJob) — зберегти стан сканування.

    get_latest_scan_job() -> Optional[Dict] — отримати останнє сканування.

    close() — закрити з'єднання.

Таблиці:
Таблиця	Призначення
objects	Усі об'єкти (універсальне сховище).
events	Усі події.
payments	Платежі.
invoices	Інвойси.
scan_jobs	Статуси сканувань.
6. LLM Абстракція
6.1. Інтерфейс (src/domain/interfaces/llm_provider.py)
python

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        pass

6.2. Реалізації
Клас	Файл	Опис
OllamaProvider	src/infrastructure/llm/ollama_provider.py	Локальна LLM (Ollama).
GroqProvider	src/infrastructure/llm/groq_provider.py	Хмарний Groq (безкоштовно).
6.3. Фабрика (src/infrastructure/llm/__init__.py)
python

def get_llm_provider():
    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "groq":
        return GroqProvider()
    else:
        return OllamaProvider()

Змінна середовища: LLM_PROVIDER=ollama|groq
7. Платіжний шар
7.1. Інтерфейс (src/domain/interfaces/payment_provider.py)
python

class PaymentProvider(ABC):
    @abstractmethod
    async def create_payment(...) -> Payment: pass
    @abstractmethod
    async def confirm_payment(...) -> bool: pass
    @abstractmethod
    async def get_payment_status(...) -> str: pass
    @abstractmethod
    async def refund_payment(...) -> bool: pass

7.2. Реалізації
Клас	Файл	Опис
SimulatedProvider	src/infrastructure/payment/simulated_provider.py	Заглушка з авто-підтвердженням.
StripeProvider	src/infrastructure/payment/stripe_provider.py	Stripe Checkout (реальна оплата).
7.3. Use Case: PaymentProcessor (src/application/use_cases/payment_processor.py)
python

class PaymentProcessor:
    async def process_invoice(invoice: Invoice) -> Optional[Payment]:
        """Створює платіж, зберігає, оновлює інвойс."""

8. Соціальний постинг
8.1. Інтерфейс (src/domain/interfaces/social_poster.py)
python

class SocialPoster(ABC):
    @abstractmethod
    async def post(content: str, hypothesis_id: str, metadata=None) -> SocialPost:
        pass
    @abstractmethod
    async def get_post_status(post_id: str) -> str:
        pass

8.2. Реалізації
Клас	Платформа	Статус
MastodonPoster	Mastodon	Активний (потребує інстансу)
TwitterPoster	Twitter	Dry-run (потребує балансу)
RedditPoster	Reddit	Dry-run
HackerNewsPoster	Hacker News	Dry-run
MediumPoster	Medium	Dry-run
8.3. Координатор: SocialPostManager (src/application/social_post_manager.py)
python

class SocialPostManager:
    async def post_hypothesis(hypothesis_id: str, hypothesis_data: dict) -> List[SocialPost]:
        """Публікує гіпотезу на всіх підключених платформах."""
        # Генерує контент для кожної платформи
        # Викликає poster.post()
        # Зберігає SocialPost у БД

9. Веб-інтерфейс та шаблони
9.1. FastAPI додаток (src/interfaces/web.py)

Маршрути:
Метод	URL	Опис
GET	/	Лендинг RENION
GET	/hypotheses	Список гіпотез
GET	/hypothesis/{id}	Деталі гіпотези
GET	/landing/{id}	Лендинг гіпотези (HTML)
POST	/api/scan	Запуск сканування
GET	/api/scan/status	Статус сканування
GET	/api/create-checkout-session/{id}	Створити Stripe Checkout сесію (редирект)

Шаблони: Використовують Jinja2 (для сторінок гіпотез) та прямі HTML-файли (для лендингів).
9.2. Шаблони HTML
9.2.1. Лендинг RENION (src/templates/landing_page.html)

Головна сторінка проєкту. Містить:

    Hero з назвою, описом, кнопкою "View Hypotheses".

    Секція "What is RENION?".

    Сітка з 6 карток (Data Collection, AI Analysis, Market Assessment, Landing Pages, Economic Layer, Social Posting).

    "How It Works" з 6 кроками.

    CTA "Ready to Launch?".

Стилі: темна тема (#0b0b12), градієнти, тіні, адаптивність (mobile-first). Використовується шрифт Inter з Google Fonts.
9.2.2. Шаблон лендингу гіпотези (src/templates/landing_template.html)

Це не сторінка, а шаблон, який заповнюється даними гіпотези.

Плейсхолдери:

    {{HEADLINE}} — заголовок.

    {{PROBLEM_DESC}} — опис проблеми (скорочений).

    {{PROBLEM}} — повний опис проблеми.

    {{MVP}} — опис MVP.

    {{CTA}} — заклик до дії.

    {{PRODUCT_NAME}} — назва продукту (зазвичай "Opportunity Hunter").

    {{FEATURES}} — список фіч (генерується LLM).

    {{HYPOTHESIS_ID}} — ID гіпотези (для посилання на оплату).

Структура:

    Hero з заголовком, описом, кнопкою "Pay Now with Stripe".

    Секція "The Problem" (картки "What people struggle with" та "Our solution").

    Секція "Why Opportunity Hunter" (3 фічі).

    Payment box з ціною $1.69 та кнопкою Stripe.

    Email-форма (опціонально, поки видалена).

    Футер.

Стилі: аналогічні лендингу RENION (темна тема, градієнти, тіні).
9.2.3. Список гіпотез (src/templates/hypotheses.html)

Jinja2-шаблон. Відображає таблицю гіпотез, статистику та кнопку "Run Scan".

Змінні:

    hypotheses — список гіпотез (кожна з полями: id, problem, headline, mvp, created_at, has_landing).

    stats — словник з total та with_landing.

JavaScript: оновлює статус сканування (polling до /api/scan/status) та запускає сканування по кнопці.
9.2.4. Деталі гіпотези (src/templates/hypothesis_detail.html)

Jinja2-шаблон. Картка з усіма полями гіпотези.

Змінні:

    hypothesis — словник з полями: id, problem, mvp, hypothesis, frequency, cta, market_tam, landing_headline, created_at, has_landing.

9.3. Стилістика (глобальний дизайн)

    Кольори: темний фон (#0b0b12), білий текст (#f0f0f5), акцентний колір (#6c6cf0), вторинний (#8b8bf7), сірий для другорядного тексту (#b0b0c8, #8080a0).

    Типографіка: шрифт Inter (Google Fonts), ваги 300, 400, 600, 700, 800, 900.

    Компоненти: картки, кнопки з градієнтами, тіні, плавні анімації (hover).

    Адаптивність: mobile-first, медіа-запити для <768px та <480px.

10. Планувальник
10.1. Scheduler (src/infrastructure/scheduler.py)

Використовує APScheduler для запуску сканування за розкладом.
python

class ScanScheduler:
    def __init__(self, storage: Storage, scan_func, schedule: str = None):
        self.schedule = schedule or "0 8 * * *"  # daily 8:00 UTC
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Додає завдання з тригером (cron або interval)
        # Запускає планувальник

    async def _run_scan(self):
        # Перевіряє, чи не виконується сканування
        # Викликає scan_func(storage)

Змінна середовища: SCAN_SCHEDULE=0 8 * * * (cron) або 1440 (хвилини).
11. Як додати новий модуль
Крок 1: Визначте тип об'єкта

Уявіть, що ви хочете додати модуль "Competitor Monitor". Визначте, які об'єкти він створює:
python

# src/domain/competitor.py (або просто використовуйте AionObject з type="Competitor")

Крок 2: Створіть use case
python

# src/application/competitor_monitor.py
class CompetitorMonitor:
    def __init__(self, storage, event_bus):
        self.storage = storage
        self.event_bus = event_bus

    async def scan(self):
        # 1. Збираємо дані
        # 2. Аналізуємо
        # 3. Створюємо об'єкти Competitor
        # 4. Публікуємо події

Крок 3: Додайте збір даних (якщо потрібно)
python

# src/infrastructure/external/competitor_api.py
async def fetch_competitors():
    ...

Крок 4: Додайте обробники подій (якщо потрібно)
python

# src/application/handlers.py (або окремий файл)
async def competitor_handler(event):
    # Реакція на нову гіпотезу або іншу подію

Крок 5: Оновіть CLI та Web

Додайте виклик нового модуля в cli.py, web.py або scan_runner.py.
Крок 6: Додайте маршрути (якщо потрібен веб-інтерфейс)
python

# src/interfaces/web.py
@app.get("/competitors")
async def list_competitors():
    # Отримуємо об'єкти type="Competitor"

Крок 7: Додайте шаблони (якщо потрібно)

Створіть HTML-шаблони в src/templates/ для відображення даних.
Крок 8: Оновіть конфігурацію

Додайте необхідні змінні середовища в .env.example та на Railway.
Приклад: додавання нового модуля "Competitor Monitor"
python

# 1. Domain: використовуємо AionObject з type="Competitor"
# 2. Application: src/application/competitor_monitor.py
class CompetitorMonitor:
    async def scan(self):
        # Отримуємо дані від API конкурентів
        data = await fetch_competitor_data()
        for item in data:
            obj = AionObject(
                type="Competitor",
                metadata={"name": item.name, "website": item.url, "funding": item.funding}
            )
            await storage.save_object(obj)
            event = Event(..., type="competitor_found", payload=item)
            await event_bus.publish(event)

# 3. Infrastructure: src/infrastructure/external/competitor_api.py
async def fetch_competitor_data():
    # Запит до зовнішнього API
    ...

# 4. Оновлюємо scan_runner.py:
async def run_scan(storage):
    # ...
    competitor_monitor = CompetitorMonitor(storage, event_bus)
    await competitor_monitor.scan()
    # ...

# 5. Веб-інтерфейс:
@app.get("/competitors")
async def list_competitors():
    # ...

Висновок

RENION надає міцну основу для створення будь-яких автономних модулів завдяки:

    Універсальній моделі об'єкта — все є об'єктом.

    Подієвій шині — модулі можуть реагувати на події один одного.

    Абстракціям — легко замінювати LLM, платежі, соцмережі.

    Чистій архітектурі — бізнес-логіка не залежить від зовнішніх факторів.

    Єдиному стилю веб-інтерфейсу — всі сторінки витримані в однаковому дизайні.

Новий модуль додається як ще один use case, без зміни ядра.
