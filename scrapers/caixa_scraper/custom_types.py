from typing import NamedTuple, List, Optional
from datetime import datetime

# from
# <a href="JavaScript:Inicializar('00782397301','LOS TRES DE VIRGINIA SL','9725017823973',
# 'rXAM53iGe1etcAzneIZ7VwAAAWerw4WjvCWHkj9PyTs')"
# class="no_subrayado"  title=""  onClick="this.blur();"><span>LOS TRES DE VIRGINIA SL</span></a>
Company = NamedTuple('Company', [
    ('title', str),
    ('request_params', List[str])
])


N43FromList = NamedTuple('N43FromList', [
    ('file_created_at', datetime),
    ('nom_fich_hp_param', str),
    ('clave_itr_param', str),
    ('clau_rec_param', str),
    ('nom_fich_pc_param', str),
    ('tipo_fichero_param', str),
])

