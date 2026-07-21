# ADR-012: Вакансії як джерело даних

**Дата:** 2026-07-21  
**Статус:** Прийнято  

## Контекст
На поточний момент Opportunity Hunter аналізує RSS та GitHub Issues. Вакансії є цінним джерелом інформації про проблеми, які компанії намагаються вирішити наймаючи людей. Якщо багато вакансій з однаковими вимогами — це сигнал про незадоволений попит.

## Рішення

### Джерела даних
- **Stack Overflow Jobs** (RSS) — `https://stackoverflow.com/jobs/feed`
- **Indeed** (RSS) — пошук за ключовими словами, наприклад: `https://rss.indeed.com/rss?q=python+developer`
- **GitHub Jobs** (закритий, але можна використовувати архіви)

### Технічний підхід
- Використовувати RSS для збору вакансій (як і для інших джерел).
- Кожна вакансія має: `title`, `description`, `company`, `location`, `url`, `source`.
- Додати фільтрацію: брати тільки технічні вакансії (за ключовими словами: developer, engineer, architect тощо).
- Інтегрувати в існуючий пайплайн: вакансії перетворюються на об'єкти `Article`.

### Конфігурація
- Додати список RSS-стрічок вакансій у `config.py`.
- Наприклад:
  ```python
  JOB_RSS_SOURCES = [
      "https://stackoverflow.com/jobs/feed",
      "https://rss.indeed.com/rss?q=python+developer",
      "https://rss.indeed.com/rss?q=react+developer",
  ]
