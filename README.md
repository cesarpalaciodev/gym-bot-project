# Gym Management Telegram Bot

A Telegram bot to manage gym members, payments, and expiration dates with MongoDB.

---

## Features

- Member management (add, search, delete, bulk)
- Payment tracking with grace period (1-4 days)
- Membership plans (Monthly, Quarterly, Semi-annual, Annual)
- Payment history
- Overdue member detection
- Statistics dashboard (active members, income, expirations)
- Excel/CSV/PDF export
- Multi-admin support with roles
- Automatic daily notifications at 5 AM
- MongoDB Atlas database
- Deploy ready for Render

---

## Commands

/start - Start the bot
/help - Show all commands
/backup - Create manual backup

### Member Menu
- ➕ Agregar miembro - Add single member
- 👥 Agregar varios - Bulk add
- 🔍 Buscar miembro - Search member
- 📋 Lista miembros - List all
- 🗑 Eliminar miembro - Delete one
- 🗑 Eliminar varios - Bulk delete

### Payment Menu
- 💰 Registrar pago - Register payment
- 📜 Historial - View history

### Reports Menu
- ⚠️ Deudores - Show overdue
- 📊 Excel - Generate Excel report

### Statistics Menu
- 👥 Miembros activos - Active members
- 💰 Ingresos del mes - Monthly income
- 📅 Vencimientos - Expirations

### Export Menu
- 📊 Excel miembros - Export members
- 📊 Excel pagos - Export payments
- 📄 PDF resumen - Summary report

### Admin Menu (Super Admin only)
- ➕ Agregar admin - Add admin
- 👥 Lista admins - List admins
- 🗑 Quitar admin - Remove admin
- 🔄 Cambiar rol - Change role

---

## Setup

### 1. Clone repository
```bash
git clone https://github.com/cesarpalaciodev/gym-bot-project.git
cd gym-bot-project
```

### 2. Create virtual environment
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment variables
Create `.env` file:
```
TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/gym
```

### 5. MongoDB Atlas
1. Create free account at mongodb.com
2. Create cluster (M0 Sandbox - free)
3. Create database "gym"
4. Create user with read/write permissions
5. Get connection string

---

## Run

```bash
python bot.py
```

---

## Deploy on Render

1. Push code to GitHub
2. Create Web Service on Render
3. Connect GitHub repository
4. Configure environment variables:
   - `TOKEN`
   - `ADMIN_ID`
   - `MONGO_URI`
5. Deploy automatically

---

## Payment Logic

```
PAYMENT: 20th of any month
DUE DATE: 20th of next month

If pays 1-4 days late (20-24):
  → GRACE PERIOD → Keep original date

If pays 5+ days late (25+):
  → LATE PAYMENT → New date = payment day
```

---

## Membership Plans

| Plan | Price | Duration |
|------|-------|----------|
| Monthly | $500 | 1 month |
| Quarterly | $1,350 | 3 months |
| Semi-annual | $2,500 | 6 months |
| Annual | $4,500 | 12 months |

---

## Admin Roles

| Role | Permissions |
|------|-------------|
| super_admin | Full access + admin management |
| admin | Members, payments, reports, stats |
| viewer | Read-only access |

---

## Project Structure

```
gym_bot_project/
├── bot.py              # Entry point
├── config.py           # Configuration
├── database/           # MongoDB connection
├── models/             # Data models
├── handlers/           # Telegram handlers
├── keyboards.py        # Keyboard menus
├── utils/             # Utilities
├── requirements.txt    # Dependencies
└── render.yaml         # Deploy config
```

---

## License

MIT - Cesar Palacio
