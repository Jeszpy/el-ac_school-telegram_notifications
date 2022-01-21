import getpass
import shutil
import PySimpleGUI as sg

username = getpass.getuser()
autorun_path = f'C:\\Users\{username}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'

sg.theme('DarkAmber')

try:
    shutil.copy(r'settings.txt', f'{autorun_path}\\settings.txt')
    shutil.copy(r'bot.exe', f'{autorun_path}\\bot.exe')
    layout = [[sg.Text('Бот успешно добален в автозагрузку.')], [sg.Button('Закрыть.')]]
except Exception as e:
    layout = [[sg.Text('Ошибка!')], 
    [sg.Text(e)],
    [sg.Button('Закрыть.')]
    ]

window = sg.Window('autorun', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Закрыть.':
        break