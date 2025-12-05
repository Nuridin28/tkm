# Каталог Пестицидов - RAG Чат-бот

AI-консультант для поиска информации о пестицидах и гербицидах из каталога.

## 🚀 Структура проекта

```
.
├── app/                    # Next.js App Router
│   ├── api/
│   │   └── chat/
│   │       └── route.ts   # API endpoint для чата
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Главная страница
│   └── globals.css        # Глобальные стили
├── components/            # React компоненты
│   └── ChatInterface.tsx  # Компонент чата
├── lib/                   # Утилиты (если нужны)
├── ingest.py              # Скрипт для индексации PDF
├── Pesticides_SHANS.pdf   # Каталог пестицидов
├── book_melnikov.pdf      # Книга Мельникова (база знаний)
└── package.json           # Зависимости Node.js
```

## 📋 Требования

- Node.js 18+ 
- Python 3.8+ (для ingest.py)
- Supabase проект с pgvector
- OpenAI API ключ

## 🛠️ Установка

### 1. Установите зависимости Node.js

```bash
npm install
```

### 2. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

Заполните в `.env`:
- `OPENAI_API_KEY` - ваш OpenAI API ключ
- `SUPABASE_URL` - URL вашего Supabase проекта
- `SUPABASE_SERVICE_ROLE_KEY` - Service Role Key из Supabase

### 3. Настройте Supabase

Выполните SQL скрипт в Supabase SQL Editor:

```sql
-- Enable pgvector
create extension if not exists vector;

-- Table for chunks
create table if not exists public.chunks (
  id bigserial primary key,
  doc_id text not null,
  chunk_index int not null,
  content text not null,
  metadata jsonb default '{}'::jsonb,
  embedding vector(1536)
);

-- Index for fast ANN search
create index if not exists idx_chunks_embedding
  on public.chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Similarity search function
create or replace function public.match_documents(
  query_embedding vector(1536),
  match_count int default 5,
  filter jsonb default '{}'::jsonb
)
returns table (
  id bigint,
  doc_id text,
  chunk_index int,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  select
    c.id,
    c.doc_id,
    c.chunk_index,
    c.content,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.chunks c
  where (filter = '{}'::jsonb) or (c.metadata @> filter)
  order by c.embedding <=> query_embedding
  limit match_count;
end;
$$;
```

### 4. Установите Tesseract OCR (для обработки книги)

**Windows:**
1. Скачайте установщик с [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Установите Tesseract (по умолчанию в `C:\Program Files\Tesseract-OCR`)
3. Добавьте путь в PATH или укажите путь в коде
4. При установке выберите языки: Russian и English

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-rus
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Примечание:** Для обработки книги используется PyMuPDF для извлечения изображений страниц, поэтому `poppler` не требуется.

### 5. Индексируйте PDF документы

```bash
# Установите Python зависимости
pip install pymupdf tiktoken supabase openai tqdm python-dotenv

# Для обработки книги (опционально, если нужна книга)
pip install pytesseract pillow

# Запустите индексацию
python ingest.py
```

**Примечание:** Скрипт обрабатывает оба документа:
- **Каталог пестицидов** (`Pesticides_SHANS.pdf`) - структурное chunking по страницам
- **Книга Мельникова** (`book_melnikov.pdf`) - OCR + fixed size chunking с overlap

## 🚀 Запуск

### Development режим

```bash
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000)

### Production сборка

```bash
npm run build
npm start
```

## 💡 Использование

1. Откройте приложение в браузере
2. Задайте вопрос о пестицидах, например:
   - "Расскажи о ЗЕНКОШАНС ГОЛД"
   - "Какие пестициды подходят для картофеля?"
   - "Как убрать полынь с поля?"
   - "Какой класс опасности у препарата X?"
3. Получите ответ, который использует:
   - **Агрономические знания** из книги для понимания проблемы
   - **Конкретные продукты** из каталога для рекомендаций
4. Ответ включает указание источников (страницы и названия пестицида)

## 🔧 Технологии

- **Frontend**: Next.js 14, React, Tailwind CSS
- **Backend**: Next.js API Routes
- **AI**: OpenAI GPT-4o-mini, text-embedding-3-small
- **Database**: Supabase (PostgreSQL + pgvector)
- **PDF Processing**: PyMuPDF (fitz), Tesseract OCR (для сканированных страниц)

## 📝 Особенности

- ✅ RAG (Retrieval-Augmented Generation) архитектура
- ✅ Два источника знаний: каталог продуктов + агрономическая книга
- ✅ Векторный поиск с pgvector
- ✅ Контекстный чат с историей сообщений
- ✅ Указание источников (страницы, названия пестицидов)
- ✅ Адаптивный UI с markdown-рендерингом
- ✅ Обработка двухколоночных страниц PDF
- ✅ OCR для сканированных документов (Tesseract)
- ✅ Разные стратегии chunking: структурная (каталог) и fixed-size с overlap (книга)

## 📄 Лицензия

MIT

