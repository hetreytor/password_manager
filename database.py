import psycopg2


database = "host='127.0.0.1' port=5432 dbname='postgres' user='postgres' password='postgres'"


def db_get(query):
    try:
        connection = psycopg2.connect(database)
        cursor_ = connection.cursor()
        cursor_.execute(query)
        response = cursor_.fetchone()
        cursor_.close()
        connection.close()
        if response:
            return response[0]
        else:
            return False
    except psycopg2.OperationalError as e:
        return False


def db_get_all(query):
    try:
        connection = psycopg2.connect(database)
        cursor_ = connection.cursor()
        cursor_.execute(query)
        response = cursor_.fetchall()
        cursor_.close()
        connection.close()
        if response:
            return response
        else:
            return False
    except psycopg2.OperationalError as e:
        return False


def db_push(query):
    try:
        connection = psycopg2.connect(database)
        cursor_ = connection.cursor()
        cursor_.execute(query)
        connection.commit()
        cursor_.close()
        connection.close()
    except psycopg2.OperationalError as e:
        return False
    except psycopg2.IntegrityError as err:
        if err.pgerror == 'psycopg2.errors.UniqueViolation':
            return False
