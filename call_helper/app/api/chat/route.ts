import { NextRequest } from "next/server";
import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { persistSession: false, autoRefreshToken: false } }
);

async function embedQuery(query: string) {
  const resp = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: query
  });
  return resp.data[0].embedding;
}

// Extract client type from conversation history
function extractClientType(history: any[]): "corporate" | "private" | null {
  const fullText = history.map(m => m.content).join(" ").toLowerCase();
  
  // Check for explicit "yes" or corporate indicators
  const corporateKeywords = [
    "да", "корпоратив", "корпоративный", "корпоративный клиент", 
    "бизнес", "компания", "организация", "юридическое лицо", "юр. лицо"
  ];
  
  // Check for explicit "no" or negative answers
  const negativeKeywords = [
    "нет", "не корпоратив", "не являюсь корпоративным", "не корпоративный"
  ];
  
  // First check for explicit negative answers (no = private)
  for (const keyword of negativeKeywords) {
    if (fullText.includes(keyword)) return "private";
  }
  
  // Then check for corporate indicators (yes or corporate keywords = corporate)
  for (const keyword of corporateKeywords) {
    if (fullText.includes(keyword)) return "corporate";
  }
  
  return null;
}

// Categorize ticket based on content
function categorizeTicket(message: string, history: any[], clientType: "corporate" | "private"): {
  category: string;
  subcategory: string;
  department: string;
  priority: "critical" | "high" | "medium" | "low";
} {
  const fullText = (message + " " + history.map(m => m.content).join(" ")).toLowerCase();
  
  // Determine category
  let category = "other";
  let subcategory = "";
  let department = "TechSupport";
  let priority: "critical" | "high" | "medium" | "low" = "medium";
  
  // Network issues
  if (fullText.match(/интернет|интернета|подключ|соединен|связь|сеть|network|internet|wi-fi|wifi/)) {
    category = "network";
    if (fullText.match(/скорост|медлен|тормоз|lag|speed/)) {
      subcategory = "internet_speed";
      priority = "high";
    } else if (fullText.match(/нет интернет|не работает|отключ|disconnect/)) {
      subcategory = "connection_issue";
      priority = "critical";
    } else if (fullText.match(/vpn|випиэн/)) {
      subcategory = "vpn_access";
      department = "Network";
    } else {
      subcategory = "general_network";
    }
  }
  // Telephony
  else if (fullText.match(/телефон|звонок|звонки|telephony|call|phone/)) {
    category = "telephony";
    if (fullText.match(/не звон|не работает|не могу позвонить/)) {
      subcategory = "call_issue";
      priority = "high";
    } else {
      subcategory = "general_telephony";
    }
  }
  // TV
  else if (fullText.match(/телевизор|тв|tv|канал|каналы|программа/)) {
    category = "tv";
    if (fullText.match(/не работает|нет сигнал|не показывает/)) {
      subcategory = "signal_issue";
      priority = "high";
    } else {
      subcategory = "general_tv";
    }
  }
  // Billing
  else if (fullText.match(/оплат|платеж|счет|биллинг|billing|тариф|цена|стоимость|деньги/)) {
    category = "billing";
    department = "Billing";
    if (fullText.match(/не могу оплат|проблем|ошибк|не проходит/)) {
      subcategory = "payment_issue";
      priority = "high";
    } else {
      subcategory = "general_billing";
    }
  }
  // Equipment
  else if (fullText.match(/оборудован|роутер|модем|устройств|equipment|device/)) {
    category = "equipment";
    if (fullText.match(/не работает|сломал|поломк|замен/)) {
      subcategory = "equipment_failure";
      priority = "high";
    } else {
      subcategory = "general_equipment";
    }
  }
  
  // Adjust priority based on keywords
  if (fullText.match(/срочно|критич|критическ|urgent|critical|не работает|полностью/)) {
    priority = "critical";
  } else if (fullText.match(/важно|important|проблем|problem/)) {
    priority = "high";
  } else if (fullText.match(/вопрос|информац|уточнени|question/)) {
    priority = "low";
  }
  
  // Corporate clients get high priority (unless already critical)
  if (clientType === "corporate" && priority !== "critical") {
    priority = "high";
  }
  
  return { category, subcategory, department, priority };
}

