#!/usr/bin/env python3
import socket
import ssl
import base64
from mimetypes import guess_type
import re

SMTP_ADDRESS = 'smtp.yandex.ru', 465
CRLF = "\r\n"
LOGIN = ''
RCPT_TO = ''
PASS = ''

class SMTPClient:
    BOUNDARY = "--=================sq22d"
    UPPER_HEADER = 'Content-Type: multipart/mixed; boundary="{}"\r\n'.format(BOUNDARY[2:])
    MIME_VERSION = "MIME-Version: 1.0" + CRLF
    ATTACHMENT_TEMPLATE = '\r\nContent-Disposition: attachment; ' \
                          'attachment_name="{}"\nContent-Transfer-Encoding: ' \
                          'base64\nContent-Type: {}; name="{}"\n\n\n'

    def __init__(self, address):
        self.__address = address
        self.__socket = None

    def start_conn(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket = ssl.wrap_socket(sock)
            self.__socket.settimeout(3)
            self.__socket.connect(self.__address)
        except:
            print("Error: no connection")
            exit(1)

    def send_cmd(self, command):
        self.__socket.send(command + b'\n')
        return self.receive_data()

    def send_message(self, LOGIN, RCPT_TO, subject, text, attach):
        self.send_cmd(self.create_message(LOGIN, RCPT_TO, subject, text, attach))

    def create_message(self, LOGIN, RCPT_TO, subject, text, attach):
        msg = self.fill_header(LOGIN, RCPT_TO, subject)
        msg += self.BOUNDARY + CRLF
        msg += self.mime_message(text)

        for file in attach:
            if file is None:
                continue
            msg += '\r\n'
            msg += self.add_attachment(file) + CRLF

        msg += self.BOUNDARY + "--" + '\r\n.' + CRLF
        return msg.encode()

    def mime_message(self, text):
        return 'Content-Type: text/plain; charset="utf-8"\r\n' \
                      'MIME-Version: 1.0\r\n' \
                      'Content-Transfer-Encoding: 8bit\r\n\r\n' \
               + text

    def fill_header(self, LOGIN, RCPT_TO, subject):
        return self.UPPER_HEADER \
               + self.MIME_VERSION + \
               f'From: {LOGIN}\n' \
               f'To: {RCPT_TO}\n' \
               f'Subject: {subject}\n\r\n'

    def add_attachment(self, attachment_name):
        header = self.BOUNDARY
        header += self.ATTACHMENT_TEMPLATE.format(attachment_name, guess_type(attachment_name)[0], attachment_name)
        with open(attachment_name, 'rb') as f:
            data = base64.b64encode(f.read())
        header += data.decode('utf8') + '\r\n'
        return header

    def receive_data(self):
        data = b''
        try:
            while True:
                segment = self.__socket.recv(1024)
                if segment:
                    data += segment
                else:
                    break
        finally:
            return data.decode()

    def stop(self):
        self.__socket.close()

    def __enter__(self):
        self.start_conn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    with open('mail.txt', 'r') as f:
        text=""
        for line in f.readlines():
            if re.search("\.+\s*",line):
                text += "." + line
            else:
                text + line

    with SMTPClient(SMTP_ADDRESS) as client:
        print(client.receive_data())
        print(client.send_cmd(b'EHLO test'))
        print(client.send_cmd(b'AUTH LOGIN'))
        print(client.send_cmd(base64.b64encode(LOGIN.encode())))
        print(client.send_cmd(base64.b64encode(PASS.encode())))

        print(client.send_cmd(b'MAIL FROM:' + LOGIN.encode()))
        print(client.send_cmd(b'RCPT TO:' + RCPT_TO.encode()))
        print(client.send_cmd(b'DATA'))
        print(client.send_message(LOGIN, RCPT_TO, 'HI', text, ['mail.txt']))


if __name__ == '__main__':
    main()
