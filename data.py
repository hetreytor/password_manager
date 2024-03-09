import kuzn
from dataclasses import dataclass
import database
from datetime import datetime, time


class NoteData:
    _VERIFICATION_PHRASE: str = "_секретнаяфраза_"

    @dataclass
    class SecretData:
        user_name: str
        note_name: str
        login: str
        password: str
        description: str
        list_time_window: str
        pincode_error_counter: int
        enc_verification_phrase: str

        def __init__(self, user_name: str = None, note_name: str = None, login: str = None, password: str = None,
                     description: str = None, list_time_window: str = None, pincode_error_counter: int = 5, enc_verification_phrase: str = None):
            self.user_name = user_name
            self.note_name = note_name
            self.login = login
            self.password = password
            self.description = description
            self.list_time_window = list_time_window
            self.pincode_error_counter = pincode_error_counter
            if enc_verification_phrase:
                self.enc_verification_phrase = enc_verification_phrase

    @staticmethod
    def encrypt(secret_data: SecretData, pincode, master_key):
        pincode = kuzn.getKeys(pincode)
        login_pin = kuzn.encrypt(secret_data.login, pincode)
        password_pin = kuzn.encrypt(secret_data.password, pincode)
        description_pin = kuzn.encrypt(secret_data.description, pincode)
        list_time_window_pin = kuzn.encrypt(secret_data.list_time_window, pincode)

        enc_verification_phrase_pin = kuzn.encrypt(NoteData._VERIFICATION_PHRASE, pincode)

        master_key = kuzn.getKeys(master_key)
        login_enc = kuzn.encrypt(login_pin, master_key)
        password_enc = kuzn.encrypt(password_pin, master_key)
        description_enc = kuzn.encrypt(description_pin, master_key)
        list_time_window_enc = kuzn.encrypt(list_time_window_pin, master_key)
        enc_verification_phrase_enc = kuzn.encrypt(enc_verification_phrase_pin, master_key)

        return login_enc, password_enc, description_enc, list_time_window_enc, enc_verification_phrase_enc

    @staticmethod
    def __decrypt_phrase(phrase, pincode, master_key):
        tmp_key = kuzn.decrypt(phrase, master_key).rstrip('\x00')
        dec_phrase = kuzn.decrypt(tmp_key, pincode).rstrip('\x00')
        if NoteData._VERIFICATION_PHRASE == dec_phrase:
            return True
        else:
            return False

    @staticmethod
    def __check_window_time(note_time) -> bool:

        try:
            time_windows = note_time.split(";")
        except:
            time_windows = note_time + ";"
            time_windows = time_windows.split(";")
        login_time = NoteData.__current_time()
        for time_window in time_windows:
            start_time, end_time = NoteData.__trans_str_into_time(time_window)
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
    def __decrypt_time(note_time, pincode, master_key):
        tmp_key = kuzn.decrypt(note_time, master_key).rstrip('\x00')
        dec_time = kuzn.decrypt(tmp_key, pincode).rstrip('\x00')
        if NoteData.__check_window_time(dec_time):
            return True
        else:
            return False

    @staticmethod
    def __decrypt(secret_data: SecretData, pincode, master_key):
        pincode = kuzn.getKeys(pincode)
        master_key = kuzn.getKeys(master_key)
        if not NoteData.__decrypt_phrase(phrase := secret_data.enc_verification_phrase, pincode, master_key):
            NoteData.__decrease_pincode_counter(secret_data)
            return False
        if not NoteData.__decrypt_time(secret_data.list_time_window, pincode, master_key):
            NoteData.__decrease_pincode_counter(secret_data)
            return False

        login = kuzn.decrypt(kuzn.decrypt(secret_data.login, master_key).rstrip('\x00'), pincode).rstrip('\x00')
        password = kuzn.decrypt(kuzn.decrypt(secret_data.password, master_key).rstrip('\x00'), pincode).rstrip('\x00')
        description = kuzn.decrypt(kuzn.decrypt(secret_data.description, master_key).rstrip('\x00'), pincode).rstrip('\x00')
        NoteData.__increase_pincode_counter(secret_data)
        return {"Логин": login, "пароль": password, "Описание": description}


    @staticmethod
    def __increase_pincode_counter(secret_data: SecretData):
        query = f"""UPDATE secret_data SET pincode_error_counter = '{5}' 
                WHERE user_name = '{secret_data.user_name}' AND note_name = '{secret_data.note_name}';"""
        database.db_push(query)

    @staticmethod
    def __block_notes(user_name, note_name):
        return ...

    @staticmethod
    def __decrease_pincode_counter(secret_data: SecretData):
        secret_data.pincode_error_counter -= 1
        query = f"""UPDATE secret_data SET pincode_error_counter = '{secret_data.pincode_error_counter}' 
        WHERE user_name = '{secret_data.user_name}' AND note_name = '{secret_data.note_name}';"""
        database.db_push(query)
        #добавить изменение количества пинкодов в базу
        if secret_data.pincode_error_counter > 0:
            return True
        else:
            return False

    @staticmethod
    def __get_on_database(user_name: str, note_name: str):
        query = f"""SELECT * FROM secret_data WHERE user_name = '{user_name}' AND note_name = '{note_name}';"""
        data = database.db_get_all(query=query)[0]
        if data[7] <= 0:
            return False
        data = NoteData.SecretData(data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
        return data

    @staticmethod
    def input_in_database(secret_data: SecretData, pincode, master_key):
        login, password, description, time, enc_verification_phrase = NoteData.encrypt(secret_data, pincode, master_key)
        query = f"""INSERT INTO secret_data (user_name, note_name, login, password, description, time,  pincode_error_counter, enc_verification_phrase) 
        VALUES ('{secret_data.user_name}', '{secret_data.note_name}', '{login}', '{password}', '{description}','{time}', '{secret_data.pincode_error_counter}', '{enc_verification_phrase}');"""
        database.db_push(query=query)

    @staticmethod
    def get_note(user_name: str, note_name: str, pincode: str, master_key: str):
        secret = NoteData.__get_on_database(user_name, note_name)
        if not secret:
            return "Запись заблокирована"
        if decrypt := NoteData.__decrypt(secret, pincode, master_key):
            return decrypt
        else:
            return "Неверный пинкод"

    @staticmethod
    def get_all_notes_name(user_name: str):
        query = f"""SELECT * FROM secret_data WHERE user_name = '{user_name}';"""
        notes = database.db_get_all(query)
        try:
            return [note_name[2] for note_name in notes]
        except TypeError:
            return False




"""CREATE TABLE secret_data ( id SERIAL PRIMARY KEY,
user_name TEXT,
note_name VARCHAR CONSTRAINT unique_note_name UNIQUE NOT NULL,
login TEXT,
password TEXT,
description TEXT,
pincode_error_counter INT CONSTRAINT pincode_not_null NOT NULL,
enc_verification_phrase TEXT CONSTRAINT unique_enc_phrase UNIQUE NOT NULL);
"""
