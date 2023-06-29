import requests
import json
from pprint import pprint
from loguru import logger


class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    """Метод получения информации о пользователе"""
    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
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

    """Метод получения фотографий от пользователя"""
    def photos_get(self,user_id, token_yandex):
        logger.info("Начало работы программы")
        url = 'https://api.vk.com/method/photos.get'
        self.id = user_id
        self.token_yandex = token_yandex
        self.file_names =[]
        self.likes_and_url = []
        self.final_json = []
        self.users_info()
        params = {'owner_id': self.id,
                  'v': '5.131','album_id': 'profile',
                  'rev': '1', 'extended': '1',
                  'photo_sizes': '1', 'count': '3'}
        if self.closed == True:
            return logger.debug(f"Профиль закрыт, загрузка фото невозможна")
        response_photo = requests.get(url, params={**self.params, **params})
        response_ = response_photo.json()
        if response_['response']['count'] == 0:
            return logger.debug(f'Фотографий для загрузки у данного пользователя нет')
        for photos in response_['response']['items']:
            size = photos['sizes'][-1]
            self.file_names.append(str(photos['likes']['count']) + '.jpg')
            prev_name = ""
            for i in range(len(self.file_names)):
                if self.file_names[i] == prev_name:
                    self.file_names[i] = str(photos['likes']['count']) +'_' + str(photos['date']) +  '.jpg'
                prev_name = self.file_names[i]

            self.likes_and_url.append({'date': photos['date'],
                                       'likes': photos['likes']['count'],
                                       'file_name' : prev_name,
                                       'size' : size['type'],
                                       'url': size['url']})
            self.final_json.append({'file_name': prev_name, 'size': size['type']})
        result = json.dumps(self.final_json, indent=2)


        # запись результата в json
        with open('result.json', 'a', encoding='utf-8') as f:
            try:
                f.write(result)
                logger.debug(f'Результат записан в json')
            except Exception as e:
                logger.error(f"Произошла ошибка: {e}")

        #создание папки
        try:
            url_folder_name = 'https://cloud-api.yandex.net/v1/disk/resources'
            params = {'path': f'ID={user_id}', 'url': url_folder_name}
            headers = {'Authorization': self.token_yandex}
            response_folder = requests.put(url_folder_name, headers=headers, params=params)
            logger.debug(f'Создана папка с именем ID пользователя')
        except Exception as e:
            logger.error(f"При создании папки произошла ошибка: {e}")

        #запись фотографий в созданную папку
        try:
            url_for_yandex = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            for upload in self.likes_and_url:
                file_name_upload = str(upload['file_name'])
                url_for_upload = upload['url']
                params = {'path': f'ID={user_id}/{file_name_upload}', 'url': url_for_upload}
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


with open(r'tokenvk.txt') as file_1, open(r'tokenyandex.txt') as file_2:
    access_token = file_1.readline()
    token_yandex = file_2.readline()

id_VK = input(f'Введите ID пользователя социальной сети ВКонтакте: ')
user_id = id_VK
vk = VK(access_token, user_id)

#Вызов метода класса VK
vk.photos_get(user_id, token_yandex)


#pip install -r requirements.txt   установка зависимостей python