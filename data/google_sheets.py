from pprint import pprint
import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

async def add_to_table(name, value):
    if name == 'ST':
        column = 'A'
    elif name == 'V':
        column = 'B'
    else:
        print("Invalid name provided. Please provide 'ST' or 'V'.")
        return

    # Получаем данные для доступа к Google Sheets
    CREDENTIALS_FILE = 'data/creds.json'
    spreadsheet_id = '13eaUPw-ceQUmeU31WwC4MiU4kM7-RCwPgbzco-xCuAA'

    # Авторизация и создание сервиса для работы с таблицей
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = discovery.build('sheets', 'v4', http=httpAuth)

    # Получаем текущие значения в столбце
    range_name = f'{column}2:{column}'
    try:
        values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            majorDimension='COLUMNS'
        ).execute()
    except KeyError:
        # Если столбец пустой, начинаем с первой строки
        first_empty_cell_index = 2
    else:
        # Находим первую пустую ячейку в столбце
        first_empty_cell_index = len(values.get('values', [[]])[0]) + 2  # 2 is added because we start from A2/B2

    # Обновляем таблицу добавляя новые данные
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"{column}{first_empty_cell_index}",
                 "majorDimension": "ROWS",
                 "values": [[value]]}
            ]
        }
    ).execute()

    print(f"Data '{value}' added to column '{column}' at row {first_empty_cell_index}")