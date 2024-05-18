import time
import paramiko
import os
import re
import logging
import psycopg2
from psycopg2 import Error

from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

dotenv_path = Path('H:/PT_coding/devops_bot/.env')
load_dotenv(dotenv_path=dotenv_path)

host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')
TOKEN = os.getenv('TOKEN')
chat_id = os.getenv('CHAT_ID')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
database = os.getenv('DB_DATABASE')


stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Подключаем логирование
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s',
                    handlers=[logging.FileHandler("log.txt", mode='w'),
                              stream_handler])

logger = logging.getLogger(__name__)

connection = None

while True:
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=host,
                                      port=db_port,
                                      database=database)
        break
    except (Exception, Error) as error:
        logging.error("Ошибка при подключение к PostgreSQL не созданно: %s", error)
        time.sleep(1)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8)(?:\d{10}|(?:\(\d{3}\)\d{7})|(?:\s\(\d{3}\)\s\d{3}\s\d{2}\s\d{2})|'
                           r'(?:\s\d{3}\s\d{3}\s\d{2}\s\d{2})|(?:\-\d{3}\-\d{3}\-\d{2}\-\d{2}))')

    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов

    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены, для повторного поиска введите команду еще раз')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    phoneNumbers = ''  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i + 1}. {phoneNumberList[i]}\n'  # Записываем очередной номер
    context.user_data['phones'] = phoneNumberList
    update.message.reply_text(phoneNumbers)  # Отправляем сообщение пользователю
    update.message.reply_text(
        "Вы можете сохранить номера в базу данных что бы это сделать введите да, если вам это не нужно нажмите нет")
    return 'Add_phone'  # Завершаем работу обработчика диалога


def AddPhones(update: Update, context):
    if update.message.text.strip() == 'нет':
        update.message.reply_text('Завершаем операцию')
        return ConversationHandler.END

    if update.message.text.strip() not in ('да', 'нет'):
        update.message.reply_text('Выбран не валидный режим введите да или нет')
        return 'Add_phone'

    if update.message.text.strip() == 'да':

        update.message.reply_text('Выполняется добавление номеров в базу данных')
        try:
            cursor = connection.cursor()
            query = 'INSERT INTO PHONES (phone) VALUES '
            query += ','.join(["(%s)" for _ in range(len(context.user_data["phones"]))])
            query += ';'
            cursor.execute(query, context.user_data["phones"])
            connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Данные добавленны')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка добавление данных операция не выполнена')
        finally:
            if cursor is not None:
                cursor.close()

    return ConversationHandler.END


def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных адрессов: ')

    return 'find_email'


def findEmails(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий(или нет) email
    emailRegex = re.compile(r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*'
 \
                            r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')

    emailList = emailRegex.findall(user_input)  # Ищем email

    if not emailList:  # Обрабатываем случай, когда email отсутствует
        update.message.reply_text('Адресса электронной почты не найдены, для повторного поиска введите команду еще раз')
        return ConversationHandler.END  # Завершаем работу обработчика диалога

    emails = ''  # Создаем строку, в которую будем записывать email
    for i in range(len(emailList)):
        emails += f'{i + 1}. {emailList[i]}\n'  # Записываем email
    context.user_data['emails'] = emailList
    update.message.reply_text(emails)  # Отправляем сообщение пользователю
    update.message.reply_text(
        "Вы можете сохранить email в базу данных что бы это сделать введите да, если вам это не нужно нажмите нет")
    return 'Add_email'  # Завершаем работу обработчика диалога


def AddEmails(update: Update, context):
    if update.message.text.strip() == 'нет':
        update.message.reply_text('Завершаем операцию')
        return ConversationHandler.END

    if update.message.text.strip() not in ('да', 'нет'):
        update.message.reply_text('Выбран не валидный режим введите да или нет')
        return 'Add_email'

    if update.message.text.strip() == 'да':

        update.message.reply_text('Выполняется добавление email в базу данных')
        try:
            cursor = connection.cursor()
            query = 'INSERT INTO EMAILS (email) VALUES '
            query += ','.join(["(%s)" for _ in range(len(context.user_data["emails"]))])
            query += ';'
            cursor.execute(query, context.user_data["emails"])
            connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Данные добавленны')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка добавление данных операция не выполнена')
        finally:
            if cursor is not None:
                cursor.close()

    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'


def verifyPassword(update: Update, context):
    user_input = update.message.text.strip()
    if re.match(r'(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[!@#$%^&*()]){8,}', user_input):
        update.message.reply_text('Пароль сложный')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END


def getReleaseCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('cat /etc/*release')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getUnameCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -m && hostname && uname -v')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getUptimeCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getDfCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getFreeCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getMpstatCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getWCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getAuthsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getCriticalCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -p 2 -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getPsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getSSCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getServiceCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl --type=service | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getEmailsCommand(update: Update, context):
    logging.basicConfig(
        filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
        encoding="utf-8"
    )

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Emails;")
        data = cursor.fetchall()
        data = str(data).replace(']', '').replace('[', '').replace('), (', ')\n(')
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if cursor is not None:
            cursor.close()
    return ConversationHandler.END


def getPhoneCommand(update: Update, context):
    logging.basicConfig(
        filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO,
        encoding="utf-8"
    )

    try:

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Phones;")
        data = cursor.fetchall()
        data = str(data).replace(']', '').replace('[', '').replace('), (', ')\n(')
        update.message.reply_text(data)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if cursor is not None:
            cursor.close()
    return ConversationHandler.END


def getAptListCommand(update: Update, context):
    update.message.reply_text(
        'В данной комманде есть два режима работы: \n1 Вывод всех установленный пакетов(первых 20). \n2 Вывод информации по интересующему пакету')

    return 'get_apt_list'


def getAptList(update: Update, context):
    if update.message.text.strip() not in ('1', '2'):
        update.message.reply_text('Выбран не валидный режим введите 1 или 2')

    if update.message.text.strip() == '1':
        update.message.reply_text('Вы выбрали режим вывода всех пакетов')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, port=port)
        stdin, stdout, stderr = client.exec_command('dpkg -l | head -n 20')
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
        return ConversationHandler.END

    if update.message.text.strip() == '2':
        update.message.reply_text('Вы выбрали режим вывода информации по конкретному пакету. \nВведите название пакета')
        return "get_apt_list_specific"


