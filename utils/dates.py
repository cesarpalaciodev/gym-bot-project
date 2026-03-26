# ==================================================
# UTILIDADES DE FECHAS
# ==================================================

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar

from config import GRACE_DAYS, LATE_DAYS


def calcular_proximo_vencimiento(fecha_pago: date) -> date:
    dia_pago = fecha_pago.day
    proximo = fecha_pago + relativedelta(months=1)
    
    ultimo_dia = calendar.monthrange(proximo.year, proximo.month)[1]
    dia_real = min(dia_pago, ultimo_dia)
    
    return proximo.replace(day=dia_real)


def calcular_dias_vencido(fecha_vencimiento: date) -> int:
    hoy = date.today()
    
    dia_pago = fecha_vencimiento.day
    
    if hoy.day < dia_pago:
        return 0
    
    return (hoy - fecha_vencimiento).days


def es_gracia(fecha_vencimiento: date) -> bool:
    dias = calcular_dias_vencido(fecha_vencimiento)
    return 0 < dias <= GRACE_DAYS


def es_tardio(fecha_vencimiento: date) -> bool:
    return calcular_dias_vencido(fecha_vencimiento) > GRACE_DAYS


def obtener_siguiente_fecha_pago(fecha_pago: date, es_tardio: bool) -> date:
    if es_tardio:
        return date.today()
    return fecha_pago


def get_ultimo_dia_mes(fecha: date) -> date:
    ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
    return fecha.replace(day=ultimo_dia)


def format_fecha(fecha: date) -> str:
    return fecha.strftime("%Y-%m-%d")


def parse_fecha(fecha_str: str) -> date | None:
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def calcular_vencimiento_con_gracia(fecha_pago: date, dias_vencido: int) -> tuple[date, bool]:
    nuevo_vencimiento = calcular_proximo_vencimiento(fecha_pago)
    grace_period = dias_vencido <= GRACE_DAYS
    if grace_period:
        return nuevo_vencimiento, True
    
    dia_pago = date.today().day
    nuevo = date.today() + relativedelta(months=1)
    ultimo_dia = calendar.monthrange(nuevo.year, nuevo.month)[1]
    dia_real = min(dia_pago, ultimo_dia)
    
    return nuevo.replace(day=dia_real), False
