import requests 
from urllib.request import urlopen
from tqdm import tqdm
from datetime import datetime
import json

with open('token.txt', 'r') as file_object:
    token = file_object.read().strip()

class VkGet:
    def __init__(self, token: str, id):
        self.token = token
        self.URL = "https://api.vk.com/method/photos.get"
        self.params = {
                'access_token': token,
                'v': '5.131',
                'photo_sizes': True,
                'album_id' : 'profile',
                'owner_id': id,
                'extended' : '1',
                'skip_hidden': '1',
                'count': 20,
                'offset': 0
            }
        print("## Получаем фотографии профиля")
        self.links = self.set()

    def max_size(self, res):
        for a in ['w','z','y','x','m','s']:
            for i in res:
                if i['type'] == a:
                    return {
                        'url' : i['url'],
                        'size' : i['type']
                    }
        return

    def photo_requests(self):
        res = requests.get(self.URL, params=self.params)
        return(res.json())

    def set(self, data = []):
        new_set = self.photo_requests()['response']['items']
        if new_set == []:
            print("✅ [Фотографии получены]", end="\n-----\n\n")
            return data
        data += self.filter_set(new_set)
        self.params['offset'] += 20
        print('✅', end="")
        return self.set(data)

    def filter_set(self, res):
        url_data = []
        names = []
        for i in res:
            url = self.max_size(i['sizes'])
            name = f"{i['likes']['count']}"
            if name in names:
                ts = int(i['date'])
                name = f"{name}__{datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d_')}"
                while name in names:
                    name += '_'
            names.append(name)
            url_data.append({
            "name": f"{name}.png",
            'url': url['url'],
            'size': url['size']
            })
        return url_data


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def create_folder(self, folder):
        print("## Создаем папку на Яндекс.Диск")
        create_url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_headers()
        params = {"path": folder}
        response = requests.put(create_url, headers = headers, params = params)
        if response.status_code == 201:
            print("✅ Папка создана")
        else: 
            print(response.json()['message'], end="\n-----\n\n")
        return 

    def upload_yandex(self, url, y_path):
        try:
            url_upload = self.get_upload_link(y_path).get("href","")
            img = urlopen(url)
            response = requests.put(url_upload,  files={'file':img})
            if response.status_code == 201:
                name = y_path.split("/")
                print(f' файл {name[1]} загружен')
        except:
                print(" файл не загружен")
                return False
        return True

    def get_upload_link(self, y_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": y_path, "overwrite": "true" }
        response = requests.get(upload_url, headers = headers, params = params)
        return response.json()

    def put_photos(self, links, folder ):
        print('## Начинаем загрузку')
        count = 0
        while len(links) < count or count < 1 :
            print(f'Доступно {len(links)} фотографий для загрузки')
            count = int(input("Сколько фотографий загрузить? "))
        for i in tqdm(links[:count]):
            check_upload = self.upload_yandex(i['url'], f"{folder}/{i['name']}")
            if not check_upload:
                links.remove(i)
        return links
        print('\n✅ Загрузка завершена', end="\n-----\n\n")

    def data_json(self, links):
        print('## Начинаем подготовку отчета')
        lister = []
        for i in tqdm(links):
            lister.append({'name': i['name'], 'size': i['size']})
        with open('data.json', 'w') as f:
            json.dump(lister, f)
        print('\n✅JSON файл с данными о фото загружен локально')


if __name__ == '__main__':
    folder_name = "folder_vk"
    vk_id = input("Введите id пользователя VK: ")
    yandex_token = input("Введите свой токен с полегона: ")

    vk = VkGet(token, vk_id)
    disk = YaUploader(yandex_token)

    disk.create_folder(folder_name)
    report = disk.put_photos(vk.links, folder_name)
    disk.data_json(report)
