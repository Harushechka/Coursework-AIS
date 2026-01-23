# МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ
федеральное государственное автономное образовательное
учреждение высшего образования
НАЦИОНАЛЬНЫЙ ИССЛЕДОВАТЕЛЬСКИЙ
ТОМСКИЙ ПОЛИТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ

Инженерная школа информационных технологий и робототехники
Отделение информационных технологий
Направление информационные системы и технологии

Курсовой проект
по дисциплине
«АРХИТЕКТУРА ИНФОРМАЦИОННЫХ СИСТЕМ»

Выполнил:
Студент группы 8И32 	_________________	М.Р. Дубовская,
      К.В. Нохрина,
С.Ю. Соболевский

Проверил:
Старший преподаватель  ИШИТР	_________________	В.А. Коровкин

Томск 2025

## Оглавление

1. Введение	2
1.1 Описание информационной системы	2
1.2 Домен и поддомены	3
1.3 Технологический стек	4
2. Архитектура системы	5
2.1 Обзор микросервисов	5
2.2 Диаграмма C4 Level 1 — Контекст	6
2.3 Диаграмма C4 Level 2 — Контейнеры	7
2.4 Синхронное и асинхронное взаимодействие	8
3. Детальное описание микросервисов	10
3.1 API Gateway Service	10
3.2 Auth Service	12
3.3 Customer Service	14
3.4 Vehicle Catalog Service	16
3.5 Inventory Service	18
3.6 Sales Service	20
3.7 Pricing Discount Service	22
3.8 Payment Service	24
3.9 Financing Service	26
3.10 Insurance Service	28
3.11 Service Booking Service	30
3.12 Notification Service	32
3.13 Reporting Analytics Service	34
3.14 Logging Monitoring Service	36
3.15 Admin Config Service	38
4. API	40
4.1 Сводка по API	40
4.2 Внешний REST API	40
4.3 gRPC API	42
4.4 Асинхронный API — RabbitMQ Topics	43
5. Паттерны проектирования	45
5.1 API Gateway	45
5.2 Database per Service	46
5.3 Saga (Choreography)	47
5.4 Event Sourcing	48
5.5 Circuit Breaker	49
5.6 CQRS	50
5.7 Service Discovery	51
6. Заключение	52
Основные результаты:	52
Перспективы развития:	53
7. Список литературы	54

## 1. Введение

### 1.1 Описание информационной системы

Данная курсовая работа посвящена проектированию и разработке микросервисной информационной системы «Автосалон» — комплексной платформы для управления продажами автомобилей, складом, сервисным обслуживанием и сопутствующими финансовыми операциями.

**Основные функциональные возможности системы:**

1. **Управление каталогом и складом:**
   - Ведение каталога моделей автомобилей с характеристиками, комплектациями и ценами
   - Учет наличия конкретных автомобилей на складе (VIN, состояние, локация)
   - Резервирование автомобилей под заказы
   - Поиск и фильтрация автомобилей по различным критериям

2. **Продажи и оформление заказов:**
   - Создание и управление заказами на покупку автомобилей
   - Расчет цен с учетом скидок, акций и промокодов
   - Статусное отслеживание заказов (черновик, подтвержден, оплачен, выдан)
   - Привязка заказов к клиентам и автомобилям

3. **Финансовые операции:**
   - Обработка платежей за автомобили
   - Кредитование (предварительный расчет, заявки на кредит, графики платежей)
   - Страхование автомобилей (ОСАГО/КАСКО)
   - Интеграция с внешними платежными системами и банками

4. **Сервисное обслуживание:**
   - Запись на техническое обслуживание и ремонт
   - Управление слотами времени и мастерами
   - История обслуживания автомобилей

5. **Управление клиентами (CRM):**
   - Ведение базы клиентов с контактами и историей взаимодействий
   - Сегментация клиентов по различным критериям
   - Отслеживание предпочтений и истории покупок

6. **Аналитика и отчетность:**
   - Отчеты по продажам и доходам
   - Анализ популярности моделей и эффективности акций
   - Статистика по финансовым показателям
   - Метрики работы сервиса

7. **Администрирование и конфигурация:**
   - Управление пользователями и ролями (клиенты, менеджеры, администраторы)
   - Настройка филиалов, продавцов и тарифов
   - Конфигурация системы скидок и акций

8. **Уведомления и коммуникации:**
   - Автоматические уведомления о статусе заказов
   - Напоминания о записях на сервис
   - Информирование о платежах и изменениях статуса

9. **Техническая инфраструктура:**
   - Централизованная аутентификация и авторизация
   - API-шлюз для внешнего доступа
   - Логирование и мониторинг системы
   - Масштабируемая архитектура на основе микросервисов

**Целевая аудитория:**
- Клиенты автосалона: частные лица, заинтересованные в покупке автомобиля
- Менеджеры по продажам: специалисты по работе с клиентами
- Менеджеры по кредитованию: специалисты по финансовым услугам
- Специалисты по страхованию: агенты по оформлению полисов
- Координаторы сервисного обслуживания: менеджеры ТО и ремонта
- Администраторы системы: руководители автосалона и IT-специалисты
- Аналитики: специалисты по работе с отчетностью

### 1.2 Домен и поддомены

**Основной домен:** Розничная торговля автомобилями и сопутствующие финансовые услуги

Основной домен охватывает комплексную деятельность автомобильного дилера, включающую продажу транспортных средств, финансовые операции, послепродажное обслуживание и управление складскими запасами.

**Поддомены:**

