from collections import namedtuple

SERVICE_LINKS = {
    'Atrás',
    'Desconectar',
    'Transferencias',
    'Más saldo a la cuenta',
    'Programa Estrella',
    'Divisas y moneda extranjera',
    'Ver titulares',
    'Saldo y detalle de cuenta',
    'Añadir a favoritos',
    'Crear/Modificar alias cuenta',
    'Recibos',
    'Recibo único',
    'Instalar ReciBox para iPhone y Android',
    'Desconectar',
    '>> Ver más movimientos',
    ''
}

CompanyUrlData = namedtuple('CompanyUrlData', ['init_url', 'company_title_in_list'])
MovementUrlData = namedtuple('MovementUrlData',
                             ['date', 'url', 'temp_balance'])
