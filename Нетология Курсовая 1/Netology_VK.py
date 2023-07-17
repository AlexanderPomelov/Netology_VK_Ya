import json
import requests
import configparser

from loguru import logger
from datetime import datetime


class VK:

    def __init__(self, user_id, version='5.131'):
        logger.info("Начало работы программы")
        self.config = configparser.ConfigParser()
        self.config.read('settings.ini')
        self.token = self.config['VK']['tokenvk']
        self.user_id = input(f'Введите ID пользователя: {user_id}')
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def id_screen_name(self):
        """Метод получения ID пользователя если используется screen_name"""
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.user_id}
        response = requests.get(url, params={**self.params, **params})
        response_id = response.json()
        for profile in response_id['response']:
            user_id = profile['id']
        return user_id

    def users_info(self):
        """Метод получения информации о пользователе"""
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id_screen_name()}
        self.closed = False
        response = requests.get(url, params={**self.params, **params})
        response_ = response.json()
        for profile in response_['response']:
            self.info_profile = f'ID пользователя: {profile["id"]}\n' \
                                f'Имя пользователя: {profile["first_name"]}\n' \
                                f'Фамилия пользователя: {profile["last_name"]}\n' \
                                f'Может ли текущий пользователь видеть профиль: {profile["can_access_closed"]}\n' \
                                f'Скрыт ли профиль пользователя настройками приватности: {profile["is_closed"]}'
            self.info_closed = f'ID пользователя: {profile["id"]}\n' \
                               f'Имя пользователя: {profile["first_name"]}\n' \
                               f'Фамилия пользователя: {profile["last_name"]}\n' \
                               f'Может ли текущий пользователь видеть профиль: {profile["can_access_closed"]}\n'
            if profile['can_access_closed'] == False and profile['is_closed'] == True:
                self.closed = True
                return self.info_closed
            return self.info_profile

    def photos_for_download(self):
        """Метод получения имени и url фотографии пользователя"""
        url = 'https://api.vk.com/method/photos.get'
        edited_names = []
        final_json = []
        album = input(f'Откуда хотите скачать фотографии?\n'
                      f'>> Введите wall -- для загрузки фотографий со стены\n'
                      f'>> Введите profile -- для загрузки фотографий профиля\n'
                      f'>> Введите: ').lower()
        while True:
            if album == 'wall' or album == 'profile':
                print(f'Вы выбрали загрузку: {album}')
                break
            else:
                print('Вы ввели не существующий альбом, повторите еще раз')
                exit()
        count = input('Введите количество фотографий для загрузки: ')
        self.users_info()
        finished_list = []
        params = {'owner_id': self.id_screen_name(),
                  'v': '5.131', 'album_id': album,
                  'rev': '1', 'extended': '1',
                  'photo_sizes': '1', 'count': count}
        response_photo = requests.get(url, params={**self.params, **params})
        response_json = response_photo.json()
        if self.closed == True:
            print('Профиль закрыт, загрузка невозможна')
        elif response_json['response']['count'] != 0:
            for photos in response_json['response']['items']:
                name_and_url = {}
                name = f'{str(photos["likes"]["count"])}'
                date = datetime.fromtimestamp(photos["date"]).strftime("%Y-%m-%d")
                size = max(photos['sizes'], key=lambda x: (x['width'], x['height']))
                if name in edited_names:
                    name_and_url['name'] = f'{name}_{date}.jpg'
                else:
                    name_and_url['name'] = f'{name}.jpg'
                edited_names.append(name)
                name_and_url['size'] = size['type']
                name_and_url['url'] = size['url']
                finished_list.append(name_and_url)
                final_json.append({'file_name': name_and_url['name'],
                                   'size': size['type']})
            result = json.dumps(final_json, indent=2)
            with open('result.json', 'a', encoding='utf-8') as f:
                f.write(result)
            return finished_list
        elif response_json['response']['count'] == 0:
            print('Фотографий для загрузки у данного пользователя нет')
            exit()


class Ya_disk:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('settings.ini')
        self.token_yandex = self.config['Yandex']['tokenyandex']

    def create_folder(self, id_screen_name):
        """Метод создания папки на Я.Диске с ID пользователя VK"""
        try:
            self.folder_name = id_screen_name
            url_folder_name = 'https://cloud-api.yandex.net/v1/disk/resources'
            params = {'path': f'ID={self.folder_name}',
                      'url': url_folder_name}
            headers = {'Authorization': self.token_yandex}
            response_folder = requests.put(url_folder_name, headers=headers, params=params)
            logger.debug(f'Создана папка с именем ID={id_screen_name}')
            return self.folder_name
        except Exception as e:
            logger.error(f'При создании папки произошла ошибка:{e}')

    def download_photo(self, photos_for_download, folder_name):
        """Метод загрузки фотографии на Я.Диск из полученных данных"""
        try:
            url_for_yandex = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            for upload in photos_for_download:
                file_name_upload = str(upload['name'])
                url_for_upload = upload['url']
                params = {'path': f'ID={folder_name}/{file_name_upload}', 'url': url_for_upload}
                headers = {'Authorization': self.token_yandex}
                response_ya = requests.post(url_for_yandex, headers=headers, params=params)
                if response_ya.status_code == 409:
                    logger.error(f'Ошибка {response_ya.status_code} Указанного пути path не существует')
                elif 200 <= response_ya.status_code <= 300:
                    logger.debug(f'Файл с именем {file_name_upload} успешно загружен ')
                else:
                    logger.debug(f'Response Status Code: {response_ya.status_code}')
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
        logger.info("Завершение работы программы")

    logger.add("app.log", rotation="1 week", level="DEBUG")


if __name__ == '__main__':
    vk = VK(user_id='')

    ya = Ya_disk()
    folder_name = ya.create_folder(vk.id_screen_name())  # создает папку на Я.Диске с именем ID пользователя
    ya.download_photo(vk.photos_for_download(), folder_name)  # загружает фотографии в созданную папку

# pip install -r requirements.txt   установка зависимостей python
