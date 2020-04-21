from telebot import types
import time
import telebot
from database import Locations, Workers, History, db, TimeHandler

bot = telebot.TeleBot('1186093630:AAG5au2zY3yv6mHsEXefI1oNdeJClZBv6VY')


def count_locations():
    return Locations.count_documents({})


def send_msg(*args):
    try:
        if len(args) == 3:
            bot.send_message(args[0], args[1], reply_markup=args[2])
        else:
            bot.send_message(args[0], args[1])
    except:
        if args[2]:
            bot.send_message(args[0], args[1], reply_markup=args[2])
        else:
            bot.send_message(args[0], args[1])


@bot.message_handler(commands=['start'])
def start(message):
    send_msg(message.chat.id,
             "Hi, press /go")


@bot.message_handler(commands=['go'])
def name_listener(message):
    try:
        try:
            outname = Workers.find_one({"Telegram": message.chat.id})
        except:
            outname = None
        if outname:
            send_msg(message.chat.id, '''Вы находитесь в главном меню. Доступные вам команды:
                /begin для начала отсчета
                /stop для окончания отсчета
                /time для отображения накопленного времени''')
            bot.register_next_step_handler(message, free_time_function)
        else:
            send_msg(message.chat.id, 'Введите свое имя')
            bot.register_next_step_handler(message, surname_listener)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def surname_listener(message):
    try:
        if message.text is not None:
            Workers.insert_one({"Telegram": message.chat.id,
                                "Name": message.text,
                                "Surname": "",
                                "Total time": "0:0:0",
                                "Last project": "",
                                "Last job": "",
                                "Last lat": 0,
                                "Last lng": 0
                                })
            TimeHandler.insert_one({"Telegram": message.chat.id, "Time_started": 0})
            send_msg(message.chat.id, 'Введите свою фамилию')
            bot.register_next_step_handler(message, surname_handler)
        else:
            send_msg(message.chat.id, "Введите фамилию корректно")
            bot.register_next_step_handler(message, surname_listener)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def surname_handler(message):
    try:
        if message.text is not None:
            Workers.update_one({"Telegram": message.chat.id}, {"$set": {"Surname": message.text}})
            send_msg(message.chat.id, '''Регистрация прошла успешно, тепер вы можете использовать бота. Его команды:
                /begin для начала отсчета
                /stop для окончания отсчета
                /time для отображения накопленного времени''')
        else:
            send_msg(message.chat.id, "Введите фамилию корректно")
            bot.register_next_step_handler(message, surname_listener)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def project_choice(message):
    try:
        markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True, resize_keyboard=True)
        locations = [c['Name'] for c in db['Locations'].find()]
        for i in range(0, count_locations()):
            markup.add(types.KeyboardButton(text=locations[i]))
        send_msg(message.chat.id, 'Выберите обьект на котором вы работаете:', markup)
        bot.register_next_step_handler(message, geo)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def geo(message):
    try:
        try:
            proj_ident = Locations.find_one({"Name": message.text})['_id']
        except Exception as e:
            proj_ident = None
        if proj_ident:
            Workers.update_one({"Telegram": message.chat.id}, {"$set": {"Last project": proj_ident}})
            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
            keyboard.add(button_geo)
            send_msg(message.chat.id,
                     "Нажмите на кнопку и передайте мне свое местоположение или нажмите /back для возврата в главное меню",
                     keyboard)
            bot.register_next_step_handler(message, location_new)

        else:
            send_msg(message.chat.id, "Некорректный ввод")
            bot.register_next_step_handler(message, geo)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def location_new(message):
    try:
        proj_ident = Workers.find_one({"Telegram": message.chat.id})["Last project"]
        if message.location:
            latitude_from_base = Locations.find_one({"_id": proj_ident})['Latitude']
            longitude_from_base = Locations.find_one({"_id": proj_ident})['Longitude']

            if latitude_from_base == "":
                latitude_from_base = 0
            else:
                latitude_from_base = float(latitude_from_base)

            if longitude_from_base == "":
                longitude_from_base = 0
            else:
                longitude_from_base = float(longitude_from_base)

            if latitude_from_base - 0.0035 < message.location.latitude < latitude_from_base + 0.0035 and \
                    longitude_from_base - 0.0035 < message.location.longitude < longitude_from_base + 0.0035:
                now = time.time()
                db['TimeHandler'].update_one({"Telegram": message.chat.id}, {'$set': {"Time_started": now}})
                send_msg(message.chat.id,
                         "Ваша локация соответствует необходимой, счетчик запущен. Для его остановки нажмите /stop  ")
                Workers.update_one({"Telegram": message.chat.id}, {"$set": {"Last project": proj_ident}})
                bot.register_next_step_handler(message, stop_function)
            else:
                send_msg(message.chat.id,
                         "Ваша геолокация не соответствует необходимой, вернитесь и отправьте геолокацию заново или нажмите /back для возврата в главное меню ")
                bot.register_next_step_handler(message, location_new)
        elif message.text == "/back":
            send_msg(message.chat.id, '''Вы находитесь в главном меню. Доступные вам команды:
                /begin для начала отсчета
                /stop для окончания отсчета
                /time для отображения накопленного времени''')
        else:
            send_msg(message.chat.id, 'Я ожидаю вашу геолокацию')
            bot.register_next_step_handler(message, location_new)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def stop_function(message):
    try:
        if message.text == '/stop':
            send_msg(message.chat.id, "Укажите в минутах время, проведенное на обеде")
            bot.register_next_step_handler(message, dinner_hours_handler)
        else:
            send_msg(message.chat.id,
                     "Сейчас вам доступна только команда /stop ")
            bot.register_next_step_handler(message, stop_function)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def dinner_hours_handler(message):
    try:
        if message.text.isdigit():
            db['TimeHandler'].update_one({"Telegram": message.chat.id},
                                         {'$inc': {"Time_started": int(message.text) * 60},
                                          '$set': {"Dinner": int(message.text)}})
            send_msg(message.chat.id, "Что вы делали сегодня? ")
            bot.register_next_step_handler(message, location_caller)
        else:
            send_msg(message.chat.id, "Введите обеденное время корректно")
            bot.register_next_step_handler(message, dinner_hours_handler)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def location_caller(message):
    try:
        if message.text is None:
            send_msg(message.chat.id, "Некорректный ввод")
            bot.register_next_step_handler(message, location_caller)
        else:
            Workers.update_one({"Telegram": message.chat.id}, {"$set": {"Last job": message.text}})
            send_msg(message.chat.id, "Теперь повторно отправьте свою геолокацию чтобы остановить таймер")
            bot.register_next_step_handler(message, location_stopper)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


