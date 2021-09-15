import json
import requests
import urllib.parse

class University:
    def __init__(self):
        self.context = None
        self.messages_to_delete = []
        self.messages_to_show = {}
        self.new_update = False
        self.msg_id = None
        self.session = requests.Session()

    def login(self, username, password):
        url = "https://lk.samgtu.ru/site/login"

        safe_string = urllib.parse.quote_plus(password)
        payload = 'LoginForm%5Busername%5D={log}&LoginForm%5Bpassword%5D={passw}&LoginForm%5BrememberMe%5D=0&LoginForm%5BrememberMe%5D=1'.format(
            log=username, passw=safe_string)
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Yandex";v="90"',
            'sec-ch-ua-mobile': '?0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://lk.samgtu.ru/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://lk.samgtu.ru/site/login',
            'Accept-Language': 'ru,en;q=0.9'
        }

        result = self.session.request("POST", url, headers=headers, data=payload)
        return 'current-user__name' in result.text

    def get_calendar_data(self, start, end):
        url = 'https://lk.samgtu.ru/api/common/distancelearning?start={start}T00%3A00%3A00%2B04%3A00&end={end}T00%3A00%3A00%2B04%3A00'.format(
            start=start, end=end)

        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Yandex";v="90"',
            'sec-ch-ua-mobile': '?0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://lk.samgtu.ru/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://lk.samgtu.ru/site/login',
            'Accept-Language': 'ru,en;q=0.9',
        }
        response = self.session.request("GET", url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def get_page_to_parse(self, url):
        url = 'https://lk.samgtu.ru' + url

        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Yandex";v="90"',
            'sec-ch-ua-mobile': '?0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://lk.samgtu.ru/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://lk.samgtu.ru/site/login',
            'Accept-Language': 'ru,en;q=0.9',
        }
        response = self.session.request("GET", url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None

    def get_tasks_to_parse(self, id):
        url = 'https://lk.samgtu.ru/api/common/distancelearningtaskresults?t_id=' + id

        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Yandex";v="90"',
            'sec-ch-ua-mobile': '?0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://lk.samgtu.ru/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://lk.samgtu.ru/site/login',
            'Accept-Language': 'ru,en;q=0.9',
        }
        response = self.session.request("GET", url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def get_messages_to_parse(self, ids, mark_as_read):
        url = 'https://lk.samgtu.ru/api/common/distancelearningresults?dl_id={dl_id}&dlp_id={dlp_id}&sp_id={sp_id}'.format(
            dl_id=ids[0], dlp_id=ids[1], sp_id=ids[2])
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Yandex";v="90"',
            'sec-ch-ua-mobile': '?0',
            'Upgrade-Insecure-Requests': '1',
            'Origin': 'https://lk.samgtu.ru/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://lk.samgtu.ru/site/login',
            'Accept-Language': 'ru,en;q=0.9',
        }
        if mark_as_read:
            new_url = 'https://lk.samgtu.ru/distancelearning/distancelearningresults/create?dl_id={dl_id}&dlp_id={dlp_id}&sp_id={sp_id}&read=1'.format(
                dl_id=ids[0], dlp_id=ids[1], sp_id=ids[2])
            self.session.request("GET", new_url, headers=headers)

        response = self.session.request("GET", url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.text)
        return None
