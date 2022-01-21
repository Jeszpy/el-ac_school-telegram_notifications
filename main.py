from ast import While
from datetime import datetime, timedelta
from re import T
import fdb
import telebot
from multiprocessing import Process, freeze_support
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import  CallbackQuery, Message
from aiogram.dispatcher.filters import Text
from aiogram_calendar import simple_cal_callback, SimpleCalendar

with open("settings.txt", "r") as file:
    contents = file.readlines()
    db_path = contents[0].strip()
    API_TOKEN = contents[1].strip()


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
tb = telebot.TeleBot(API_TOKEN)

def create_con(path=db_path):
    con = fdb.connect(dsn=f'127.0.0.1:{path}',
                    user='SYSDBA',
                    password='masterkey',
                    charset='WIN1251')
    return con


poll_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
poll_keyboard.add(types.KeyboardButton(text="🗺️ Местоположение 🗺️"))
poll_keyboard.add(types.KeyboardButton(text="📄 Получить отчет 📄"))

@dp.message_handler(commands='start')
async def start_cmd_handler(message: types.Message):
  await message.reply(f"👋 Здравствуйте! Ваш ID: {message.chat.id}", reply_markup=poll_keyboard)

def location(parent):
    try:
        date = datetime.today().strftime("%d.%m.%Y")
        date_plus_day = (datetime.today() + timedelta(days=1)).strftime("%d.%m.%Y")

        get_person = f"select user_num from user_props where prop_value = {int(parent)}"
        con = create_con()
        cur = con.cursor()

        cur.execute(get_person)
        person = cur.fetchone()
        person = person[0]

        get_events = f"select * from events where datetime >= '{date}' and datetime < '{date_plus_day}' and param2 = {int(person)} and event_type = {23}"
        cur.execute(get_events)
        data = cur.fetchall()
        if data == []:
            return 'Сегодня на занятиях не был(а).'
        else:
            data = data[-1][4]
            get_readers = f"select phys_addr from d5_readers where reader = {int(data)}"
            cur.execute(get_readers)
            reader = cur.fetchone()

            if reader[0] == 0:
                return '🏫 В учебном учреждении 🏫'
            else: return '🚶🚶‍♀️ Вне учебного учреждения 🚶‍♀️🚶'
    except Exception as e:
        return '🙏 Извините, но вас не внесли в базу данных. 🙏'
        

@dp.message_handler(lambda message: message.text == ("🗺️ Местоположение 🗺️"))
async def check_status(message: types.Message):
  status = location(message.chat.id)
  await message.answer(status, reply_markup=poll_keyboard)

def check_parent_in_DB(parent):
    try:
        get_person = f"select user_num from user_props where prop_value = {int(parent)}"
        con = create_con()
        cur = con.cursor()

        cur.execute(get_person)
        person = cur.fetchone()
        person = person[0]
        if person != None:
            return True
    except:
        return False

@dp.message_handler(Text(equals=['📄 Получить отчет 📄'], ignore_case=True))
async def nav_cal_handler(message: Message):
    if(check_parent_in_DB(message.chat.id)):
        await message.answer("Пожалуйста, выберите дату: ", reply_markup = await SimpleCalendar().start_calendar())
    else: await message.answer('🙏 Извините, но вас не внесли в базу данных. 🙏', reply_markup=poll_keyboard)

def report(date, parent):
    entrance_events = []
    exit_events = []

    if date > datetime.today():
        message = '📅 Эта дата ещё не наступила, пожалуйста, выберите другую. 📅'
        return message
    else:
        date_plus_day = date + timedelta(days=1)
        date = date.strftime("%d.%m.%Y")
        date_plus_day = date_plus_day.strftime("%d.%m.%Y")

        get_person = f"select user_num from user_props where prop_value = {int(parent)}"
        con = create_con()
        cur = con.cursor()

        cur.execute(get_person)
        person = cur.fetchone()
        person = person[0]

        get_events = f"select * from events where datetime >= '{date}' and datetime < '{date_plus_day}' and param2 = {int(person)} and event_type = {23}"
        cur.execute(get_events)
        data = cur.fetchall()

        for el in data:
            get_readers = f"select phys_addr from d5_readers where reader = {el[4]}"
            cur.execute(get_readers)
            reader = cur.fetchall()
            if reader[0][0] == 0:
                entrance_events.append(el[1])
            else: exit_events.append(el[1])
        
        total_time = timedelta()
        if len(entrance_events) == len(exit_events):
            for el in list(zip(entrance_events, exit_events)):
                total_time += el[1] - el[0]
        else: total_time = '⚠️ Невозможно посчитать из-за неравного количества приходов и уходов. ⚠️'

        """
        total_time = 0
        if len(entrance_events) != len(exit_events):
            total_time = 'Невозможно посчитать из-за неравного количества приходов и уходов.'
        for enter_time, exit_time in zip(entrance_events, exit_events):
            total_time += exit_time - enter_time
        total_time.strftime("%H:%M:%S")
        """ 

        en_ev = []
        for el in entrance_events:
            en_ev.append(el.strftime("%H:%M:%S"))

        ex_ev = []
        for el in exit_events:
            ex_ev.append(el.strftime("%H:%M:%S"))

        message = f'Приходы:\n'
        message += '\n'
        for el in en_ev:
            message += f'{el}\n'
        message += '\n'
        message += 'Уходы:\n'
        message += '\n'
        for el in ex_ev:
            message += f'{el}\n'
        message += '\n'
        message += 'Общее время прибывания:\n'
        message += '\n'
        message += str(total_time)

        return message

@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        date.strftime("%d.%m.%Y")
        data = report(date, callback_query.message.chat.id)
        await callback_query.message.answer(f'{data}', reply_markup = poll_keyboard)

def listen_event():
    while True:
        try:
            con = create_con()
            cond = con.event_conduit(["d_new_event"])
            cond.begin()
            cond.wait()
            select_num = "select max(num) as NUM from events"
            cur = con.cursor()
            cur.execute(select_num)
            num = cur.fetchone()
            select_event = f"select * from events where num = {int(num[0])}"
            cur.execute(select_event)
            get_event = cur.fetchone()
            if get_event[3] == 23:
                children_id = get_event[5]
                event_time = get_event[1]
                event_time = event_time.strftime("%H:%M:%S")
                select_parent_id = f'select prop_value from user_props where user_num = {children_id}'
                cur.execute(select_parent_id)
                parent_id = cur.fetchone()
                parent_id = parent_id[0].strip() # .replace(" ", "")
                if parent_id == '':
                    message = ''
                else:
                    select_children_name = f'select username from users where num = {children_id}'
                    cur.execute(select_children_name)
                    children_name = cur.fetchone()
                    children_name = children_name[0]

                    reader = get_event[4]
                    select_reader = f'select read_name from d_devices where reader = {reader}'
                    cur.execute(select_reader)
                    reader = cur.fetchone()
                    reader = reader[0]

                    message = f'{event_time}   {children_name} прошел по карте доступа через {reader}'
                    tb.send_message(chat_id=parent_id, text=message)
        except Exception as e:
            pass
        finally:
            print('close con')
            con.close()
            pass


def start_tg_observer():
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    freeze_support()
    try:
        Process(target=start_tg_observer).start()
        Process(target=listen_event).start()
    except Exception as e:
        pass
