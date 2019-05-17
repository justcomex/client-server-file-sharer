from constants import TCP_IP, TCP_PORT
import glob
import os
import pickle
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread


class ClientThread(Thread):
    # Констркетор класа ClientThread, который является наследником класса Thread
    def __init__(self, ip, port, sock):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        print("New thread started for " + ip + ":" + str(port))

    # Переопредялем метод класса Thread для того, чтобы использовать start() в main()
    def run(self):
        # Получаем размер строки с директорий и расширением
        size_str = self.sock.recv(32)
        # Декодируем байтстроку в строку
        size_str = size_str.decode()
        # Конвертируем размер строки в целочисленный тип
        size_str = int(size_str[:size_str.find(' ')])
        # Получаем директорию и расширение для поиска необходимых файлов
        dir_ext_str = self.sock.recv(size_str)
        print(f"Search directory: {dir_ext_str.decode()}")
        # Ищем требуемые файлы в директории, указанной клиентом
        files = glob.glob(dir_ext_str.decode())
        # Формируем список как последовательность байтов для того,
        # чтобы на стороне клиента можно было снова его преобразовать в список
        pickle_files = pickle.dumps(files)
        # Получаем размер pickle-объекта, представляющий список найденных имен файлов
        size_pickle_files = len(pickle_files)
        # Конвертируем целочисленный размер файла в строку, дополняем справа строку до 32 байт, конвертируем результат в байтстроку
        size_pickle_files_str = str(size_pickle_files).ljust(32).encode()
        # Отправляем размер pickle-объекта
        self.sock.send(size_pickle_files_str)
        # Отправляем список файлов
        self.sock.send(pickle_files)
        # Если файлы в директории, определенной клиентом не найдены
        if not files:
            print("Unfortunately, the server does not have the necessary files for client. Goodbye!\n")
        # Если файлы найдены
        else:
            print(f"\nFound files on server: ")
            for file in files:
                print(file)
            print()
            # Если файлы в директории, определенной клиентом найдены
            if files:
                # Для имени каждого найденного файла в списке с именами найденных файлами
                for file in files:
                    # Получаем размер отправляемого файла
                    file_size = os.path.getsize(file)
                    # Конвертируем целочисленный размер файла в строку, дополняем справа строку до 32 байт, конвертируем результат в байтстроку
                    file_size_str = str(file_size).ljust(32).encode()
                    # Отправлем размер файла клиенту
                    self.sock.send(file_size_str)
                    # Открываем файл с именем file
                    f = open(file, 'rb')
                    print(f"File {file} is opened for sending.")
                    while True:
                        # Читаем file_size символов из потока в buf
                        buf = f.read(file_size)
                        # Пока buf не пуст
                        while (buf):
                            # Отправляем байтстроку клиенту
                            self.sock.send(buf)
                            # Вывод байтстрок в коноль
                            #print('Sending: ',repr(buf))
                            # Читаем file_size символов из потока в buf
                            buf = f.read(file_size)
                        # Если buf пуст
                        if not buf:
                            # Закрываем файл
                            f.close()
                            print(f'File {file} is closed.\n')
                            break
                print("The files sending was completed successfully.")
                # Закрываем сокет
        self.sock.close()
        print("Connection is closed.\n")
        print("\nWaiting for incoming connections...\n")


# Главная функция
def main():
    try:
        # Инициализируем серверный сокет: AF_INET для IPv4, SOCK_STREAM для TCP
        server_socket = socket(AF_INET, SOCK_STREAM)
        # Устанавливаем флаг на сокете:
        # SO_REUSEADDR -- позволяет нескольким приложениям «слушать» сокет
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Cвязываеv сокет с конкретным адресом
        server_socket.bind((TCP_IP, TCP_PORT))
        # список с потоками, один поток = один клиент
        threads = []

        while True:
            # Разрешаем серверу принимать соединения. Максимальное количество подключений в очереди = 5
            server_socket.listen(5)
            print("Waiting for incoming connections...\n")
            # Принять соединение
            connection, (ip, port) = server_socket.accept()
            print("Got connection from", (ip, port))
            # Инициализируем клиентский поток
            new_client_thread = ClientThread(ip, port, connection)
            # Запускаме поток
            new_client_thread.start()
            # Добавляем текущий клиентский поток в список всех потоков
            threads.append(new_client_thread)

        for t in threads:
            # Ожидаем, пока поток не завершится;
            # это блокирует вызывающий поток до тех пор, пока поток, метод join() которого вызывается, не завершится
            t.join()
    # Обработка прерывания KeyboardInterrupt в случае CTRL + Z
    except KeyboardInterrupt:
        print("\nThe server has completed its work.")
        os._exit(0)

if __name__ == '__main__':
    main()