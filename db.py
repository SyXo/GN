# -*- coding: utf-8 -*-
"""Control DB file for GNBot"""
from Config_GNBot.config import GN_ID, GN_Stickers, BD_CONNECT
from funcs import log
import pymysql
import redis
import random


def start_connection():
    """
    .. notes:: Funk to connect to MySQL DB
    :return: connection
    :rtype: connection: pymysql.connect
    """
    try:
        connection = pymysql.connect(**BD_CONNECT)
        return connection
    except pymysql.err.OperationalError:
        log('Ошибка подключения к БД!', 'error')


def get_user(user, chat) -> [dict, int or bool, bool]:
    """
    :param user
    :param chat
    :return: user, en
    :rtype: user: dict, en: int
    :return: False, False
    :rtype: False: bool, False: bool
    .. notes:: Get some user
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM Users ORDER BY karma DESC;')
        all_users = cursor.fetchall()
        users_groups = []
        for en, user_ in enumerate(all_users):
            if user_['supergroup'] is None:
                all_users.pop(en)
            else:
                for group in user_['supergroup'].split(','):
                    if group == str(chat.id):
                        users_groups.append(user_)
        if users_groups:
            for en, user_ in enumerate(users_groups, 1):
                if user_['user_id'] == user.id:
                    return user_, en
        else:
            return False, False
    connection.close()


def add_user(user, chat=None, connection=None) -> None:
    """
    :param user
    :param chat
    :param connection
    :return: None
    .. notes:: add or update user to DB
    """
    if connection is None:
        connection = start_connection()
    with connection.cursor() as cursor:
        if chat is not None:
            if cursor.execute(f'SELECT * FROM Setting WHERE id=\'{chat.id}\';') == 0:
                cursor.execute(f'INSERT INTO `Setting`(`id`) VALUES (\'{chat.id}\');')
                connection.commit()
        else:
            if cursor.execute(f'SELECT * FROM Setting WHERE id=\'{user.id}\';') == 0:
                cursor.execute(f'INSERT INTO `Setting`(`id`) VALUES (\'{user.id}\');')
                connection.commit()
        if cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE \'{user.id}\'') == 0:
            if chat is not None:
                cursor.execute('INSERT INTO Users (`user_id`, `is_bote`, `first_name`, `last_name`, '
                               '`username`, `is_gn`, `supergroup`) VALUE '
                               f'(\'{int(user.id)}\', \'{str(user.is_bot)}\',\'{user.first_name}\','
                               f'\'{user.last_name}\',\'{user.username}\','
                               f' \'{str(True) if str(chat.id) == GN_ID else str(False)}\', '
                               f'\'{str(chat.id)},\');')
            else:
                cursor.execute('INSERT INTO Users (`user_id`, `is_bote`, `first_name`, `last_name`, '
                               '`username`) VALUE '
                               f'(\'{int(user.id)}\', \'{str(user.is_bot)}\',\'{user.first_name}\','
                               f'\'{user.last_name}\',\'{user.username}\');')
            connection.commit()
        else:
            cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE {user.id}')
            user_db = cursor.fetchone()
            if user_db['first_name'] != user.first_name:
                cursor.execute(f'UPDATE Users SET first_name=\'{user.first_name}\' WHERE user_id LIKE {user.id};')
                connection.commit()
            if user_db['last_name'] != user.last_name:
                cursor.execute(f'UPDATE Users SET last_name=\'{user.last_name}\' WHERE user_id LIKE {user.id};')
                connection.commit()
            if user_db['username'] != user.username:
                cursor.execute(f'UPDATE Users SET username=\'{user.username}\' WHERE user_id LIKE {user.id};')
                connection.commit()
            if chat is not None:
                if cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE {user.id} AND supergroup IS NULL;') != 0:
                    cursor.execute(f'UPDATE Users SET supergroup = \'{chat.id},\' WHERE user_id LIKE {user.id};')
                    connection.commit()
                elif cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE \'{user.id}\' AND supergroup IS NOT NULL;') != 0:
                    cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE \'{user.id}\';')
                    res = cursor.fetchone()
                    if str(chat.id) not in res['supergroup'].split(','):
                        cursor.execute(f'UPDATE Users SET supergroup = \'{res["supergroup"] + str(chat.id)},\''
                                       f' WHERE user_id LIKE {user.id};')
                        connection.commit()
                if str(chat.id) == GN_ID and cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE {user.id} '
                                                                   f'AND is_gn = \'False\';') == 0:
                    cursor.execute(f'UPDATE Users SET is_gn = \'True\' WHERE user_id LIKE {user.id}')
                    connection.commit()


def reset_users(chat_id=None) -> None:
    """
    :param chat_id
    :type chat_id: str
    :return: None
    .. notes:: reset users daily karma
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM Users WHERE supergroup IS NOT NULL AND is_bote!=\'True\';')
        if chat_id is None:
            for user in cursor.fetchall():
                cursor.execute(f'UPDATE Users SET daily={user["karma"]} WHERE id={user["id"]};')
                connection.commit()
        else:
            for user in cursor.fetchall():
                 for group in user['supergroup'].split(','):
                     if group == chat_id:
                         cursor.execute(f'UPDATE Users SET daily={user["karma"]} WHERE id={user["id"]};')
                         connection.commit()
    connection.close()


