-- Seed initial data

-- Insert default departments
INSERT INTO public.departments (id, name, sla_accept_minutes, sla_remote_minutes) VALUES
    (uuid_generate_v4(), 'TechSupport', 15, 60),
    (uuid_generate_v4(), 'Network', 10, 45),
    (uuid_generate_v4(), 'Sales', 30, 120),
    (uuid_generate_v4(), 'Billing', 20, 60),
    (uuid_generate_v4(), 'LocalOffice', 30, 120)
ON CONFLICT (name) DO NOTHING;

-- Insert sample FAQ entries
INSERT INTO public.faq_kb (title, content, tags) VALUES
    ('VPN подключение', 'Для подключения к VPN используйте следующие настройки: сервер vpn.example.com, тип подключения L2TP/IPSec, логин и пароль от личного кабинета.', ARRAY['vpn', 'network', 'connection']),
    ('Проверка скорости интернета', 'Проверить скорость интернета можно на сайте speedtest.net. Убедитесь, что закрыты все программы, использующие интернет, и подключены напрямую к роутеру.', ARRAY['internet', 'speed', 'diagnostics']),
    ('Проблемы с оплатой', 'Если возникли проблемы с оплатой, проверьте баланс в личном кабинете. При необходимости обратитесь в отдел биллинга.', ARRAY['billing', 'payment', 'account']),
    ('Настройка роутера', 'Для настройки роутера подключитесь к нему по адресу 192.168.1.1, используйте логин и пароль admin/admin (по умолчанию).', ARRAY['router', 'setup', 'network'])
ON CONFLICT DO NOTHING;

