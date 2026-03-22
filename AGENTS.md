# AGENTS.md - Bot de Gimnasio para Telegram

## Descripción del Proyecto

Bot de Telegram en Python para gestionar miembros de gimnasio, pagos y fechas de vencimiento con MongoDB.

## Comandos de Ejecución

### Instalación
```bash
pip install -r requirements.txt
```

### Ejecutar
```bash
python bot.py
```

### Configuración del Entorno (.env)
```
TOKEN=tu_token_del_bot_telegram
ADMIN_ID=tu_id_de_telegram
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/gym
```

## Pruebas

```bash
pytest
pytest tests/test_archivo.py::test_nombre_funcion
pytest --cov=. --cov-report=term-missing
```

## Convenciones de Código

### Type Hints (Obligatorias)
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
```

### Imports
stdlib → third-party → local

### Convenciones de Nombres
- Funciones: `snake_case`
- Clases: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`

### Async/Await
Usar `async def` para todos los handlers de Telegram.

### Manejo de Errores
Usar try/except con logging y mensajes de error claros para el usuario.

### Logging
Usar `logging` module. Niveles: DEBUG, INFO, WARNING, ERROR.

## Arquitectura del Proyecto

```
gym_bot_project/
├── bot.py              # Entry point
├── config.py           # Configuración
├── database/
│   └── __init__.py     # Conexión MongoDB
├── models/
│   ├── member.py       # Modelo Member
│   ├── payment.py      # Modelo Payment
│   └── admin.py        # Modelo Admin
├── handlers/
│   ├── start.py        # /start, /help
│   ├── members.py      # Gestión de miembros
│   ├── payments.py     # Pagos y planes
│   ├── reports.py      # Reportes
│   ├── stats.py        # Estadísticas
│   ├── notifications.py # Notificaciones 5 AM
│   ├── admins.py       # Gestión multi-admin
│   ├── export.py       # Exportar datos
│   └── button_handler.py
├── keyboards.py        # Menús
├── utils/
│   └── dates.py        # Lógica de fechas
├── requirements.txt
└── render.yaml         # Deploy en Render
```

## Lógica de Pagos

```
Vencimiento = fecha_pago + 1 mes (mismo día)

1-4 días después del vencimiento:
  → GRACIA → Mantiene fecha original

5+ días después del vencimiento:
  → TARDÍO → Nueva fecha = día de pago
```

## Roles de Admin

| Rol | Permisos |
|-----|----------|
| super_admin | Todo + gestión de admins |
| admin | Miembros, pagos, reportes, estadísticas |
| viewer | Solo lectura |

## Planes de Membresía

| Plan | Precio |
|------|--------|
| Mensual | $500 |
| Trimestral | $1,350 |
| Semestral | $2,500 |
| Anual | $4,500 |

## Dependencias

- python-telegram-bot==20.7
- pymongo==4.6.0
- openpyxl
- python-dateutil
- python-dotenv
- httpx==0.24.1

## Despliegue en Render

1. Crear cuenta en MongoDB Atlas
2. Obtener connection string (MONGO_URI)
3. Conectar Render con GitHub
4. Configurar variables de entorno en Render
5. Deploy automático

## Git Workflow

- Ramas: `feature/descripcion` o `fix/descripcion`
- Commits: `feat: agregar funcionalidad` o `fix: resolver problema`
- No commitear: `.env`, `data/`, `backup/`, `logs/`