def get_bad_guy() -> dict:
    """
    :return: dict_bag_guys
    :rtype: dict_bag_guys: dict
    .. notes:: get bad guys for all super groups
    """
    connection = start_connection()
    all_users = {}
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT id FROM Setting WHERE bad_guy=\'On\';')
        chats = cursor.fetchall()
        cursor.execute(f'SELECT * FROM Users WHERE supergroup IS NOT NULL AND is_bote=\'False\';')
        users = cursor.fetchall()
    for user in users:
        for group in user['supergroup'].split(','):
            for chat in chats:
                if group == chat['id']:
                    if chat['id'] not in all_users:
                        all_users[chat['id']] = []
                    all_users[chat['id']].append({'id': user['user_id'], 'karma': user['karma'], 'daily': user['daily']})
    for chat, users in all_users.items():
        bad_guy = []
        for user in users:
            if not bad_guy:
                bad_guy.append(user)
            elif user['karma'] - user['daily'] < bad_guy[0]['karma'] - bad_guy[0]['daily']:
                bad_guy.clear()
                bad_guy.append(user)
            elif user['karma'] - user['daily'] == bad_guy[0]['karma'] - bad_guy[0]['daily']:
                bad_guy.append(user)
        all_users[chat] = bad_guy
    return all_users


def save_pin_bag_guys(chat_id: str, message_id: str) -> None:
    """
    :param chat_id
    :type chat_id: str
    :param message_id
    :type message_id: str
    :return: None
    .. notes:: save pins id's
    """
    r = redis.Redis(host='localhost', port=6379, db=2)
    r.set(chat_id, message_id)

def get_pin_bag_guys() -> list:
    """
    :return: list_pins
    :rtype: list_pins: list
    .. notes:: get pin's messages
    """
    r = redis.Redis(host='localhost', port=6379, db=2)
    return [{'chat_id': id_.decode('utf-8'), 'message_id': r.get(id_.decode('utf-8'))} for id_ in r.keys()]


def change_setting(chat_id: str, method: str, status: str) -> None:
    """
    :param: chat_id
    :type: chat_id: str
    :param: method
    :type: method: str
    :param: status
    :type: status: str
    :return: None
    .. notes:: change some setting in group
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        if method == 'bad_guy' and status == 'on':
            reset_users(chat_id)
        cursor.execute(f'UPDATE Setting SET `{method}`=\'{status.title()}\' WHERE id LIKE \'{chat_id}\'')
        connection.commit()
    connection.close()


def check(user_id: str, check_t: str) -> bool:
    """
    :param: user_id
    :type: user_id: str
    :param: check_t
    :type: check_t: str
    :rtype: bool
    .. notes:: check user in DB
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        return False if cursor.execute(f'SELECT * FROM Users WHERE user_id LIKE \'{user_id}\' AND {check_t} LIKE \'True\';') == 0 else True


def change_karma(user_id, action: str, exp: int):
    """
    :param: user
    :param: action
    :type: action: str
    :param: exp
    :type: exp: int
    :type: check_t: str
    :return karma
    :rtype: karma: dict
    .. notes:: change and get back karma of some users
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT `karma` FROM `Users` WHERE `user_id` = {str(user_id)};')
        karma = int(cursor.fetchone()['karma'])
        if action == '+':
            karma += exp * 10
        else:
            karma -= exp * 10
        cursor.execute(f'UPDATE `Users` SET `karma` = \'{karma}\' WHERE `user_id` = \'{str(user_id)}\';')
        connection.commit()
    return karma


def get_from(id_: [int, str], type_=None) -> [list, dict, str]:
    """
    :param id_
    :type: id_: int
     :param type_
    :type: type_: str
    .. notes:: get something from somewhere
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        if type_ == 'Users_stat':  # get stats users in some group
            cursor.execute(f'SELECT * FROM Users WHERE is_bote = \'False\' AND supergroup IS NOT NULL ORDER BY karma DESC')
            return [i for i in cursor.fetchall() if str(id_) in i['supergroup'].split(',')]
        elif type_ == 'Setting':  # get setting from group
            cursor.execute(f'SELECT * FROM Setting WHERE id=\'{id_}\';')
            return cursor.fetchone()
        elif type_ == 'Users_name':  # # get username by user_id
            cursor.execute(f'SELECT first_name, last_name FROM Users WHERE user_id=\'{id_}\';')
            user = cursor.fetchone()
            return f"{user['first_name']} {user['last_name']}" if user['last_name'] != 'None' else user['first_name']


def get_roulette() -> list:
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT id FROM Setting WHERE roulette=\'On\';')
    return cursor.fetchall()