def location_stopper(message):
    try:
        if message.location:
            user_dict = Workers.find_one({"Telegram": message.chat.id})
            lastproject_from_base = user_dict['Last project']

            latitude_from_base = Locations.find_one({"_id": lastproject_from_base})['Latitude']

            longitude_from_base = Locations.find_one({"_id": lastproject_from_base})['Longitude']

            name_from_base = user_dict['Name']

            surname_from_base = user_dict['Surname']

            last_job_from_base = user_dict['Last job']

            last_project_name_from_base = Locations.find_one({"_id": lastproject_from_base})['Name']

            if latitude_from_base == "":
                latitude_from_base = 0
            else:
                latitude_from_base = float(latitude_from_base)

            if longitude_from_base == "":
                longitude_from_base = 0
            else:
                longitude_from_base = float(longitude_from_base)

            if latitude_from_base - 0.0035 < message.location.latitude < latitude_from_base + 0.0035 and \
                    longitude_from_base - 0.0035 < message.location.longitude < longitude_from_base + 0.0035:
                send_msg(message.chat.id, "Ваша локация соответствует необходимой, таймер остановлен корректно")
                minutes = 0
                hours = 0
                prev_time = db["TimeHandler"].find_one({"Telegram": message.chat.id})['Time_started']
                now = time.time()
                seconds = int(now - prev_time)
                if seconds < 0:
                    seconds = 0
                if seconds < 0:
                    seconds = 0
                if seconds >= 60:
                    minutes = seconds // 60
                    seconds = seconds % 60
                if minutes >= 60:
                    hours = minutes // 60
                    minutes = minutes % 60

                Workers.update_one({"Telegram": message.chat.id},
                                   {"$set": {"Last lat": message.location.latitude,
                                             "Last lng": message.location.longitude}})
                time_list = user_dict['Total time'].split(":")
                hours_from_base = int(time_list[0])

                minutes_from_base = int(time_list[1])

                seconds_from_base = int(time_list[2])

                full_hours = hours + hours_from_base
                full_minutes = minutes + minutes_from_base
                full_secounds = seconds + seconds_from_base
                if full_secounds >= 60:
                    full_minutes = full_minutes + (full_secounds // 60)
                    full_secounds = full_secounds % 60
                if full_minutes >= 60:
                    full_hours = full_hours + (full_minutes // 60)
                    full_minutes = full_minutes % 60
                time_totally = str(full_hours) + ":" + str(full_minutes) + ":" + str(full_secounds)
                Workers.update_one({"Telegram": message.chat.id},
                                   {"$set": {"Total time": time_totally}})
                fresh_time = str(hours) + ":" + str(minutes) + ":" + str(seconds)

                dinner_time = db["TimeHandler"].find_one({"Telegram": message.chat.id})['Dinner']

                pretty_time_court = time.strftime("%d %b %H %M %S").split(' ')
                pretty_time = pretty_time_court[0] + " " + pretty_time_court[1] + " " + str(
                    int(pretty_time_court[2]) - 1) + ":" + pretty_time_court[3] + ":" + pretty_time_court[4]

                History.insert_one(
                    {"Telegram": message.chat.id, "Name": name_from_base, "Surname": surname_from_base,
                     "Time written": fresh_time, "Time": pretty_time, "Project": last_project_name_from_base,
                     "Work": last_job_from_base, "Dinner": dinner_time, "Correct": True})
                send_msg(message.chat.id,
                         "За сегодня вы получили {0} часов {1} минут {2} секунд, делая {3} на обьекте  {4}".format(
                             hours, minutes, seconds, last_job_from_base, last_project_name_from_base))
                send_msg(message.chat.id,
                         "Ваше общее время: {0} часов , {1} минут , {2} секунд".format(full_hours, full_minutes,
                                                                                       full_secounds))
                send_msg(403316002,
                         "Пользователь {0} {1} остановил таймер корректно, начав работу на обьекте {2}, делая {3}, записал себе {4} часов {5} минут {6} секунд, обед длился {7} минут".format(
                             name_from_base, surname_from_base, last_project_name_from_base,
                             last_job_from_base, hours, minutes, seconds, dinner_time))

            else:
                minutes = 0
                hours = 0
                prev_time = db["TimeHandler"].find_one({"Telegram": message.chat.id})['Time_started']
                now = time.time()
                seconds = int(now - prev_time)
                if seconds < 0:
                    seconds = 0
                if seconds < 0:
                    seconds = 0
                if seconds >= 60:
                    minutes = seconds // 60
                    seconds = seconds % 60
                if minutes >= 60:
                    hours = minutes // 60
                    minutes = minutes % 60

                Workers.update_one({"Telegram": message.chat.id},
                                   {"$set": {"Last lat": message.location.latitude,
                                             "Last lng": message.location.longitude}})

                time_list = user_dict['Total time'].split(":")
                hours_from_base = int(time_list[0])

                minutes_from_base = int(time_list[1])

                seconds_from_base = int(time_list[2])

                full_hours = hours + hours_from_base
                full_minutes = minutes + minutes_from_base
                full_secounds = seconds + seconds_from_base
                if full_secounds >= 60:
                    full_minutes = full_minutes + (full_secounds // 60)
                    full_secounds = full_secounds % 60
                if full_minutes >= 60:
                    full_hours = full_hours + (full_minutes // 60)
                    full_minutes = full_minutes % 60
                time_totally = str(full_hours) + ":" + str(full_minutes) + ":" + str(full_secounds)
                Workers.update_one({"Telegram": message.chat.id},
                                   {"$set": {"Total time": time_totally}})
                fresh_time = str(hours) + ":" + str(minutes) + ":" + str(seconds)

                dinner_time = db["TimeHandler"].find_one({"Telegram": message.chat.id})['Dinner']

                pretty_time_court = time.strftime("%d %b %H %M %S").split(' ')
                pretty_time = pretty_time_court[0] + " " + pretty_time_court[1] + " " + str(
                    int(pretty_time_court[2]) - 1) + ":" + pretty_time_court[3] + ":" + pretty_time_court[4]

                History.insert_one(
                    {"Telegram": message.chat.id, "Name": name_from_base, "Surname": surname_from_base,
                     "Time written": fresh_time, "Time": pretty_time, "Project": last_project_name_from_base,
                     "Work": last_job_from_base, "Dinner": dinner_time, "Correct": False})
                send_msg(message.chat.id,
                         "За сегодня вы получили {0} часов {1} минут {2} секунд, делая {3} на обьекте {4}, но таймер был остановлен НЕКОРРЕКТНО".format(
                             hours, minutes, seconds, message.text, last_project_name_from_base))
                send_msg(403316002,
                         "Пользователь {0} {1} остановил таймер НЕКОРРЕКТНО, начав работу на обьекте {2}, делая {3}. Записанное время:{4} часов {5} минут {6} секунд, обед: {7} минут. Последние координаты: Lat: {8} Lng: {9} ".format(
                             name_from_base, surname_from_base, last_project_name_from_base,
                             last_job_from_base, hours, minutes, seconds, dinner_time, message.location.latitude,
                             message.location.longitude))
                send_msg(message.chat.id,
                         "Ваше общее время: {0} часов , {1} минут , {2} секунд".format(full_hours, full_minutes,
                                                                                       full_secounds))
        else:
            send_msg(message.chat.id, "Я ожидаю вашу геолокацию")
            bot.register_next_step_handler(message, location_stopper)
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


@bot.message_handler(commands=['time', 'stop', 'begin'])
def free_time_function(message):
    try:
        if message.text == "/time":
            time_value = Workers.find_one({"Telegram": message.chat.id})["Total time"]
            send_msg(message.chat.id,
                     f"Ваше время: {time_value}")

        elif message.text == "/begin":
            project_choice(message)
        elif message.text == "/stop":
            send_msg(message.chat.id, "Нечего останавливать, таймер не был запущен")

        else:
            send_msg(message.chat.id, "Ваше сообщение некорректно")
    except Exception as e:
        send_msg(message.chat.id, "Error occurred")
        print("Exception: ", e)


bot.polling(none_stop=True, timeout=123)
