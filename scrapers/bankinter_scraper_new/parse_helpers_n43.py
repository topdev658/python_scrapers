from typing import List


def get_programmed_daily_files_data(resp_json: dict) -> List[dict]:
    """Parses
    {
  "page": 0,
  "items": [
    {
      "id": "6b9dc",
      "name": "ESOFITEC",
      "fileRqs": [
        {
          "id": "d981c_B_XBBBB9fcS8",
          "type": "diaria",
          "fileName": "DIARIO_ESOFITEC",
          "fileStatus": "descargado",
          "info": {
            "description": true,
            "observation": false,
            "automaticMovement": false
          },
          "keyMgmt": "9999123123595900001"
        }
      ]
    },
    {
      "id": "a3b3D",
      "name": "SIN GRUPO",
      "fileRqs": [
        {
          "id": "4705D_c_XBBBBSDBHc",
          "type": "peticion",
          "fileName": "24022022_24022022_SIN GRUPO",
          "fileStatus": "descargado",
          "info": {
            "description": true,
            "observation": true,
            "automaticMovement": false
          },
          "startDate": "2022-02-24",
          "endDate": "2022-02-24",
          "keyMgmt": "2022040512581600002"
        }
      ]
    }
    ...
    ]}
    """
    daily_files_data = []  # type: List[dict]
    for file_data in resp_json['items']:
        if file_data['fileRqs'][0]['type'] == 'diaria':
            daily_files_data.append(file_data)
    return daily_files_data