| Поддомен | Тип | Описание | Сервис |
|----------|-----|----------|---------|
| Продажа автомобилей | Core | Оформление заказов, управление жизненным циклом заказа | Sales Service |
| CRM клиентов | Core | Ведение клиентской базы, история взаимодействий | Customer Service |
| Управление складом и каталогом | Core | Каталог автомобилей, учет наличия, резервирование | Inventory Service, Vehicle Catalog Service |
| Финансы и платежи | Core | Обработка платежей, транзакции | Payment Service |
| Кредитование и страхование | Supporting | Финансирование, заявки на кредит, страховые полисы | Financing Service, Insurance Service |
| Сервис и ремонт | Supporting | Запись на ТО, управление ремонтными работами | Service Booking Service |
| Маркетинг и рекомендации | Supporting | Акции, скидки, промокоды, персонализация | Pricing Discount Service |
| Отчетность и аналитика | Generic | Агрегация данных, финансовые и операционные отчеты | Reporting Analytics Service |
| Техническая инфраструктура | Generic | Аутентификация, API-шлюз, логирование, конфигурация | Auth Service, API Gateway Service, Logging Monitoring Service, Admin Config Service |
| Уведомления | Generic | Отправка уведомлений пользователям | Notification Service |

### 1.3 Технологический стек

**Backend:**
1. Python 3.11 – Основной язык разработки
2. FastAPI 0.104 – Асинхронный REST API фреймворк
3. SQLAlchemy 2.0 – ORM для работы с реляционными БД
4. Pydantic 2.0 – Валидация данных и сериализация
5. aio-pika 9.0 – Асинхронный клиент RabbitMQ
6. httpx – Асинхронный HTTP клиент для межсервисного взаимодействия
7. pytest – Фреймворк для тестирования
8. pytest-asyncio – Поддержка асинхронных тестов

**Базы данных:**
1. PostgreSQL 15 – Основное хранилище данных (Database-per-Service паттерн)
2. Каждая БД имеет отдельный порт:
   - Auth DB: localhost:54321, database: `auth_db`
   - Payment DB: localhost:54322, database: `payment_db`
   - Financing DB: localhost:54323, database: `financing_db`
   - Insurance DB: localhost:54324, database: `insurance_db`

**Инфраструктура:**
1. Docker & Docker Compose – Контейнеризация и оркестрация
2. RabbitMQ 3-management – Брокер сообщений для асинхронного взаимодействия
3. RabbitMQ Management UI: http://localhost:15672 (guest/guest)
4. Nginx – API Gateway, балансировка нагрузки (запланировано)
5. Prometheus – Сбор метрик (запланировано)
6. Grafana – Визуализация метрик (запланировано)

**Безопасность:**
1. JWT (JSON Web Tokens) с алгоритмом HS256 и refresh токенами
2. BCrypt для хеширования паролей
3. CORS Middleware
4. Ролевая модель доступа (RBAC)

## 2. Архитектура системы

### 2.1 Обзор микросервисов

Система состоит из 5 реализованных микросервисов и инфраструктурных компонентов (Database-per-Service паттерн):

| Сервис | Порт | База данных | Описание |
|--------|------|-------------|----------|
| API Gateway Service | 8000 | - | Единая точка входа, маршрутизация, аутентификация |
| Auth Service | 8001 | auth_db (54321) | Аутентификация и управление пользователями |
| Payment Service | 8002 | payment_db (54322) | Обработка платежей за автомобили |
| Financing Service | 8003 | financing_db (54323) | Кредитование и расчет графиков платежей |
| Insurance Service | 8004 | insurance_db (54324) | Страхование автомобилей и управление полисами |

**Инфраструктурные компоненты:**
- **RabbitMQ**: Брокер сообщений (порты 5672, 15672)
- **PostgreSQL**: 4 отдельные базы данных по одной на сервис
- **Docker Compose**: Оркестрация всех компонентов

### 2.2 Диаграмма C4 Level 1 — Контекст

**Описание элементов:**
1. Клиент автосалона — конечный пользователь системы (покупатель автомобиля)
2. Менеджер автосалона — сотрудник, управляющий продажами и обслуживанием
3. Администратор — руководитель автосалона, управляющий системой
4. Информационная система "Автосалон" — разрабатываемая микросервисная платформа
5. Банковская система — внешняя система для кредитования
6. Страховая компания — внешняя система для страхования
7. Платежный шлюз — внешняя система обработки платежей

```
[Клиент автосалона] → [ИС "Автосалон"] → [Банковская система]
[Менеджер автосалона] → [ИС "Автосалон"] → [Страховая компания]
[Администратор] → [ИС "Автосалон"] → [Платежный шлюз]
```

### 2.3 Диаграмма C4 Level 2 — Контейнеры

**Описание контейнеров:**
1. Web Frontend (SPA) — пользовательский интерфейс (запланирован)
2. API Gateway — единая точка входа для всех запросов (порт 8000)
3. Auth Service — сервис аутентификации (порт 8001)
4. Payment Service — обработка платежей (порт 8002)
5. Financing Service — кредитование (порт 8003)
6. Insurance Service — страхование (порт 8004)
7. Message Broker (RabbitMQ) — асинхронная коммуникация (порты 5672, 15672)
8. Databases Cluster — 4 отдельные базы данных PostgreSQL

```
[Web Frontend] → [API Gateway] → [Auth Service]
[API Gateway] → [Payment Service] → [payment_db]
[API Gateway] → [Financing Service] → [financing_db]
[API Gateway] → [Insurance Service] → [insurance_db]
[Business Services] → [RabbitMQ] → [Business Services]
```

