import _pystribog as pystribog
import binascii
import database
from data import NoteData
from dataclasses import dataclass
from datetime import datetime, time


SALT = "salt"


class Login:
    @dataclass
    class AuthData:
        username: str
        user_password: str
        list_time_window: str

        def __init__(self, username: str = None, user_password: str = None, list_time_window: str = None):
            self.username = username
            self.user_password = user_password
            self.list_time_window = list_time_window

    @staticmethod
    def add_time_window(data: AuthData, new_time_window: str) -> None:
        if data.list_time_window is None:
            data.list_time_window = f"{new_time_window}"
        else:
            data.list_time_window += f";{new_time_window}"

    @staticmethod
    def __hash_password(password: str) -> str:
        h = pystribog.StribogHash(pystribog.Hash256)
        h.update(f"{password + SALT}")
        res = h.digest()
        return binascii.hexlify(res).decode("utf-8")

    @staticmethod
    def __check_window_time(data: AuthData) -> bool:
        time_windows = data.list_time_window.split(";")
        login_time = Login.__current_time()
        for time_window in time_windows:
            start_time, end_time = Login.__trans_str_into_time(time_window)
            if end_time < start_time:
                if end_time <= login_time <= start_time:
                    continue
                else:
                    return True
            if start_time <= login_time <= end_time:
                return True
        return False

    @staticmethod
    def __current_time() -> time:
        return time(datetime.now().hour, datetime.now().minute)

    @staticmethod
    def __trans_str_into_time(string: str) -> tuple:
        substrings = string.split("-")
        if int(substrings[0].split(":")[0]) >= 24:
            first_hour = 0
        else:
            first_hour = int(substrings[0].split(":")[0])

        if int(substrings[0].split(":")[1]) >= 60:
            first_minutes = 0
        else:
            first_minutes = int(substrings[0].split(":")[1])

        if int(substrings[1].split(":")[0]) >= 24:
            second_hour = 0
        else:
            second_hour = int(substrings[1].split(":")[0])

        if int(substrings[1].split(":")[1]) >= 60:
            second_minutes = 0
        else:
            second_minutes = int(substrings[1].split(":")[1])

        return time(hour=first_hour, minute=first_minutes), time(hour=second_hour, minute=second_minutes)

    @staticmethod
    def input_in_database(auth_data: AuthData) -> None:
        query = f"""INSERT INTO login_data (login, password, time) VALUES ('{auth_data.username}', 
        '{Login.__hash_password(auth_data.user_password)}', '{auth_data.list_time_window}');"""
        database.db_push(query=query)

    @staticmethod
    def __get_on_database(login: str) -> AuthData:
        query = f"""SELECT * FROM login_data WHERE login = '{login}';"""
        data = database.db_get_all(query=query)[0]
        return Login.AuthData(data[1], data[2], data[3])

    @staticmethod
    def check_credentials(login: str, password: str):
        try:
            loaded_data = Login.__get_on_database(login)
        except TypeError:
            return False

        if not loaded_data:
            return False
        if Login.__hash_password(password) != loaded_data.user_password:
            return False
        if not Login.__check_window_time(data=loaded_data):
            return False

        return True


"""CREATE TABLE login_data ( id SERIAL PRIMARY KEY,
login VARCHAR CONSTRAINT unique_login UNIQUE NOT NULL,
password TEXT CONSTRAINT not_null_password NOT NULL,
time VARCHAR);
"""



