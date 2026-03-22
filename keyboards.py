from telegram import ReplyKeyboardMarkup

menu_principal = ReplyKeyboardMarkup(
    [
        ["👥 Miembros", "💰 Pagos"],
        ["📊 Reportes", "📈 Estadísticas"],
        ["💾 Exportar", "⚙️ Admin"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_miembros = ReplyKeyboardMarkup(
    [
        ["➕ Agregar miembro", "👥 Agregar varios"],
        ["🔍 Buscar miembro", "📋 Lista miembros"],
        ["🗑 Eliminar miembro", "🗑 Eliminar varios"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_pagos = ReplyKeyboardMarkup(
    [
        ["💰 Registrar pago"],
        ["📜 Historial"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_reportes = ReplyKeyboardMarkup(
    [
        ["⚠️ Deudores", "📊 Excel"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_estadisticas = ReplyKeyboardMarkup(
    [
        ["👥 Miembros activos"],
        ["💰 Ingresos del mes"],
        ["📅 Vencimientos"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_exportar = ReplyKeyboardMarkup(
    [
        ["📊 Excel miembros"],
        ["📊 Excel pagos"],
        ["📄 PDF resumen"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_admin = ReplyKeyboardMarkup(
    [
        ["➕ Agregar admin"],
        ["👥 Lista admins"],
        ["🗑 Quitar admin"],
        ["🔄 Cambiar rol"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)

menu_planes = ReplyKeyboardMarkup(
    [
        ["1. Mensual ($70,000)"],
        ["⬅️ Cancelar"],
    ],
    resize_keyboard=True,
)

menu_confirmar = ReplyKeyboardMarkup(
    [
        ["✅ Confirmar"],
        ["❌ Cancelar"],
    ],
    resize_keyboard=True,
)

menu_principal_admin = ReplyKeyboardMarkup(
    [
        ["👥 Miembros", "💰 Pagos"],
        ["📊 Reportes", "📈 Estadísticas"],
        ["💾 Exportar"],
        ["⬅️ Volver"],
    ],
    resize_keyboard=True,
)