### 2.4 Синхронное и асинхронное взаимодействие

#### 2.4.1 Синхронное взаимодействие
REST API через API Gateway:
- API Gateway → Auth Service (проверка токенов)
- API Gateway → Business Services (маршрутизация запросов)
- Sales Service → Pricing Discount Service (расчет цены)
- Sales Service → Inventory Service (проверка наличия)

#### 2.4.2 Асинхронное взаимодействие
Event-driven архитектура через RabbitMQ:
- Sales Service публикует OrderCreated → Notification Service отправляет уведомления
- Payment Service публикует PaymentSucceeded → Sales Service обновляет статус заказа
- Service Booking Service публикует BookingCreated → Notification Service отправляет напоминания

## 3. Детальное описание микросервисов

### 3.1 API Gateway Service

**Назначение:** Единая точка входа для всех клиентских запросов.

**Ответственность:**
1. Маршрутизация запросов к соответствующим микросервисам
2. Аутентификация и авторизация пользователей
3. Агрегация данных из нескольких сервисов
4. Балансировка нагрузки
5. Логирование запросов

**Модель данных:**
- Не имеет собственной базы данных
- Кеширует JWT токены для валидации

**Архитектура компонентов:**
```
[Request Handler] → [Auth Middleware] → [Router] → [Aggregator] → [Response Formatter]
```

