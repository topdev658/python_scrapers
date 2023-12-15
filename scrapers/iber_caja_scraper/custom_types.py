from typing import NamedTuple

Contract = NamedTuple('Contract', [
    ('id', str),  # numero, Z43414
    ('title', str),  # identidadTitular, 1B83233346 00
    ('org_title', str),  # nombreTitular, "ACTURUS CAPITAL SL"
    ('orden_param', str),  # orden, 3
    ('negocio_param', str),  # negocio, true
])
