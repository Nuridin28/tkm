# Где получается и проверяется роль

## 🎯 Фронтенд (React)

### 1. Получение роли из базы данных

**Файл:** `frontend/src/contexts/AuthContext.tsx` (строка 66-194)

```typescript
// Загрузка профиля из таблицы public.users
const loadUserProfile = async (userId: string) => {
  const queryPromise = supabase
    .from('users')                    // ← Таблица public.users
    .select('id, email, name, role, department_id')
    .eq('id', userId)
    .single()
  
  const { data, error } = await queryPromise
  
  // Роль берется из data.role
  return {
    id: data.id,
    email: data.email,
    name: data.name,
    role: String(data.role).trim(),  // ← РОЛЬ ЗДЕСЬ
    department_id: data.department_id
  }
}
```

**Где используется:**
- После логина вызывается `loadUserProfile(userId)`
- Роль сохраняется в `userProfile.role`
- Используется для редиректа на нужный дашборд

### 2. Проверка роли для доступа к роутам

**Файл:** `frontend/src/components/ProtectedRoute.tsx` (строка 20-26)

```typescript
if (allowedRoles && userProfile) {
  const userRole = userProfile.role  // ← Роль из public.users
  if (!allowedRoles.includes(userRole)) {
    return <Navigate to="/dashboard" replace />
  }
}
```

**Пример использования:**
```tsx
<ProtectedRoute allowedRoles={['admin', 'supervisor']}>
  <AdminDashboard />
</ProtectedRoute>
```

### 3. Редирект по роли

**Файл:** `frontend/src/pages/Dashboard.tsx` (строка 49-69)

```typescript
const role = userProfile.role  // ← Роль из public.users

if (role === 'admin' || role === 'supervisor') {
  navigate('/admin')
} else if (role === 'engineer') {
  navigate('/engineer')
} else if (role === 'call_agent') {
  navigate('/call-agent')
} else {
  navigate('/department')
}
```

---

## 🔧 Бэкенд (FastAPI)

### 1. Получение роли (ПРОБЛЕМА!)

**Файл:** `backend/app/core/auth.py` (строка 35-44)

```python
def require_role(allowed_roles: list[str]):
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        # ⚠️ ПРОБЛЕМА: Роль берется из user_metadata, а не из public.users!
        user_role = user.get("role") or user.get("user_metadata", {}).get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {allowed_roles}"
            )
        return user
    return role_checker
```

**Проблема:** 
- Роль берется из `user_metadata` (данные из `auth.users`)
- Но роль должна браться из `public.users` (как на фронтенде)

### 2. Использование проверки роли

**Файл:** `backend/app/api/v1/admin.py` (строка 18)

```python
@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
    # ↑ Проверка роли здесь
) -> MetricsResponse:
    # Только admin или supervisor могут получить метрики
    ...
```

---

## ❌ Текущая проблема на бэкенде

**Проблема:** Бэкенд проверяет роль из `user_metadata`, но роль хранится в `public.users`

**Решение:** Нужно загружать роль из `public.users` на бэкенде

---

## ✅ Исправление для бэкенда

Нужно изменить `backend/app/core/auth.py`:

```python
async def get_user_role_from_db(user_id: str, supabase: Client) -> Optional[str]:
    """Get user role from public.users table"""
    try:
        result = supabase.table("users").select("role").eq("id", user_id).single().execute()
        if result.data:
            return result.data.get("role")
    except Exception as e:
        print(f"Error loading user role: {e}")
    return None

def require_role(allowed_roles: list[str]):
    async def role_checker(
        user: dict = Depends(get_current_user),
        supabase: Client = Depends(get_supabase)
    ) -> dict:
        user_id = user.get("id")
        
        # Загрузить роль из public.users
        user_role = await get_user_role_from_db(user_id, supabase)
        
        # Fallback на user_metadata если роль не найдена в БД
        if not user_role:
            user_role = user.get("role") or user.get("user_metadata", {}).get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {allowed_roles}, but user has: {user_role}"
            )
        return user
    return role_checker
```

---

## 📊 Схема получения роли

### Фронтенд:
```
1. Логин → Supabase Auth → получает JWT токен
2. loadUserProfile(userId) → запрос к public.users
3. Получает role из public.users
4. Сохраняет в userProfile.role
5. Использует для редиректа и проверки доступа
```

### Бэкенд (текущая реализация):
```
1. Запрос с токеном → get_current_user()
2. Проверяет токен через Supabase Auth
3. Получает user из auth.users (с user_metadata)
4. require_role() берет роль из user_metadata ❌
5. Проблема: роль не из public.users!
```

### Бэкенд (исправленная версия):
```
1. Запрос с токеном → get_current_user()
2. Проверяет токен через Supabase Auth
3. Получает user_id
4. Запрос к public.users для получения роли ✅
5. Проверяет роль из public.users
```

---

## 🔍 Где проверить роль в базе данных

```sql
-- Проверить роль пользователя
SELECT id, email, name, role 
FROM public.users 
WHERE email = 'admin@test.com';

-- Обновить роль
UPDATE public.users
SET role = 'admin'
WHERE email = 'admin@test.com';
```

---

## 📝 Резюме

| Где | Откуда берется роль | Файл | Статус |
|-----|-------------------|------|--------|
| **Фронтенд** | `public.users` | `AuthContext.tsx` | ✅ Правильно |
| **Бэкенд** | `user_metadata` (auth.users) | `auth.py` | ❌ Неправильно |
| **Нужно** | `public.users` | `auth.py` | 🔧 Требует исправления |