// Create ticket in Supabase
async function createTicket(
  userId: string,
  clientType: "corporate" | "private",
  language: string,
  category: string,
  subcategory: string,
  department: string,
  priority: "critical" | "high" | "medium" | "low",
  confidence: number,
  content: string
) {
  const { data, error } = await supabase
    .from("tickets")
    .insert({
      user_id: userId,
      client_type: clientType,
      language: language,
      category: category,
      subcategory: subcategory,
      department: department,
      priority: priority,
      auto_resolve_candidate: false,
      confidence: confidence,
      content: content,
      status: "open",
      created_at: new Date().toISOString()
    })
    .select()
    .single();
  
  if (error) {
    console.error("Error creating ticket:", error);
    throw error;
  }
  
  return data;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message = (body?.message ?? "").toString().trim();
    const conversationHistory = body?.history || [];
    const userId = body?.user_id || "anonymous";
    const language = body?.language || "ru";

    if (!message) {
      return new Response(JSON.stringify({ error: "Пустой запрос" }), {
        status: 400,
        headers: { "content-type": "application/json" }
      });
    }

    // Check if client type is known
    const clientType = extractClientType(conversationHistory);
    
    // If client type is unknown, ask user
    if (!clientType) {
      return new Response(JSON.stringify({
        answer: "Вы корпоративный клиент?",
        sources: [],
        requiresClientType: true
      }), { 
        status: 200, 
        headers: { "content-type": "application/json" }
      });
    }
    
    // If user answered "no" (not corporate), treat as regular RAG without client type
    // Only use clientType for corporate clients (for priority in tickets)
    const isCorporate = clientType === "corporate";

    // 1) Embed the query
    const queryEmb = await embedQuery(message);

    // 2) Retrieve from Kazakhtelecom PDF - get 6 most relevant chunks
    const kazakhtelecomResult = await supabase.rpc("match_documents", {
      query_embedding: queryEmb,
      match_count: 6,
      filter: { source_type: "kazakhtelecom" },
    });

    if (kazakhtelecomResult.error) throw kazakhtelecomResult.error;

    const kazakhtelecomChunks = kazakhtelecomResult.data || [];

    // 3) Build the context
    let context = "";

    if (kazakhtelecomChunks.length > 0) {
      context += "ИНФОРМАЦИЯ ИЗ ДОКУМЕНТА КАЗАХТЕЛЕКОМ:\n\n";
      kazakhtelecomChunks.forEach((c: any, i: number) => {
        const pageInfo = c.metadata?.page ? `(Страница ${c.metadata.page})` : "";
        const similarity = c.similarity ? `(релевантность: ${c.similarity.toFixed(2)})` : "";
        context += `[Информация ${i + 1}] ${pageInfo} ${similarity}\n${c.content}\n\n`;
      });
    }

    if (!context) {
      return new Response(JSON.stringify({
        answer: "К сожалению, я не нашел информацию по вашему запросу. Попробуйте переформулировать вопрос.",
        sources: []
      }), { status: 200, headers: { "content-type": "application/json" }});
    }

    // 4) Build system prompt for Help Desk assistant with ticket logic
    // Only mention client type for corporate clients
    const systemPrompt = `Ты часть системы Help Desk Казахтелеком. Твоя основная задача — отвечать пользователю через RAG по базе знаний.

${isCorporate ? "ТИП КЛИЕНТА: Корпоративный клиент\n\n" : ""}ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА сначала пытайся ответить самостоятельно через RAG, используя информацию из предоставленных фрагментов документации (помечены как [Информация 1], [Информация 2] и т.д.)
2. НЕ придумывай информацию - используй ТОЛЬКО то, что есть в предоставленных фрагментах
3. Анализируй историю разговора - используй информацию, которую пользователь уже предоставил
4. Отвечай на русском языке профессионально и понятно
5. Всегда указывай номер страницы при цитировании из документации (формат: Страница X)
6. При упоминании конкретных данных (тарифы, условия, требования) всегда указывай ТОЧНЫЕ данные из предоставленных фрагментов
7. Будь вежливым и профессиональным

ФОРМАТИРОВАНИЕ ОТВЕТА (используй Markdown для красивого отображения):

КРИТИЧЕСКИ ВАЖНО: Всегда форматируй ответ структурированно, НЕ пиши сплошным текстом!

- Используй заголовки (##) для разделения основных разделов
- Используй нумерованные списки (1., 2., 3.) для пошаговых инструкций
- Используй маркированные списки (- или *) для перечисления вариантов, тарифов, условий
- Используй **жирный текст** для выделения важной информации (названия тарифов, цены, ключевые слова, номера телефонов)
- Используй разделители (---) между разными разделами ответа
- Структурируй информацию по тарифам в виде таблиц или списков с четким форматированием
- Добавляй пустые строки между абзацами для лучшей читаемости
- Для тарифов используй формат:
  **Название тарифа**
  - Стоимость: X тг/месяц
  - Трафик: ...
  - Звонки: ...
  
- Для инструкций используй нумерованный список с четкими шагами
- Для рекомендаций используй маркированные списки с подпунктами
- НЕ указывай источники в тексте ответа - они будут добавлены автоматически

ОПРЕДЕЛЕНИЕ УВЕРЕННОСТИ И НЕОБХОДИМОСТИ ТИКЕТА:

КРИТИЧЕСКИ ВАЖНО: Если в предоставленных фрагментах есть информация с релевантностью >= 20% (например, 26%, 30%, 35%, 40%) - это означает, что информация ЕСТЬ в документации и её ОБЯЗАТЕЛЬНО нужно использовать для ответа!

После анализа запроса определи:
- CONFIDENCE: твоя уверенность в ответе (0.0-1.0), где:
  * Если релевантность фрагментов >= 20% → CONFIDENCE должен быть >= 0.2 (минимум 0.2)
  * 0.6-1.0 = высокая уверенность, информация найдена в документации
  * 0.2-0.59 = средняя уверенность, информация есть, можно ответить (даже при 20-40% релевантности)
  * 0.0-0.19 = низкая уверенность, информации действительно нет (релевантность < 20%)

- NEEDS_TICKET: нужен ли тикет (true/false), если:
  * ТОЛЬКО если релевантность всех фрагментов < 20% (реально нет информации в документации)
  * Требуется вмешательство сотрудника Казахтелеком (выезд, техническая проблема)
  * Проблема требует ручной обработки
  * НЕ создавай тикет, если есть фрагменты с релевантностью >= 20% - используй информацию для ответа!

СТРУКТУРА ОТВЕТА:

1. Если релевантность фрагментов >= 20% (даже 20-40%):
   - ОБЯЗАТЕЛЬНО используй информацию из этих фрагментов для ответа
   - Дай четкий и структурированный ответ на основе документации
   - Форматируй ответ красиво используя Markdown (заголовки, списки, жирный текст)
   - НЕ указывай источники в тексте ответа - они будут добавлены автоматически
   - Используй информацию из нескольких фрагментов, если это помогает дать полный ответ
   - CONFIDENCE должен быть >= 0.2, NEEDS_TICKET = false
   - НЕ говори "нет информации" или "информации недостаточно" если релевантность >= 20%
   - Примеры хорошего форматирования:
     * Для тарифов: используй заголовки и списки с выделением ключевых данных
     * Для инструкций: используй нумерованные списки с четкими шагами
     * Для решения проблем: используй заголовки для разделов и маркированные списки для рекомендаций
     * Для сравнения: используй таблицы или списки с разделителями
     * НИКОГДА не пиши сплошным текстом - всегда структурируй информацию!

2. Если релевантность фрагментов < 20% ИЛИ требуется вмешательство:
   - В конце ответа добавь специальный блок в формате:
     [TICKET_REQUIRED]
     CONFIDENCE: <число от 0.0 до 1.0>
     NEEDS_TICKET: true
     REASON: <краткое объяснение, почему нужен тикет>
   
   - В ответе пользователю напиши: "Хорошо, ваш запрос зарегистрирован. Наши специалисты свяжутся с вами."

3. Если информации в предоставленных фрагментах недостаточно, но вопрос простой:
   - Задай уточняющие вопросы
   - Используй информацию из истории разговора, чтобы не спрашивать то, что уже известно

ПРИМЕРЫ ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:

Пример 1 - Тарифы:
## Доступные тарифы для мобильной связи

### 1. Премиум
- **Стоимость:** 4490 тг/месяц
- **Трафик:** Безлимит (20 ГБ на максимальной скорости)
- **Звонки на фиксированные номера РК:** бесплатно
- **Звонки внутри сети ALTEL/Tele2:** бесплатно
- **SMS внутри сети:** 300 SMS в день, свыше – 1 тг/SMS

### 2. VIP
- **Стоимость:** 6490 тг/месяц
- **Трафик:** Безлимит (45 ГБ на максимальной скорости)
- **Звонки на фиксированные номера РК:** бесплатно
- **Звонки внутри сети ALTEL/Tele2:** бесплатно

---

Пример 2 - Инструкции:
## Как подключить тариф

Для подключения тарифов мобильной связи вы можете воспользоваться следующими способами:

1. **Мобильное приложение** - подайте заявку на смену тарифного плана
2. **Личный кабинет** на сайте telecom.kz - здесь также можно изменить тариф
3. **Онлайн каналы** - обратитесь через WhatsApp и Telegram по номеру **+77080000160**
4. **Контактный центр** - позвоните по номеру **160**
5. **Офисы обслуживания** - посетите ближайший офис Казахтелеком

---

Пример 3 - Решение проблем (структурированный ответ):
## Решение проблемы с интернетом

Если предыдущие шаги не помогли, рассмотрите следующие дополнительные рекомендации:

### 1. Проверьте настройки вашего устройства
- Убедитесь, что настройки прокси корректны. Неправильные настройки могут блокировать доступ к интернету
- Проверьте файл hosts на наличие ошибок. Ошибки в этом файле могут также вызвать проблемы с подключением

### 2. Проблемы с DNS
- Убедитесь, что DNS-серверы настроены правильно. Неправильные настройки могут привести к отсутствию доступа к интернету

### 3. Проверка на вирусы
- Проверьте ваше устройство на наличие вирусов или вредоносного ПО, которые могут блокировать доступ к интернету

### 4. Использование другого устройства
- Попробуйте открыть сайт ismet.kz на другом устройстве (например, на телефоне или планшете). Если сайт открывается, проблема, вероятно, в вашем компьютере

### 5. Подключение к другой сети
- Попробуйте подключиться к другой Wi-Fi сети, чтобы исключить проблемы с вашим интернет-провайдером

---

Если после выполнения всех этих шагов интернет все еще не работает, рекомендуется обратиться в контактный центр Казахтелеком по номеру **160** или оставить заявку на вызов мастера через онлайн каналы обслуживания.

---

ВАЖНО: 
- Всегда используй Markdown для форматирования
- Разделяй информацию на логические блоки
- Используй списки для перечисления
- Выделяй важную информацию жирным текстом
- Всегда анализируй, можно ли ответить автоматически или требуется создание тикета.`;

    // 6) Build messages with conversation history
    const messages: any[] = [
      { role: "system", content: systemPrompt }
    ];

    // Add conversation history (last 10 messages to keep more context for questioning)
    const recentHistory = conversationHistory.slice(-10);
    for (const msg of recentHistory) {
      messages.push({ role: msg.role, content: msg.content });
    }

    // Build conversation history text for ticket content
    const conversationText = conversationHistory
      .map((msg: any) => `${msg.role === "user" ? "Пользователь" : "Ассистент"}: ${msg.content}`)
      .join("\n");
    const fullContent = `${conversationText}\nПользователь: ${message}`;

    // Add current query with context
    messages.push({
      role: "user",
      content: `ВОПРОС: ${message}\n\n${context}\n\nОТВЕТЬ на вопрос, используя ТОЛЬКО информацию из предоставленных выше фрагментов документации Казахтелеком. 

ВАЖНО ПО ФОРМАТИРОВАНИЮ:
- НЕ пиши сплошным текстом - всегда используй структурированное форматирование
- Используй заголовки (##) для разделов
- Используй маркированные списки (-) для рекомендаций и вариантов
- Используй нумерованные списки (1., 2., 3.) для пошаговых инструкций
- Выделяй важную информацию жирным текстом (**текст**)
- Добавляй разделители (---) между разделами
- Всегда структурируй ответ для лучшей читаемости

Если информации недостаточно или требуется вмешательство сотрудника - укажи [TICKET_REQUIRED] с CONFIDENCE и REASON. НЕ указывай источники в тексте ответа - они будут добавлены автоматически.`
    });

    // 7) Get completion from OpenAI
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.4,
      messages: messages,
      max_tokens: 2000
    });

    let answer = completion.choices[0]?.message?.content ?? "";
    
    // Check max similarity to determine if we have relevant information
    const maxSimilarity = kazakhtelecomChunks.length > 0
      ? Math.max(...kazakhtelecomChunks.map((c: any) => c.similarity || 0))
      : 0;
    
    // For non-corporate clients, remove any mentions of client type from answer
    // Treat them as regular RAG without client type restrictions
    if (!isCorporate) {
      const clientTypeMentions = [
        "для частных лиц", "для частных клиентов", "частным лицам", "частных лиц", "частных клиентов",
        "для физических лиц", "для физических клиентов", "физическим лицам", "физических лиц",
        "частное лицо", "физическое лицо", "физ. лицо",
        "для корпоративных", "корпоративным", "корпоративных клиентов", "корпоративный клиент"
      ];
      
      for (const mention of clientTypeMentions) {
        const regex = new RegExp(mention, "gi");
        answer = answer.replace(regex, "").trim();
      }
      // Clean up multiple spaces and empty lines
      answer = answer.replace(/\s+/g, " ").replace(/\n\s*\n+/g, "\n").trim();
    }
    
    // Remove sources block from answer if present
    answer = answer.replace(/\n\n---\s*\n\nИсточники:[\s\S]*$/i, "").trim();
    answer = answer.replace(/\n\nИсточники:[\s\S]*$/i, "").trim();
    answer = answer.replace(/---\s*\n\nИсточники:[\s\S]*$/i, "").trim();
    answer = answer.replace(/Источники:[\s\S]*$/i, "").trim();
    // Remove [Информация X] (Страница Y) patterns
    answer = answer.replace(/\s*\[Информация\s+\d+\]\s*\(Страница\s+\d+\)/gi, "").trim();
    answer = answer.replace(/\s*\[Информация\s+\d+\]/gi, "").trim();
    
    // Parse ticket requirement from answer - try multiple formats
    let ticketMatch = answer.match(/\[TICKET_REQUIRED\]\s*CONFIDENCE:\s*([\d.]+)\s*NEEDS_TICKET:\s*(true|false)\s*REASON:\s*([\s\S]+?)(?=\n\n|\n$|$)/);
    
    // Alternative format: CONFIDENCE: X REASON: Y (without TICKET_REQUIRED block)
    if (!ticketMatch) {
      ticketMatch = answer.match(/CONFIDENCE:\s*([\d.]+)\s*REASON:\s*([\s\S]+?)(?=\n\n|\n$|$)/i);
      if (ticketMatch) {
        // Convert to standard format: [confidence, "true", reason]
        ticketMatch = [ticketMatch[0], ticketMatch[1], "true", ticketMatch[2]];
      }
    }
    
    let needsTicket = false;
    let confidence = 0.0;
    let ticketReason = "";
    
    if (ticketMatch) {
      needsTicket = ticketMatch[2] === "true";
      confidence = parseFloat(ticketMatch[1]) || 0.0;
      ticketReason = ticketMatch[3]?.trim() || "";
      
      // Remove ticket block from answer
      answer = answer.replace(/\[TICKET_REQUIRED\][\s\S]*$/, "").trim();
      answer = answer.replace(/CONFIDENCE:\s*[\d.]+\s*REASON:\s*[^\n]+/gi, "").trim();
      
      // Check if this is a technical issue requiring intervention (equipment, technical problems)
      const fullTextForCheck = (message + " " + ticketReason + " " + conversationHistory.map((m: any) => m.content).join(" ")).toLowerCase();
      const isTechnicalIssue = /роутер|модем|оборудован|диагностик|техническ|не работает|сломал|поломк|замен|техническая проблема|помощь специалиста|требуется вмешательство|выезд|ремонт/i.test(fullTextForCheck);
      
      // Override: If we have chunks with similarity >= 20%, we should use them instead of creating ticket
      // EXCEPT for technical issues requiring intervention - always create ticket for those
      if (needsTicket && maxSimilarity >= 0.2 && !isTechnicalIssue) {
        // Don't create ticket if we have relevant information (unless it's a technical issue)
        needsTicket = false;
        confidence = Math.max(0.2, maxSimilarity);
        // Remove ticket confirmation message if present
        answer = answer.replace(/\n\nХорошо, ваш запрос зарегистрирован\. Наши специалисты свяжутся с вами\./g, "").trim();
        answer = answer.replace(/Хорошо, ваш запрос зарегистрирован\. Наши специалисты свяжутся с вами\./g, "").trim();
        answer = answer.replace(/К сожалению, в предоставленных фрагментах документации нет информации/g, "").trim();
        answer = answer.replace(/К сожалению, в предоставленных фрагментах документации не содержится информации/g, "").trim();
        answer = answer.replace(/Я не могу предоставить вам точный ответ/g, "").trim();
        answer = answer.replace(/Я не могу предоставить вам точные шаги/g, "").trim();
      }
      
      // If ticket is needed, create it
      if (needsTicket) {
        // Use clientType for ticket creation (corporate gets high priority)
        const { category, subcategory, department, priority } = categorizeTicket(message, conversationHistory, clientType);
        
        try {
          console.log("Creating ticket with:", {
            userId,
            clientType,
            category,
            subcategory,
            department,
            priority,
            confidence,
            contentLength: fullContent.length,
            ticketReason
          });
          
          const ticket = await createTicket(
            userId,
            clientType,
            language,
            category,
            subcategory,
            department,
            priority,
            confidence,
            fullContent
          );
          
          console.log("Ticket created successfully:", ticket.id);
          
          // Update answer to confirm ticket creation
          if (!answer.includes("зарегистрирован")) {
            answer += "\n\nХорошо, ваш запрос зарегистрирован. Наши специалисты свяжутся с вами.";
          }
        } catch (error: any) {
          console.error("Failed to create ticket:", error);
          console.error("Error details:", JSON.stringify(error, null, 2));
          // Continue with answer even if ticket creation fails
        }
      }
    } else {
      // Calculate confidence based on similarity scores
      // If we have chunks with similarity >= 20%, set confidence to at least 0.2
      if (maxSimilarity >= 0.2) {
        // If any chunk has similarity >= 20%, we have information to use
        confidence = Math.max(0.2, maxSimilarity);
      } else {
        // Only set low confidence if all chunks are below 20%
        confidence = maxSimilarity;
      }
    }

    // Extract sources with metadata
    const sources = kazakhtelecomChunks.map((c: any) => ({
      content: c.content,
      page: c.metadata?.page,
      source_type: "kazakhtelecom",
      similarity: c.similarity
    }));

    return new Response(JSON.stringify({
      answer: answer,
      sources: sources,
      confidence: confidence,
      ticketCreated: needsTicket
    }), { 
      status: 200, 
      headers: { "content-type": "application/json" }
    });

  } catch (err: any) {
    console.error("api/chat error:", err?.message || err);
    return new Response(JSON.stringify({ 
      error: err?.message || "Произошла ошибка при обработке запроса" 
    }), {
      status: 500,
      headers: { "content-type": "application/json" }
    });
  }
}

