from constants import TCP_IP, TCP_PORT, REGEX_DIR, REGEX_EXT
import os
import pickle
import re
from socket import socket, AF_INET, SOCK_STREAM


# Главная функция
def main():
    # Вводим необходимую директорию
    directory = input("Please, input the desired directory (ex. '/home/<username>/<folder>/.../'): ")
    while True:
        # Если директория соответствует регулярному выражению
        if re.match(REGEX_DIR, directory) is not None:
            # Заканчиваем ввод
            break
        # Если ошибка
        else:
            directory = input("You made a mistake! Please, input the correct desired directory (ex. '/home/<username>/<folder>/...'): ")
    #Вводим необходимое расширение
    extension = input("Please, input the desired extension (ex. '.<extension>'): ")
    while True:
        # Если расширение соответствует регулярному выражению
        if re.match(REGEX_EXT, extension) is not None:
            # Если ошибка
            break
        else:
            extension = input("You made a mistake! Please, input the correct desired extension (ex. '.<extension>'): ")
    dir_ext_str = directory + '*' + extension

    # Инициализируем клиентский сокет: AF_INET для IPv4, SOCK_STREAM для TCP
    client_socket = socket(AF_INET, SOCK_STREAM)
    # Подключаемся к серверу
    client_socket.connect((TCP_IP, TCP_PORT))
    # Конвертируем целочисленный размер строки с директорией и расширением в строку,
    # дополняем справа строку до 32 байт, конвертируем результат в байтстроку
    size_dir_ext_str = str(len(dir_ext_str)).ljust(32).encode()
    # Отправляем размер строки с директорией и расширением на сервер
    client_socket.send(size_dir_ext_str)
    # Отправляем строку с поисковым запросом на сервер
    client_socket.send(dir_ext_str.encode())
    # Получаем размер pickle-объекта, содержащий список найденных имен файлов в необходимом каталоге
    size_pickle_files_str = client_socket.recv(32)
    # Декодируем байтстроку в строку
    size_pickle_files_str = size_pickle_files_str.decode()
    # Конвертируем размер pickle-объекта в целочисленный тип
    size_pickle_files = int(size_pickle_files_str[:size_pickle_files_str.find(' ')])
    # Получаем найденные файлы на сервере в виде потока байт
    pickle_files = client_socket.recv(size_pickle_files)
    # Преобразовываем поток байтов в список
    files = pickle.loads(pickle_files)
    # Печатаем в консоль клиента список с файлами, если они были найдены.
    if not files:
        print("\nUnfortunately, the server does not have the necessary files. Try again later!\n")
    else:
        print(f"\nFound files on server: ")
        for file in files:
            print(file)
        print()
        # Создадим директорию 'downloads', если ее нет в папке со скриптом клиента
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

    # Если файлы в директории, определенной клиентом найдены
    if files:
        for file in files:
            # Получаем размер файла в байтстроке
            file_size = client_socket.recv(32)
            # Декодируем строку из байтстроки в строку
            file_size = file_size.decode()
            # Конвертируем размер файла в целочисленный тип
            file_size = int(file_size[:file_size.find(' ')])
            # Путь и имя загружаемого с сервера файла
            local_file_name = os.path.join('downloads', file.split('/')[-1])
            # Открывае файл для записи, with позволяет косвеено закрывать поток, после завершения записи в файл
            with open(local_file_name, 'wb') as f:
                print(f"File '{file}' is opened for writing from server.")
                # Размер буфера
                buffer_size = 2048
                # Если загружаемый файл не пуст
                while file_size > 0:
                    # Если размер файла, меньше, чем размер буфера
                    if file_size < buffer_size:
                        # Размер буфера равен полученному размеру файла
                        buffer_size = file_size
                    #print('Receiving data...')
                    # Получаем информацию с сервера
                    data = client_socket.recv(buffer_size)
                    #print('Data: %s' % data)
                    # Запись полученных байтстрок в файл на устройстве клиента
                    f.write(data)
                    # Вычитаем из размера файла, размер полученных байтстрок с сервера
                    file_size -= len(data)
                print(f"File '{file.split('/')[-1]}' is closed.\n")
        print("The files obtaining was completed successfully.")
    client_socket.close()
    print("Connection is closed.")

if __name__ == '__main__':
    main()