# Gym Management Telegram Bot

A Telegram bot to manage gym members, payments, and expiration dates efficiently.

---

## Overview

This Telegram bot allows you to manage gym members, track payments, and monitor expiration dates without the need for complex systems.

---

## Features

- Member management (add, search, delete)
- Bulk member registration
- Bulk delete functionality
- Payment tracking
- Automatic expiration date calculation
- Overdue member detection
- Excel report generation
- Automatic backups
- Admin-only access control

---

## Commands

/start - Start the bot  
/add - Add a new member  
/list - Show all members  
/delete - Remove a member  
/report - Generate Excel report  
/overdue - Show overdue members  

---

## Project Structure

gym_bot_project/
├── bot.py  
├── requirements.txt  
├── .env  
├── .gitignore  
├── data/  
│   └── miembros.json  
├── backup/  
├── logs/  
├── reports/  
└── README.md  

---

## Setup

### 1. Clone the repository

git clone https://github.com/cesarpalaciodev/gym-bot-project.git  
cd gym-bot-project  

---

### 2. Create virtual environment

python -m venv venv  

#### Activate environment:

Windows  
venv\Scripts\activate  

Mac / Linux  
source venv/bin/activate  

---

### 3. Install dependencies

pip install -r requirements.txt  

---

### 4. Environment variables

Create a .env file:

TOKEN=your_telegram_bot_token  
ADMIN_ID=your_telegram_id  

---

## Run

python bot.py  

---

## Security

- Uses environment variables for sensitive data  
- .env is excluded from version control  
- Admin-restricted commands  

---

## Modules

- Members → manage users  
- Payments → track payments  
- Reports → Excel + overdue users  
- Backup → automatic backups  

---

## Deployment

Ready to deploy on:

- Render  
- Railway  
- VPS  

---

## Roadmap

- [ ] Payment history  
- [ ] Automatic reminders  
- [ ] Database integration (PostgreSQL)  
- [ ] Web dashboard  

---

## License

MIT  

---

## Author

Cesar Palacio  

---

⭐ If you find this project useful, consider giving it a star!
