const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

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

// Генерация QR-кода для авторизации
client.on('qr', (qr) => {
    console.log('📱 Отсканируйте QR-код для авторизации в WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Успешная авторизация
client.on('ready', () => {
    console.log('✅ WhatsApp бот готов к работе!');
    console.log('Бот будет отвечать "привет" на любое сообщение.');
});

// Обработка входящих сообщений
client.on('message', async (message) => {
    // Игнорируем сообщения от самого бота
    if (message.fromMe) return;
    
    // Игнорируем статусы и системные сообщения
    if (message.isStatus) return;
    
    try {
        // Отвечаем "привет" на любое сообщение
        await message.reply('привет');
        console.log(`✅ Ответил на сообщение от ${message.from}`);
    } catch (error) {
        console.error('❌ Ошибка при отправке сообщения:', error);
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
console.log('🚀 Запуск WhatsApp бота...');
client.initialize();

