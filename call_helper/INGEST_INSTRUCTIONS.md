# Инструкция по индексации документов

## Установка зависимостей

### Базовые зависимости (обязательно)
```bash
pip install pymupdf tiktoken supabase openai tqdm python-dotenv
```

### Для обработки книги с OCR (опционально)
```bash
pip install pytesseract pillow
```

**Важно:** Также нужно установить сам Tesseract OCR (не требуется poppler, используется PyMuPDF):

- **Windows**: Скачайте с [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) и установите
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-rus`
- **macOS**: `brew install tesseract tesseract-lang`

## Запуск индексации

```bash
python ingest.py
```

Скрипт обработает оба документа:

1. **Каталог пестицидов** (`Pesticides_SHANS.pdf`)
   - Использует PyMuPDF для извлечения текста
   - Структурное chunking: 1 страница = 1 пестицид
   - Если страница не помещается, делится на 2 чанка
   - Второй чанк получает префикс с названием пестицида

2. **Книга Мельникова** (`book_melnikov.pdf`)
   - Использует Tesseract OCR для сканированных страниц
   - Fixed size chunking: 1000 токенов на чанк с overlap 200 токенов
   - Все страницы объединяются в один текст перед chunking

## Результат

После выполнения скрипта в Supabase будут загружены чанки с метаданными:
- `source_type: "catalog"` - для каталога
- `source_type: "book"` - для книги

Чат-бот будет использовать оба источника для ответов:
- 3 чанка из каталога (продукты)
- 3 чанка из книги (агрономические знания)