def getAptListSpecific(update: Update, context):
    packetName = update.message.text.strip();
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('dpkg -s ' + packetName)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def getReplLogsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(
        'cat /var/log/postgresql/postgresql-14-main.log.1 | grep repl_user | tail -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'Add_phone': [MessageHandler(Filters.text & ~Filters.command, AddPhones)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'Add_email': [MessageHandler(Filters.text & ~Filters.command, AddEmails)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerGetRelease = ConversationHandler(
        entry_points=[CommandHandler('get_release', getReleaseCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetUname = ConversationHandler(
        entry_points=[CommandHandler('get_uname', getUnameCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetUptime = ConversationHandler(
        entry_points=[CommandHandler('get_uptime', getUptimeCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetDf = ConversationHandler(
        entry_points=[CommandHandler('get_df', getDfCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetFree = ConversationHandler(
        entry_points=[CommandHandler('get_free', getFreeCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetMpstat = ConversationHandler(
        entry_points=[CommandHandler('get_mpstat', getMpstatCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetW = ConversationHandler(
        entry_points=[CommandHandler('get_w', getWCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetAuths = ConversationHandler(
        entry_points=[CommandHandler('get_auths', getAuthsCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetCritical = ConversationHandler(
        entry_points=[CommandHandler('get_critical', getCriticalCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetPs = ConversationHandler(
        entry_points=[CommandHandler('get_ps', getPsCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetSS = ConversationHandler(
        entry_points=[CommandHandler('get_ss', getSSCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetServices = ConversationHandler(
        entry_points=[CommandHandler('get_services', getServiceCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetEmails = ConversationHandler(
        entry_points=[CommandHandler('get_emails', getEmailsCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerGetPhones = ConversationHandler(
        entry_points=[CommandHandler('get_phone_numbers', getPhoneCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerReplLogs = ConversationHandler(
        entry_points=[CommandHandler('get_repl_logs', getReplLogsCommand)],
        states={
        },
        fallbacks=[]
    )

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
            'get_apt_list_specific': [MessageHandler(Filters.text & ~Filters.command, getAptListSpecific)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetRelease)
    dp.add_handler(convHandlerGetUname)
    dp.add_handler(convHandlerGetUptime)
    dp.add_handler(convHandlerGetDf)
    dp.add_handler(convHandlerGetFree)
    dp.add_handler(convHandlerGetMpstat)
    dp.add_handler(convHandlerGetW)
    dp.add_handler(convHandlerGetAuths)
    dp.add_handler(convHandlerGetCritical)
    dp.add_handler(convHandlerGetPs)
    dp.add_handler(convHandlerGetSS)
    dp.add_handler(convHandlerGetServices)
    dp.add_handler(convHandlerAptList)
    dp.add_handler(convHandlerGetEmails)
    dp.add_handler(convHandlerGetPhones)
    dp.add_handler(convHandlerReplLogs)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
