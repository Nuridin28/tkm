const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// Конфигурация
const API_URL = process.env.API_URL || 'http://localhost:8000';
const WHATSAPP_BOT_API_KEY = process.env.WHATSAPP_BOT_API_KEY || 'dev_key';

// Хранилище сессий пользователей
const userSessions = new Map();

// Создаем клиент WhatsApp
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './auth'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

// Получить или создать сессию пользователя
function getUserSession(from) {
    if (!userSessions.has(from)) {
        userSessions.set(from, {
            conversation_history: [],
            contact_info: {
                phone: from.replace('@c.us', '')
            },
            ticket_draft: null
        });
    }
    return userSessions.get(from);
}

// Анализ сообщения через RAG API (используем основной public chat API)
async function analyzeMessage(text, from, conversationHistory = []) {
    try {
        // Форматируем conversation_history в формат PublicChatMessage
        const formattedHistory = conversationHistory.map(msg => ({
            role: msg.role || 'user',
            content: msg.content || '',
            timestamp: msg.timestamp || new Date().toISOString()
        }));
        
        const response = await axios.post(
            `${API_URL}/api/public/chat`,
            {
                message: text,
                conversation_history: formattedHistory,
                contact_info: {
                    phone: from.replace('@c.us', '')
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            }
        );
        
        const result = response.data;
        
        // Адаптируем ответ под формат, ожидаемый ботом
        return {
            can_answer: result.can_answer && !result.ticketCreated,
            answer: result.response || result.answer,
            response: result.response,
            category: result.ticket_draft?.category || null,
            priority: result.ticket_draft?.priority || 'medium',
            department: result.ticket_draft?.department || 'TechSupport',
            subject: text.substring(0, 50),
            confidence: result.confidence || 0.0,
            ticketCreated: result.ticketCreated || false,
            ticket_draft: result.ticket_draft
        };
    } catch (error) {
        console.error('Error analyzing message:', error.message);
        return {
            can_answer: false,
            answer: null,
            response: null,
            category: null,
            priority: 'medium',
            department: 'TechSupport',
            subject: text.substring(0, 50),
            confidence: 0.0,
            ticketCreated: false
        };
    }
}

// Создание тикета через основной API
async function createTicket(text, from, analysis, ticketDraft = null) {
    try {
        // Если есть ticket_draft из предыдущего запроса, используем его
        const ticketData = ticketDraft || {
            subject: analysis.subject || text.substring(0, 50),
            description: text,
            language: 'ru',
            category: analysis.category || 'other',
            subcategory: 'general',
            department: analysis.department || 'TechSupport',
            priority: analysis.priority || 'medium',
            contact_info: {
                phone: from.replace('@c.us', ''),
                whatsapp_number: from.replace('@c.us', '')
            },
            conversation_history: []
        };
        
        const response = await axios.post(
            `${API_URL}/api/public/chat/create-ticket`,
            ticketData,
            {
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error creating ticket:', error.message);
        throw error;
    }
}

// Генерация QR-кода для авторизации
client.on('qr', (qr) => {
    console.log('📱 Отсканируйте QR-код для авторизации в WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Успешная авторизация
client.on('ready', () => {
    console.log('✅ WhatsApp бот готов к работе!');
    console.log('Бот использует RAG для ответов на вопросы.');
});

// Обработка входящих сообщений
client.on('message', async (message) => {
    // Игнорируем сообщения от самого бота
    if (message.fromMe) return;
    
    // Игнорируем статусы и системные сообщения
    if (message.isStatus) return;
    
    try {
        const from = message.from;
        const text = message.body.trim();
        
        if (!text) return;
        
        // Получаем сессию пользователя
        const session = getUserSession(from);
        
        // Добавляем сообщение в историю
        session.conversation_history.push({
            role: 'user',
            content: text
        });
        
        // Показываем индикатор печати
        await message.reply('⏳ Обрабатываю ваш запрос...');
        
        // Анализируем сообщение через RAG
        const analysis = await analyzeMessage(text, from, session.conversation_history);
        
        // Проверяем, был ли тикет уже создан автоматически
        if (analysis.ticketCreated) {
            // Тикет уже создан автоматически
            const answer = analysis.response || analysis.answer;
            if (answer) {
                await message.reply(
                    `${answer}\n\n✅ Тикет создан автоматически. Мы свяжемся с вами в ближайшее время.`
                );
            } else {
                await message.reply(
                    '✅ Ваш запрос зарегистрирован как тикет. Мы свяжемся с вами в ближайшее время.'
                );
            }
            console.log(`✅ Ticket auto-created for ${from}`);
        } else if (analysis.can_answer && (analysis.response || analysis.answer)) {
            // Можем ответить - отправляем ответ
            const answer = analysis.response || analysis.answer;
            // Добавляем ответ в историю
            session.conversation_history.push({
                role: 'assistant',
                content: answer
            });
            
            // Сохраняем ticket_draft если есть
            if (analysis.ticket_draft) {
                session.ticket_draft = analysis.ticket_draft;
            }
            
            await message.reply(answer);
            console.log(`✅ Ответил на сообщение от ${from} через RAG (can_answer=true)`);
        } else {
            // Не можем ответить автоматически - создаем тикет
            try {
                const ticketResult = await createTicket(text, from, analysis, session.ticket_draft);
                
                await message.reply(
                    `К сожалению, я не могу ответить на этот вопрос автоматически.\n\n` +
                    `✅ Тикет #${ticketResult.ticket_id.substring(0, 8)} создан и отправлен в техподдержку.\n` +
                    `Приоритет: ${analysis.priority}\n` +
                    `Департамент: ${analysis.department || 'TechSupport'}\n\n` +
                    `Мы свяжемся с вами в ближайшее время.`
                );
                
                console.log(`✅ Создан тикет ${ticketResult.ticket_id} для ${from}`);
            } catch (ticketError) {
                console.error('❌ Ошибка при создании тикета:', ticketError);
                await message.reply('❌ Ошибка при создании тикета. Попробуйте еще раз.');
            }
        }
        
    } catch (error) {
        console.error('❌ Ошибка при обработке сообщения:', error);
        try {
            await message.reply(
                '❌ Произошла ошибка при обработке вашего сообщения. ' +
                'Пожалуйста, попробуйте еще раз.'
            );
        } catch (replyError) {
            console.error('❌ Ошибка при отправке сообщения об ошибке:', replyError);
        }
    }
});

// Обработка ошибок авторизации
client.on('auth_failure', (msg) => {
    console.error('❌ Ошибка авторизации:', msg);
});

// Обработка отключения
client.on('disconnected', (reason) => {
    console.log('⚠️ Бот отключен:', reason);
});

// Запуск бота
console.log('🚀 Запуск WhatsApp бота с RAG...');
console.log(`API URL: ${API_URL}`);
client.initialize();
