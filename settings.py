import PySimpleGUI as sg
import os.path

file_name = 'settings.txt'

def create_file(db, token):
    f = open(file_name, "a")
    f.write(db + '\n')
    f.write(token)
    f.close()

sg.theme('DarkAmber')   

layout = [  [sg.Text('Укажите путь к файлу БД:'), sg.FileBrowse(target='-IN0-', button_text = 'выбрать')],
            [sg.Input(key='-IN0-')],
            [sg.Text('Укажите BOT-TOKEN:')], 
            [sg.Input(key='-IN1-')],
            [sg.Text('')],
            [sg.Button('Сохранить настройки и выйти.'), sg.Button('Отмена.')]
            ]


window = sg.Window('Настройки Telegram бота.', layout)
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Отмена.':
        break
    if event == 'Сохранить настройки и выйти.':
        DB_path = values['-IN0-']
        bot_token = values['-IN1-']
        if os.path.exists(file_name):
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)
            os.remove(path)
            create_file(DB_path, bot_token)
            window.close()
        else:
            create_file(DB_path, bot_token)
            window.close()

