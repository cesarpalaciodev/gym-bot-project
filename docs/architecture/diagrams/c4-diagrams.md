# C4 Architecture Diagrams - GymBot

## Level 1: System Context Diagram

```mermaid
graph TB
    User[Admin User<br/>Telegram] -->|Commands| Bot[Telegram Bot<br/>GymBot]
    User -->|View Data| Dashboard[Web Dashboard<br/>FastAPI]
    
    Bot -->|Read/Write| MongoDB[(MongoDB<br/>Members, Payments)]
    Dashboard -->|Read| MongoDB
    
    Bot -->|Send Notifications| TelegramAPI[Telegram API]
    TelegramAPI -->|Messages| User
    
    Bot -.->|Errors| Sentry[Sentry<br/>Monitoring]
    Dashboard -.->|Errors| Sentry
    
    Bot -.->|Rate Limiting| Redis[(Redis<br/>Optional)]
```

## Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Infrastructure"
        Docker[Docker Compose]
        Nginx[Nginx<br/>Reverse Proxy]
    end
    
    subgraph "GymBot Application"
        Bot[Telegram Bot<br/>Python + python-telegram-bot]
        Dashboard[Web Dashboard<br/>FastAPI + Jinja2]
        Scheduler[Job Scheduler<br/>5 AM Notifications]
    end
    
    subgraph "Data"
        MongoDB[(MongoDB<br/>Motor Async)]
        Redis[(Redis<br/>Rate Limiting)]
    end
    
    User[Admin] -->|Bot Father| Telegram[Telegram API]
    Telegram -->|Webhooks/Polling| Bot
    User -->|HTTPS| Nginx
    Nginx -->|/| Dashboard
    
    Bot -->|TCP| MongoDB
    Dashboard -->|TCP| MongoDB
    Scheduler -->|TCP| MongoDB
    
    Bot -.->|TCP| Redis
    Dashboard -.->|TCP| Redis
```

## Level 3: Component Diagram (Dashboard)

```mermaid
graph TB
    subgraph "FastAPI Dashboard"
        Router[Router/API Layer<br/>HTTP Endpoints]
        Auth[Auth Component<br/>Sessions + CSRF]
        Services[Services Layer<br/>Business Logic]
        Templates[Templates<br/>Jinja2 HTML]
        Static[Static Files<br/>CSS/JS]
    end
    
    subgraph "Security"
        Middleware[Security Middleware<br/>Headers + Rate Limit]
        SessionStore[(Session Store<br/>MongoDB)]
    end
    
    Client[Browser] -->|HTTP| Middleware
    Middleware --> Router
    Router --> Auth
    Auth --> SessionStore
    Router --> Services
    Services --> MongoDB[(MongoDB)]
    Router --> Templates
    Router --> Static
```

## Level 3: Component Diagram (Bot)

```mermaid
graph TB
    subgraph "Telegram Bot"
        Handlers[Handlers Layer<br/>Command Handlers]
        Services[Services Layer<br/>CRUD Operations]
        Auth[Auth Component<br/>RBAC + Rate Limit]
        Jobs[Background Jobs<br/>APScheduler]
    end
    
    Telegram[Telegram API] -->|Updates| Handlers
    Handlers --> Auth
    Auth --> Services
    Services --> MongoDB[(MongoDB)]
    
    Jobs -->|5 AM| Services
    Jobs -.->|Notifications| Telegram
```

## Data Flow Diagram - Payment Registration

```mermaid
sequenceDiagram
    actor Admin
    participant Bot as Telegram Bot
    participant PaymentSvc as PaymentService
    participant MemberSvc as MemberService
    participant DB as MongoDB
    
    Admin->>Bot: /register_payment John Monthly
    Bot->>PaymentSvc: register_payment()
    PaymentSvc->>MemberSvc: find_member("John")
    MemberSvc->>DB: find_one({name: "John"})
    DB-->>MemberSvc: member doc
    MemberSvc-->>PaymentSvc: member data
    PaymentSvc->>DB: insert_one(payment)
    DB-->>PaymentSvc: success
    PaymentSvc-->>Bot: payment confirmation
    Bot-->>Admin: Payment registered!
```

## Data Flow - Dashboard Authentication

```mermaid
sequenceDiagram
    actor Admin
    participant Dashboard as FastAPI Dashboard
    participant Auth as Auth Service
    participant DB as MongoDB Sessions
    
    Admin->>Dashboard: GET /login
    Dashboard-->>Admin: Login form
    Admin->>Dashboard: POST /login (chat_id)
    Dashboard->>Auth: _verify_admin(chat_id)
    Auth->>DB: find_one({telegram_id})
    DB-->>Auth: admin data
    Auth-->>Dashboard: admin valid
    Dashboard->>Auth: create_session(chat_id)
    Auth->>DB: insert_one(session)
    DB-->>Auth: session stored
    Auth-->>Dashboard: token
    Dashboard-->>Admin: Set-Cookie + Redirect /
    Admin->>Dashboard: GET / (with cookie)
    Dashboard->>Auth: get_current_admin(request)
    Auth->>DB: find session
    DB-->>Auth: session valid
    Auth-->>Dashboard: admin data
    Dashboard-->>Admin: Dashboard HTML
```

## Legend

- **Solid line**: Synchronous/HTTP communication
- **Dotted line**: Asynchronous/Background communication
- **Cylinder**: Database/Storage
- **Rectangle**: Component/Service
- **Actor**: External user