**API эндпоинты:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | / | Общая статистика системы |
| GET | /health | Проверка здоровья API Gateway |
| POST | /auth/* | Маршрутизация в Auth Service |
| GET/POST | /sales/* | Маршрутизация в Sales Service |
| GET/POST | /payment/* | Маршрутизация в Payment Service |

### 3.2 Auth Service

**Назначение:** Сервис аутентификации и управления пользователями.

**Ответственность:**
1. Регистрация новых пользователей
2. Аутентификация (login/logout) с JWT токенами
3. Генерация и валидация access и refresh токенов
4. Управление профилями пользователей
5. RBAC (Role-Based Access Control) с ролями client/manager/admin

**Модель данных:**
```sql
User:
- id: integer (PK)
- email: string (unique)
- full_name: string
- phone: string
- hashed_password: string (BCrypt)
- role: enum (client, manager, admin)
- is_active: boolean
- created_at: datetime
- updated_at: datetime
```

**Архитектура компонентов:**
```
[Auth Controller] → [User CRUD] → [SQLAlchemy Repository] → [PostgreSQL auth_db]
```

**API эндпоинты:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /register | Регистрация нового пользователя |
| POST | /token | Получение access и refresh токенов |
| POST | /logout | Выход из системы |
| POST | /refresh | Обновление пары токенов |
| GET | /users/me | Данные текущего пользователя |
| GET | /users/{id} | Данные пользователя по ID |
| GET | /users/ | Список пользователей (admin only) |

**Пример API вызова:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "Иван Иванов",
    "password": "password123",
    "phone": "+7-999-123-45-67",
    "role": "client"
  }'
```

### 3.3 Customer Service

**Назначение:** Сервис управления клиентской базой.

**Ответственность:**
1. CRUD операции с клиентами
2. Управление контактами клиентов
3. История взаимодействий
4. Сегментация клиентов
5. Интеграция с другими сервисами

**Модель данных:**
```sql
Customer:
- id: integer (PK)
- user_id: integer (FK)
- full_name: string
- email: string
- phone: string
- address: text
- created_at: datetime

CustomerInteraction:
- id: integer (PK)
- customer_id: integer (FK)
- type: enum (call, email, visit)
- description: text
- created_at: datetime
```

### 3.4 Vehicle Catalog Service

**Назначение:** Сервис управления каталогом автомобилей.

**Ответственность:**
1. Управление моделями автомобилей
2. Хранение характеристик и комплектаций
3. Управление ценами
4. Поиск и фильтрация автомобилей

**Модель данных:**
```sql
VehicleModel:
- id: integer (PK)
- brand: string
- model: string
- year: integer
- base_price: decimal
- specifications: jsonb

VehicleModification:
- id: integer (PK)
- model_id: integer (FK)
- name: string
- price: decimal
- features: jsonb
```

### 3.5 Inventory Service

**Назначение:** Сервис учета автомобилей на складе.

**Ответственность:**
1. Учет конкретных экземпляров автомобилей
2. Резервирование автомобилей
3. Отслеживание локаций
4. Управление статусами автомобилей

**Модель данных:**
```sql
Vehicle:
- id: integer (PK)
- vin: string (unique)
- model_id: integer (FK)
- modification_id: integer (FK)
- color: string
- mileage: integer
- condition: enum (new, used)
- location: string
- status: enum (available, reserved, sold)
```

### 3.6 Sales Service

**Назначение:** Сервис управления продажами автомобилей.

**Ответственность:**
1. Создание и управление заказами
2. Связывание заказов с клиентами и автомобилями
3. Управление жизненным циклом заказа
4. Интеграция с платежами и резервированиями

**Модель данных:**
```sql
SaleOrder:
- id: integer (PK)
- customer_id: integer (FK)
- vehicle_id: integer (FK)
- status: enum (draft, confirmed, paid, completed, cancelled)
- total_price: decimal
- created_at: datetime
- updated_at: datetime
```

### 3.7 Pricing Discount Service

**Назначение:** Сервис расчета цен и управления скидками.

**Ответственность:**
1. Расчет финальной цены заказа
2. Управление акциями и скидками
3. Обработка промокодов
4. Правила ценообразования

**Модель данных:**
```sql
Discount:
- id: integer (PK)
- code: string (unique)
- type: enum (percentage, fixed)
- value: decimal
- valid_from: datetime
- valid_to: datetime
- usage_limit: integer
```

### 3.3 Payment Service

**Назначение:** Сервис обработки платежей за автомобили.

**Ответственность:**
1. Обработка платежных транзакций за заказы
2. Управление статусами платежей (pending, processing, completed, failed)
3. Логирование всех изменений статуса платежей
4. Интеграция с платежными системами (эмулируется)
5. Обработка различных методов оплаты

**Модель данных:**
```sql
Payment:
- id: integer (PK)
- order_id: integer (внешняя ссылка)
- user_id: integer
- amount: float
- currency: string (default: "RUB")
- method: enum (card, bank_transfer, cash, credit)
- status: enum (pending, processing, completed, failed, cancelled)
- transaction_id: string (unique)
- description: string
- card_last_four: string(4)
- bank_reference: string
- created_at: datetime
- updated_at: datetime

PaymentLog:
- id: integer (PK)
- payment_id: integer (FK)
- action: string
- old_status: enum
- new_status: enum
- message: string
- created_at: datetime
```

**Архитектура компонентов:**
```
[Payment Controller] → [Payment CRUD] → [SQLAlchemy Repository] → [PostgreSQL payment_db]
[Payment Service] → [RabbitMQ Publisher] (асинхронные события)
```

**API эндпоинты:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /payments | Создание платежа |
| GET | /payments | Список платежей пользователя |
| GET | /payments/{id} | Детали платежа |
| PUT | /payments/{id}/status | Обновление статуса платежа |
| GET | /stats | Статистика платежей |

**Пример API вызова:**
```bash
curl -X POST "http://localhost:8000/payment/payments" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 1500000.00,
    "method": "card",
    "description": "Покупка автомобиля Toyota Camry"
  }'
```

### 3.4 Financing Service

**Назначение:** Сервис кредитования и финансовых расчетов для автомобилей.

**Ответственность:**
1. Расчет кредитных программ и ежемесячных платежей
2. Управление жизненным циклом заявок на кредитование
3. Формирование графиков платежей
4. Интеграция с банковскими системами (эмулируется)
5. Оценка кредитоспособности клиентов

**Модель данных:**
```sql
FinancingApplication:
- id: integer (PK)
- user_id: integer
- order_id: integer
- vehicle_price: float
- down_payment: float
- loan_amount: float
- financing_type: enum (car_loan, leasing, installment)
- term_months: integer
- interest_rate: float
- monthly_payment: float
- total_payment: float
- status: enum (draft, submitted, under_review, approved, rejected, active, completed, defaulted)
- employment_status: string
- monthly_income: float
- credit_score: integer (300-850)
- approved_at: datetime
- approved_by: integer

FinancingSchedule:
- id: integer (PK)
- application_id: integer (FK)
- payment_number: integer
- due_date: datetime
- principal_amount: float
- interest_amount: float
- total_amount: float
- remaining_balance: float
- is_paid: boolean
- paid_at: datetime
```

**Архитектура компонентов:**
```
[Financing Controller] → [Financing CRUD] → [SQLAlchemy Repository] → [PostgreSQL financing_db]
[Calculator Service] → [Payment Schedule Generator]
[RabbitMQ Publisher] → [асинхронные события]
```

**API эндпоинты:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /applications | Создание заявки на кредит |
| GET | /applications | Список заявок пользователя |
| GET | /applications/{id} | Детали заявки |
| PUT | /applications/{id} | Обновление заявки |
| POST | /applications/{id}/submit | Подача заявки на рассмотрение |
| GET | /applications/{id}/schedule | График платежей |
| PUT | /applications/{id}/status | Изменение статуса (менеджер) |

**Пример API вызова:**
```bash
curl -X POST "http://localhost:8000/financing/applications" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "vehicle_price": 2000000.00,
    "down_payment": 400000.00,
    "term_months": 36,
    "financing_type": "car_loan",
    "employment_status": "employed",
    "monthly_income": 80000.00
  }'
```

### 3.5 Insurance Service

**Назначение:** Сервис страхования автомобилей и управления полисами.

**Ответственность:**
1. Расчет стоимости страховых полисов
2. Оформление и управление полисами различных типов
3. Обработка страховых случаев и выплат
4. Интеграция со страховыми компаниями (эмулируется)
5. Генерация уникальных номеров полисов

**Модель данных:**
```sql
InsurancePolicy:
- id: integer (PK)
- user_id: integer
- order_id: integer
- vehicle_id: integer (опционально)
- policy_number: string (unique)
- insurance_type: enum (osago, kasko, life, health)
- provider_name: string
- coverage_amount: float
- premium_amount: float
- deductible: float
- start_date: datetime
- end_date: datetime
- status: enum (draft, quoted, purchased, active, expired, cancelled, claimed)
- is_paid: boolean
- vehicle_make: string
- vehicle_model: string
- vehicle_year: integer
- vehicle_vin: string

InsuranceClaim:
- id: integer (PK)
- policy_id: integer (FK)
- user_id: integer
- claim_number: string (unique)
- incident_date: datetime
- incident_type: string
- incident_description: string
- claimed_amount: float
- approved_amount: float
- paid_amount: float
- status: string (submitted, under_review, approved, rejected, paid)
- assessor_notes: string
- rejection_reason: string
```

**Архитектура компонентов:**
```
[Insurance Controller] → [Insurance CRUD] → [SQLAlchemy Repository] → [PostgreSQL insurance_db]
[Quote Calculator] → [Premium Calculator Service]
[Claim Processor] → [Payment Integration]
[RabbitMQ Publisher] → [асинхронные события]
```

**API эндпоинты:**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /quotes | Создание запроса на расчет страховки |
| GET | /quotes | Список запросов пользователя |
| GET | /quotes/{id} | Детали запроса |
| POST | /policies | Оформление полиса |
| GET | /policies | Список полисов пользователя |
| GET | /policies/{id} | Детали полиса |
| POST | /claims | Подача страхового случая |
| GET | /claims | Список страховых случаев |

**Пример API вызова:**
```bash
curl -X POST "http://localhost:8000/insurance/quotes" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "insurance_type": "kasko",
    "coverage_amount": 2000000.00,
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_year": 2023,
    "vehicle_vin": "1HGCM82633A123456"
  }'
```

### 3.6 Sales Service

**Назначение:** Сервис управления заказами на продажу автомобилей.

**Ответственность:**
1. Создание и управление заказами на покупку автомобилей
2. Управление жизненным циклом заказа (черновик, подтвержден, выдан)
3. Привязка заказов к клиентам, автомобилям и условиям оплаты
4. Интеграция с платежами и резервированиями

**Модель данных:**
```sql
SaleOrder:
- id: integer (PK)
- customer_id: integer (FK)
- vehicle_id: integer (FK)
- status: enum (draft, confirmed, paid, completed, cancelled)
- total_price: decimal
- created_at: datetime
- updated_at: datetime
```

### 3.7 Pricing Discount Service

**Назначение:** Сервис расчета цен и управления скидками.

**Ответственность:**
1. Расчет финальной цены по заказу
2. Управление правилами скидок, акциями и промокодами
3. Применение скидок к заказам
4. Валидация промокодов

**Модель данных:**
```sql
Discount:
- id: integer (PK)
- code: string (unique)
- type: enum (percentage, fixed)
- value: decimal
- valid_from: datetime
- valid_to: datetime
- usage_limit: integer
```

### 3.8 Customer Service

**Назначение:** Сервис управления клиентской базой.

**Ответственность:**
1. CRUD операции с данными клиентов
2. Управление контактами клиентов
3. История взаимодействий с клиентами
4. Сегментация клиентов
5. Интеграция с другими сервисами

**Модель данных:**
```sql
Customer:
- id: integer (PK)
- user_id: integer (FK)
- full_name: string
- email: string
- phone: string
- address: text
- created_at: datetime

CustomerInteraction:
- id: integer (PK)
- customer_id: integer (FK)
- type: enum (call, email, visit)
- description: text
- created_at: datetime
```

### 3.9 Vehicle Catalog Service

**Назначение:** Сервис управления каталогом автомобилей.

**Ответственность:**
1. Управление моделями и комплектациями автомобилей
2. Хранение характеристик и цен автомобилей
3. Поиск и фильтрация автомобилей по различным критериям
4. Управление ценами на модели

**Модель данных:**
```sql
VehicleModel:
- id: integer (PK)
- brand: string
- model: string
- year: integer
- base_price: decimal
- specifications: jsonb

VehicleModification:
- id: integer (PK)
- model_id: integer (FK)
- name: string
- price: decimal
- features: jsonb
```

### 3.10 Inventory Service

**Назначение:** Сервис учета автомобилей на складе.

**Ответственность:**
1. Учет конкретных экземпляров автомобилей (VIN)
2. Резервирование автомобилей под заказы
3. Отслеживание локаций и состояний автомобилей
4. Управление статусами автомобилей

**Модель данных:**
```sql
Vehicle:
- id: integer (PK)
- vin: string (unique)
- model_id: integer (FK)
- modification_id: integer (FK)
- color: string
- mileage: integer
- condition: enum (new, used)
- location: string
- status: enum (available, reserved, sold)
```

### 3.11 Service Booking Service

**Назначение:** Сервис записи на сервисное обслуживание.

**Ответственность:**
1. Управление записями на техническое обслуживание и ремонт
2. Расписание мастеров и управление слотами времени
3. Привязка записей к автомобилям и клиентам
4. Управление статусами обслуживания

**Модель данных:**
```sql
ServiceBooking:
- id: integer (PK)
- customer_id: integer (FK)
- vehicle_id: integer (FK)
- service_type: enum (maintenance, repair)
- scheduled_date: datetime
- mechanic_id: integer
- status: enum (scheduled, in_progress, completed, cancelled)
```

### 3.12 Notification Service

**Назначение:** Сервис отправки уведомлений.

**Ответственность:**
1. Получение событий из других сервисов
2. Формирование и отправка уведомлений (email/SMS)
3. Логирование отправленных уведомлений
4. Управление шаблонами уведомлений

**Модель данных:**
```sql
Notification:
- id: integer (PK)
- user_id: integer (FK)
- type: enum (email, sms, push)
- subject: string
- message: text
- status: enum (pending, sent, failed)
- sent_at: datetime
```

### 3.13 Reporting Analytics Service

**Назначение:** Сервис аналитики и отчетности.

**Ответственность:**
1. Агрегация данных по продажам и доходам
2. Формирование финансовых и операционных отчетов
3. Анализ эффективности акций и скидок
4. Статистика по различным показателям

**Модель данных:**
```sql
SalesReport:
- id: integer (PK)
- period_start: date
- period_end: date
- total_sales: integer
- total_revenue: decimal
- created_at: datetime
```

### 3.14 Logging Monitoring Service

**Назначение:** Сервис централизованного логирования и мониторинга.

**Ответственность:**
1. Сбор и агрегация логов из всех микросервисов
2. Централизованное хранение технической информации
3. Предоставление интерфейса для поиска и анализа логов
4. Мониторинг производительности системы

**Модель данных:**
```sql
LogEntry:
- id: integer (PK)
- service_name: string
- level: enum (debug, info, warning, error)
- message: text
- timestamp: datetime
- trace_id: string
```

### 3.15 Admin Config Service

**Назначение:** Сервис управления конфигурацией системы.

**Ответственность:**
1. Управление настройками автосалона
2. Конфигурация филиалов и продавцов
3. Управление тарифами и ролями
4. Системные параметры и конфигурации

**Модель данных:**
```sql
SystemConfig:
- id: integer (PK)
- key: string (unique)
- value: text
- category: string
- updated_at: datetime
```

## Архитектура одного микросервиса

### Гексагональная архитектура (Hexagonal Architecture)

В качестве примера рассмотрим архитектуру **Sales Service** - одного из ключевых микросервисов системы.

#### Основные принципы гексагональной архитектуры:

Гексагональная архитектура (порты и адаптеры) позволяет создавать слабо связанные компоненты, где бизнес-логика не зависит от внешних систем.

#### Структура Sales Service:

**Domain (Домен):**
- **Сущности:** Order, OrderItem, OrderStatus
- **Use cases / Application services:** CreateOrder, ConfirmOrder, CancelOrder, GetOrderDetails
- **Бизнес-правила:** Валидация заказов, расчет стоимости, проверка доступности

**Inbound Adapters (Входящие адаптеры):**
- **REST Controller** (/orders) - обработка HTTP запросов
- **gRPC Endpoint** (опционально) - для межсервисного взаимодействия
- **Event Consumer** - обработка событий из RabbitMQ

**Outbound Adapters (Исходящие адаптеры):**
- **Order Repository** - работа с базой данных PostgreSQL
- **Pricing Client** - вызов Pricing Discount Service
- **Inventory Client** - вызов Inventory Service
- **Payment Client** - вызов Payment Service
- **Event Publisher** - публикация событий в RabbitMQ

```
[REST API] → [HTTP Controller] → [Application Services] → [Domain Entities]
[gRPC API] → [gRPC Controller] → [Application Services] → [Domain Entities]
[Event Bus] → [Event Handler] → [Application Services] → [Domain Entities]

[Application Services] → [Repository] → [PostgreSQL Database]
[Application Services] → [Pricing Client] → [Pricing Service]
[Application Services] → [Inventory Client] → [Inventory Service]
[Application Services] → [Payment Client] → [Payment Service]
[Application Services] → [Event Publisher] → [RabbitMQ]
```

**Преимущества данной архитектуры:**
1. **Изоляция бизнес-логики** - домен не зависит от внешних систем
2. **Тестируемость** - легкая замена адаптеров на mocks
3. **Гибкость** - возможность изменения внешних интерфейсов без изменения домена
4. **Масштабируемость** - независимое развитие компонентов

## 4. API

### 4.1 Сводка по API

| Категория | Количество | Описание |
|-----------|------------|----------|
| REST endpoints | ~25 | Внешние API через API Gateway |
| Internal REST | ~30 | Внутренние вызовы между сервисами |
| RabbitMQ topics | 8 | Асинхронные события (запланированы) |
| Swagger UI | 5 | Автоматическая документация для каждого сервиса |

### 4.2 Внешний REST API

**Auth Service (9 endpoints):**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /auth/register | Регистрация пользователя |
| POST | /auth/login | Аутентификация |
| POST | /auth/logout | Выход из системы |
| POST | /auth/refresh | Обновление токенов |
| GET | /auth/me | Данные текущего пользователя |
| GET | /auth/users/{id} | Данные пользователя по ID |
| GET | /auth/users | Список пользователей |
| PATCH | /auth/users | Обновление профиля |
| DELETE | /auth/users/{id} | Удаление пользователя |

**Пример: POST /auth/register**
```json
Request:
{
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "phone": "+79001234567",
  "role": "client"
}

Response (201 Created):
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "role": "client",
  "created_at": "2025-01-22T10:00:00Z"
}
```

**Sales Service (8 endpoints):**
| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | /sales/orders | Создание заказа |
| GET | /sales/orders | Список заказов |
| GET | /sales/orders/{id} | Получение заказа |
| PUT | /sales/orders/{id} | Обновление заказа |
| DELETE | /sales/orders/{id} | Удаление заказа |
| POST | /sales/orders/{id}/confirm | Подтверждение заказа |
| POST | /sales/orders/{id}/cancel | Отмена заказа |

### 4.3 gRPC API

**Proto-файл: payment.proto**
```protobuf
syntax = "proto3";
package payment;

service PaymentGateway {
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse);
  rpc CheckPaymentStatus (StatusRequest) returns (StatusResponse);
}

message PaymentRequest {
  int32 order_id = 1;
  double amount = 2;
  string currency = 3;
  string payment_method = 4;
}

message PaymentResponse {
  enum Status {
    PENDING = 0;
    SUCCESS = 1;
    FAILED = 2;
  }
  Status status = 1;
  string transaction_id = 2;
  string message = 3;
}
```

### 4.4 Асинхронный API — RabbitMQ Topics

**Exchange: autosalon_events (type: TOPIC, durable: true)**

| Routing Key | Publisher | Subscribers | Payload |
|-------------|-----------|-------------|---------|
| sales.order.created | Sales Service | Notification, Analytics | order_id, customer_id, vehicle_id, total_price |
| sales.order.paid | Sales Service | Notification, Analytics | order_id, payment_id |
| sales.order.cancelled | Sales Service | Notification, Analytics, Inventory | order_id, reason |
| payment.succeeded | Payment Service | Sales, Notification | payment_id, order_id, amount |
| payment.failed | Payment Service | Sales, Notification | payment_id, order_id, reason |
| financing.application.created | Financing | Notification, Analytics | application_id, customer_id, loan_amount |
| insurance.policy.issued | Insurance | Notification, Analytics | policy_id, customer_id, premium_amount |
| service.booking.created | Service Booking | Notification | booking_id, customer_id, scheduled_date |
| inventory.vehicle.reserved | Inventory | Sales, Notification | vehicle_id, order_id |
| inventory.vehicle.sold | Inventory | Analytics | vehicle_id, sale_price |
| notification.sent | Notification | Analytics | notification_id, type, user_id |
| system.error | All Services | Logging, Monitoring | service_name, error_message, trace_id |

**Пример события: sales.order.created**
```json
{
  "event_id": "evt_123456789",
  "event_type": "OrderCreated",
  "timestamp": "2025-01-22T10:30:00Z",
  "payload": {
    "order_id": 42,
    "customer_id": 1,
    "vehicle_id": 15,
    "total_price": 2500000.00
  }
}
```

## 5. Паттерны проектирования

### 5.1 API Gateway

**Реализация:** Собственная реализация на FastAPI

**Описание:** Единая точка входа для всех клиентских запросов. Обеспечивает:
- Аутентификацию через проверку JWT токенов
- Маршрутизацию запросов к микросервисам
- Агрегацию данных из нескольких сервисов (эндпоинт / для статистики)
- Rate limiting для защиты от DDoS
- Логирование всех запросов

**Преимущества:**
1. Централизованная аутентификация
2. Упрощение клиентских приложений
3. Возможность кеширования ответов
4. Единая точка мониторинга

### 5.2 Database per Service

**Описание:** Каждый микросервис имеет собственную изолированную базу данных PostgreSQL.

**Преимущества:**
1. **Независимое масштабирование:** Каждый сервис может масштабироваться отдельно
2. **Изоляция данных:** Проблемы в одном сервисе не влияют на данные других
3. **Технологическая свобода:** Возможность выбора оптимальной СУБД для каждого сервиса
4. **Упрощение развертывания:** Независимые миграции и обновления

**Недостатки и решения:**
1. **Сложность транзакций:** Решение через паттерн Saga
2. **Дублирование данных:** Решение через CQRS и событийную модель

### 5.3 Saga (Choreography)

**Реализация:** Хореография через RabbitMQ с Topic Exchange

**Описание:** Распределенные транзакции через оркестрацию событий. Каждый сервис подписывается на нужные события и публикует результат своей работы.

**Сценарий "Покупка автомобиля":**
1. Sales Service создает заказ → публикует OrderCreated
2. Inventory Service резервирует автомобиль → публикует VehicleReserved
3. Payment Service обрабатывает платеж → публикует PaymentSucceeded
4. Sales Service завершает заказ → публикует OrderCompleted

**Компенсирующие транзакции:**
1. PaymentFailed → Sales Service отменяет заказ, Inventory Service снимает резерв
2. InventoryReservationFailed → Sales Service отменяет заказ

### 5.4 Event Sourcing

**Реализация:** Order Service с таблицей order_events

**Описание:** Состояние заказа восстанавливается из последовательности событий.

**Пример Aggregate:**
```python
class OrderAggregate:
    def __init__(self):
        self.id = None
        self.status = "created"
        self.exists = False

    def apply_event(self, event_data):
        e_type = event_data.get("event_type")
        if e_type == "OrderCreated":
            self.status = "created"
            self.exists = True
        elif e_type == "OrderPaid":
            self.status = "paid"
        elif e_type == "OrderCancelled":
            self.status = "cancelled"
        elif e_type == "OrderCompleted":
            self.status = "completed"
```

**Преимущества:**
1. Полная история изменений
2. Возможность восстановления состояния на любой момент
3. Аудит всех операций
4. Поддержка аналитики и отчетности

### 5.5 Circuit Breaker

**Реализация:** aiobreaker в Payment Service

**Описание:** Защита от каскадных сбоев при недоступности внешних платежных систем.

**Пример реализации:**
```python
from aiobreaker import CircuitBreaker

circuit_breaker = CircuitBreaker(fail_max=3, name="payment_gateway_breaker")

class PaymentGatewayClient:
    @circuit_breaker
    async def process_payment(self, payment_data):
        # Вызов внешнего API платежной системы
        return await self._call_payment_api(payment_data)

    async def fallback_process_payment(self, payment_data):
        # Резервная логика при недоступности платежной системы
        return {"status": "pending", "message": "Payment queued for processing"}
```

### 5.6 CQRS (Command Query Responsibility Segregation)

**Реализация:** Reporting Analytics Service

**Описание:** Разделение ответственности за команды (изменение данных) и запросы (чтение данных).

**Применение в системе:**
- **Command side:** Sales Service, Payment Service, Inventory Service изменяют данные
- **Query side:** Reporting Analytics Service предоставляет агрегированные данные для отчетов

**Преимущества:**
1. Оптимизация производительности чтения
2. Масштабируемость запросов
3. Гибкость в представлении данных
4. Упрощение аналитики

### 5.7 Service Discovery

**Реализация:** HashiCorp Consul (запланировано)

**Описание:** Динамическая регистрация и обнаружение микросервисов.

**Функциональность:**
1. Регистрация сервисов при запуске
2. Health checks для мониторинга доступности
3. DNS-based service discovery
4. Load balancing между инстансами

**Пример регистрации:**
```python
def register_service(service_name, service_port):
    data = {
        "Name": service_name,
        "ID": f"{service_name}-{instance_id}",
        "Address": container_ip,
        "Port": service_port,
        "Check": {
            "HTTP": f"http://{container_ip}:{service_port}/health",
            "Interval": "10s"
        }
    }
    consul_client.agent.service.register(**data)
```

### 5.8 API Composition

**Реализация:** API Gateway для агрегации данных

**Описание:** Сбор данных из нескольких микросервисов в одном запросе для упрощения клиентских приложений.

**Пример:** Эндпоинт `/` в API Gateway агрегирует статистику из всех сервисов:
```python
@app.get("/")
async def get_overall_stats():
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth_stats = await client.get(f"{AUTH_SERVICE_URL}/stats")
        payment_stats = await client.get(f"{PAYMENT_SERVICE_URL}/stats")
        financing_stats = await client.get(f"{FINANCING_SERVICE_URL}/stats")
        insurance_stats = await client.get(f"{INSURANCE_SERVICE_URL}/stats")

        return {
            "message": "API Gateway is running",
            "version": "1.0.0",
            "services": {
                "auth": auth_stats.json() if auth_stats.status_code == 200 else {"error": "Auth Service unavailable"},
                "payment": payment_stats.json() if payment_stats.status_code == 200 else {"error": "Payment Service unavailable"},
                "financing": financing_stats.json() if financing_stats.status_code == 200 else {"error": "Financing Service unavailable"},
                "insurance": insurance_stats.json() if insurance_stats.status_code == 200 else {"error": "Insurance Service unavailable"},
            }
        }
```

**Преимущества:**
1. Сокращение количества запросов от клиента
2. Упрощение клиентских приложений
3. Централизованная агрегация данных
4. Единая точка для комплексных запросов

## 6. Заключение

**Основные результаты:**

В ходе выполнения курсовой работы была спроектирована и реализована микросервисная архитектура информационной системы «Автосалон».

1. **Декомпозиция системы:** Выделено 15 микросервисов с четким разделением ответственности согласно принципам Domain-Driven Design (DDD).

2. **Гибридное взаимодействие:** Реализованы синхронные (REST API, gRPC) и асинхронные (RabbitMQ) способы коммуникации между сервисами.

3. **Отказоустойчивость:** Применены паттерны Circuit Breaker, Saga с компенсирующими транзакциями, Database per Service.

4. **Масштабируемость:** Архитектура позволяет горизонтально масштабировать каждый сервис независимо. Реализована балансировка нагрузки через API Gateway.

5. **Наблюдаемость:** Интегрированы системы логирования и мониторинга.

6. **API Gateway:** Единая точка входа с аутентификацией, маршрутизацией и агрегацией данных.

7. **Тестирование:** Реализованы интеграционные тесты для проверки взаимодействия микросервисов.

8. **Безопасность:** Реализована JWT-аутентификация и ролевая модель доступа.

**Перспективы развития:**

• Добавление Redis для кэширования горячих данных
• Реализация полнотекстового поиска (Elasticsearch)
• Внедрение Kubernetes для production-развертывания
• Добавление WebSocket для real-time уведомлений
• Реализация Service Mesh (Istio) для улучшения наблюдаемости
• Добавление системы трассировки (Jaeger)
• Внедрение API rate limiting на уровне сервисов
• Реализация blue-green deployments для бесшовных обновлений
• Добавление системы A/B тестирования
• Интеграция с внешними системами (1C, SAP)

## 7. Список литературы

1. Ричардсон К. Микросервисы. Паттерны разработки и рефакторинга. — СПб.: Питер, 2021. — 544 с.
2. Ньюман С. Создание микросервисов. — СПб.: Питер, 2019. — 448 с.
3. Эванс Э. Предметно-ориентированное проектирование (DDD): структуризация сложных программных систем. — М.: Вильямс, 2011. — 448 с.
4. Клепманн М. Высоконагруженные приложения. Программирование, масштабирование, поддержка. — СПб.: Питер, 2019. — 640 с.
5. Браун С. Модель C4 для визуализации архитектуры программного обеспечения // [Электронный ресурс]. URL: https://c4model.com/ (дата обращения: 22.01.2025).
6. Документация FastAPI // [Электронный ресурс]. URL: https://fastapi.tiangolo.com/ (дата обращения: 22.01.2025).
7. Документация RabbitMQ // [Электронный ресурс]. URL: https://www.rabbitmq.com/documentation.html (дата обращения: 22.01.2025).
8. Документация Docker // [Электронный ресурс]. URL: https://docs.docker.com/ (дата обращения: 22.01.2025).
9. Документация PostgreSQL // [Электронный ресурс]. URL: https://www.postgresql.org/docs/ (дата обращения: 22.01.2025).
10. Документация JWT // [Электронный ресурс]. URL: https://jwt.io/ (дата обращения: 22.01.2025).