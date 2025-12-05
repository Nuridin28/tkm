# Создание тестовых пользователей

## Способ 1: Через Supabase Dashboard (РЕКОМЕНДУЕТСЯ) ✅

### Шаг 1: Создайте пользователей через Dashboard

1. Откройте ваш Supabase проект
2. Перейдите в **Authentication** → **Users**
3. Нажмите **"Add user"** → **"Create new user"**
4. Создайте следующих пользователей:

| Email | Password | Роль (будет назначена в шаге 2) |
|-------|----------|----------------------------------|
| `admin@test.com` | `admin123` | admin |
| `operator@test.com` | `operator123` | department_user (TechSupport) |
| `engineer@test.com` | `engineer123` | engineer |
| `agent@test.com` | `agent123` | call_agent |
| `supervisor@test.com` | `supervisor123` | supervisor |

### Шаг 2: Назначьте роли через SQL

После создания пользователей выполните SQL запрос из файла `004_create_test_users.sql` в SQL Editor.

Или выполните этот упрощенный запрос:

```sql
-- Обновление ролей для созданных пользователей
DO $$
DECLARE
    v_tech_support_dept_id UUID;
    v_network_dept_id UUID;
BEGIN
    -- Получаем ID департаментов
    SELECT id INTO v_tech_support_dept_id FROM public.departments WHERE name = 'TechSupport' LIMIT 1;
    SELECT id INTO v_network_dept_id FROM public.departments WHERE name = 'Network' LIMIT 1;
    
    -- Администратор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'admin@test.com', 'Администратор', 'admin', NOW(), NOW()
    FROM auth.users WHERE email = 'admin@test.com'
    ON CONFLICT (id) DO UPDATE SET name = 'Администратор', role = 'admin', updated_at = NOW();
    
    -- Оператор
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT id, 'operator@test.com', 'Оператор Техподдержки', 'department_user', v_tech_support_dept_id, NOW(), NOW()
    FROM auth.users WHERE email = 'operator@test.com'
    ON CONFLICT (id) DO UPDATE SET name = 'Оператор Техподдержки', role = 'department_user', 
        department_id = v_tech_support_dept_id, updated_at = NOW();
    
    -- Инженер
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT id, 'engineer@test.com', 'Инженер', 'engineer', v_network_dept_id, NOW(), NOW()
    FROM auth.users WHERE email = 'engineer@test.com'
    ON CONFLICT (id) DO UPDATE SET name = 'Инженер', role = 'engineer', 
        department_id = v_network_dept_id, updated_at = NOW();
    
    -- Call Agent
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'agent@test.com', 'Оператор Колл-центра', 'call_agent', NOW(), NOW()
    FROM auth.users WHERE email = 'agent@test.com'
    ON CONFLICT (id) DO UPDATE SET name = 'Оператор Колл-центра', role = 'call_agent', updated_at = NOW();
    
    -- Супервизор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'supervisor@test.com', 'Супервизор', 'supervisor', NOW(), NOW()
    FROM auth.users WHERE email = 'supervisor@test.com'
    ON CONFLICT (id) DO UPDATE SET name = 'Супервизор', role = 'supervisor', updated_at = NOW();
END $$;
```

## Способ 2: Через Python скрипт (альтернатива)

Создайте файл `create_users.py`:

```python
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # service_role key!

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Создаем пользователей
users = [
    {
        "email": "admin@test.com",
        "password": "admin123",
        "name": "Администратор",
        "role": "admin"
    },
    {
        "email": "operator@test.com",
        "password": "operator123",
        "name": "Оператор Техподдержки",
        "role": "department_user"
    },
    {
        "email": "engineer@test.com",
        "password": "engineer123",
        "name": "Инженер",
        "role": "engineer"
    },
    {
        "email": "agent@test.com",
        "password": "agent123",
        "name": "Оператор Колл-центра",
        "role": "call_agent"
    },
    {
        "email": "supervisor@test.com",
        "password": "supervisor123",
        "name": "Супервизор",
        "role": "supervisor"
    }
]

for user_data in users:
    # Создаем пользователя в auth
    auth_response = supabase.auth.admin.create_user({
        "email": user_data["email"],
        "password": user_data["password"],
        "email_confirm": True
    })
    
    if auth_response.user:
        user_id = auth_response.user.id
        
        # Получаем department_id если нужно
        dept_id = None
        if user_data["role"] == "department_user":
            dept = supabase.table("departments").select("id").eq("name", "TechSupport").execute()
            if dept.data:
                dept_id = dept.data[0]["id"]
        
        # Создаем запись в public.users
        supabase.table("users").upsert({
            "id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
            "department_id": dept_id
        }).execute()
        
        print(f"✅ Created user: {user_data['email']}")
    else:
        print(f"❌ Failed to create: {user_data['email']}")
```

Запустите:
```bash
python create_users.py
```

## Способ 3: Быстрый SQL (если пользователи уже созданы)

Если пользователи уже созданы через Dashboard, но нет записей в `public.users`, выполните:

```sql
-- Простое создание записей для существующих auth пользователей
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    id,
    email,
    CASE 
        WHEN email = 'admin@test.com' THEN 'Администратор'
        WHEN email = 'operator@test.com' THEN 'Оператор'
        WHEN email = 'engineer@test.com' THEN 'Инженер'
        WHEN email = 'agent@test.com' THEN 'Call Agent'
        ELSE 'Пользователь'
    END as name,
    CASE 
        WHEN email = 'admin@test.com' THEN 'admin'
        WHEN email = 'operator@test.com' THEN 'department_user'
        WHEN email = 'engineer@test.com' THEN 'engineer'
        WHEN email = 'agent@test.com' THEN 'call_agent'
        ELSE 'department_user'
    END as role,
    NOW(),
    NOW()
FROM auth.users
WHERE email IN ('admin@test.com', 'operator@test.com', 'engineer@test.com', 'agent@test.com', 'supervisor@test.com')
ON CONFLICT (id) DO NOTHING;
```

## Проверка созданных пользователей

```sql
-- Проверить всех пользователей
SELECT u.id, u.email, u.name, u.role, d.name as department
FROM public.users u
LEFT JOIN public.departments d ON u.department_id = d.id
ORDER BY u.role, u.email;
```

## Вход в систему

После создания пользователей вы можете войти в систему используя:

- **Email:** `admin@test.com`
- **Password:** `admin123`

И так далее для других пользователей.