def add_sticker(id_, emoji, name) -> None:
    """
    :param: id_
    :param: emoji
    :param: name
    :return None
    .. notes:: add new sticker to DB
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        if cursor.execute(f'SELECT * FROM Stickers WHERE `set_name`=\'{name}\' AND emoji=\'{emoji}\';') == 0:
            cursor.execute(f'INSERT INTO `Stickers`(`item_id`, `emoji`, `set_name`) VALUES (\'{id_}\','
                               f'\'{emoji}\',\'{name}\');')
            connection.commit()
    connection.close()

def random_sticker(gn=False) -> str:
    """
    :param: gn
    :type: gn: bool
    :return sticker_id
    :rtype: sticker_id: str
    .. notes:: get random sticker from DB
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        if gn is False:
            cursor.execute(f'SELECT * FROM Stickers WHERE `set_name`!=\'{GN_Stickers[0]}\' AND'
                           f'`set_name`!=\'{GN_Stickers[1]}\' AND `set_name`!=\'{GN_Stickers[2]}\' AND'
                           f'`set_name`!=\'{GN_Stickers[3]}\' ORDER BY RAND() LIMIT 1')
        else:
            cursor.execute(f"SELECT `item_id` FROM Stickers WHERE `set_name`"
                           f"=\'{random.choice(GN_Stickers)}\'"
                           f" ORDER BY RAND() LIMIT 1")
        return cursor.fetchone()['item_id']

def get_user_karma(user_id: int) -> str:
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT karma FROM Users WHERE user_id=\'{user_id}\'')
        return cursor.fetchone()['karma']

def ban_user(user: str) -> None:
    """
    :param: user
    :type: user: str
    :return None
    .. notes:: ban some user in group
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'INSERT INTO `BlackList` (`user_id`) VALUES (\'{user}\');')
        connection.commit()
    connection.close()


def add_joke(setup, panchline):
    connection = start_connection()
    with connection.cursor() as cursor:
        try:
            cursor.execute(f'INSERT INTO `Joke`(`setup`, `panchline`) VALUES (\'{setup}\', \'{panchline}\');')
            connection.commit()
        except Exception:
            pass
    connection.close()

def check_ban_user(user: str) -> bool:
    """
    :param: user
    :type: user: str
    :return sticker_id
    :rtype: bool
    .. notes:: Check baned user or not
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        return True if cursor.execute(f'SELECT * FROM `BlackList` WHERE user_id LIKE \'{user}\';') == 0 else False


def get_code(name: str) -> [dict, None]:
    """
    :param: name
    :type: name: str
    :return code
    :rtype: code: dict or None
    .. notes:: Get code of programming lang
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT code FROM PasteBin WHERE name LIKE \'{name}\'')
        return cursor.fetchone()


def del_meme(meme_id: str) -> None:
    """
    :param: meme_id
    :type: meme_id: str
    :return None
    .. notes:: Delete meme from DB (for admins)
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'DELETE FROM Memes WHERE id={meme_id}')
        connection.commit()
    connection.close()

def get_all(type_: str) -> list:
    """
    :param: type_
    :type: type_: str
    :rtype list
    .. notes:: get all {some thing} from DB
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT * FROM {type_};')
        return cursor.fetchall()


def add_memes(data_memes: list) -> None:
    """
    :param: data_memes
    :type: data_memes: list
    :rtype None
    .. notes:: Add new memes from daily parser
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        for en, meme in enumerate([meme for meme in data_memes if cursor.execute(f'SELECT * FROM Memes WHERE url LIKE \'{meme}\'') == 0], 1):
            cursor.execute(f'INSERT INTO `Memes`(`url`) VALUES (\'{meme}\');')
            connection.commit()
        else:
            log(f'Мемов добавлено: {en}', 'info')
    connection.close()


def get_forbidden(type_: str) -> str:
    """
    :param: type_
    :type: type_: str
    :return forbidden
    :rtype forbidden: str
    .. notes:: get random forbidden
    """
    r = redis.Redis(host='localhost', port=6379, db=0)
    return r.get(f'{type_}{random.randint(1, int(r.get(f"len_{type_}")))}').decode('utf-8')


def get_doc(id_: str) -> str:
    """
    :param: id_
    :type: id_: str
    :return doc
    :rtype doc: str
    .. notes:: get document from some task of Project Euler
    """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT other FROM Project_Euler WHERE id={id_};')
        return cursor.fetchone()['other']


def get_task_answer(id_: str) -> str:
    """
   :param: id_
   :type: id_: str
   :return task_answer
   :rtype task_answer: str
   .. notes:: get answer from Logic Task
   """
    connection = start_connection()
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT answer FROM Logic_Tasks WHERE id={id_};')
        return cursor.fetchone()['answer']


def get_answer() -> str:
    """
    :return bot_answer
    :rtype bot_answer: str
    .. notes:: get random bot answer from DB
    """
    r = redis.Redis(host='localhost', port=6379, db=1)
    return r.get(f'answer{random.randint(1, int(r.get("len_answer")))}').decode('utf-8')