import time
import calendar
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import datetime

def select_month(year: int, month: int):
    """空室状況フォームでの月の選択"""

    date = str(year) + ',' + str(month)
    Select(driver.find_element_by_id('boxCalendarSelect')).select_by_value(date)
    time.sleep(2)


def get_vacancy_status(driver, year: int, month: int):
    """指定した月の空室状況を返す"""

    _, f = calendar.monthrange(year, month)
    status_lists = {}
    for i in range(1, f + 1):
        date = str(year) + str(month).rjust(2, '0') + str(i).rjust(2, '0')
        cal_date = driver.find_element_by_class_name('cal_' + date)
        status = cal_date.text.split('\n')
        status_lists[date] = status

    # driver.find_element_by_xpath("//img[@src='/cgp/images/jp/pc/btn/btn_close_06.png']").click()
    driver.find_element_by_css_selector('.close01.closeModal.vacancy').click()

    return status_lists


def select_room(driver, room):
    """指定した部屋の空室状況確認画面へ遷移する"""
    room_class = '.button.next.js-callVacancyStatusSearch.next.' + room
    driver.find_element_by_css_selector(room_class).click()
    adult_num_vacancy = int(driver.find_element_by_id('adultNumVacancy').get_attribute("value"))
    if adult_num_vacancy == 0:
        # Session単位で初回確認時では人数等の設定が必要
        select = Select(driver.find_element_by_id('adultNumVacancy'))
        select.select_by_index(2)
        driver.find_element_by_css_selector('.next.js-conditionHide').click()
    time.sleep(2)


def create_message(room_status):
    """ リストからメッセージを作成します

    リストから改行区切りのメッセージを作成します。
    Args:
        room_status (list): メッセージ化したいlistを指定します
    Returns:
        str: メッセージ
    """

    message = '\n'
    for room_name, status_by_date in room_status.items():
        message += room_name
        message += '\n'
        for date in status_by_date:
            message += date
            message += '\n'
    return message

def post_message_by_line(message):

    url = "https://notify-api.line.me/api/notify"
    access_token = 'nRn5BZ5ILeclbbAXMmzDTREqN7Dg2HmUBU0jje6JRTh'
    headers = {'Authorization': 'Bearer ' + access_token}

    hotelurl = 'https://reserve.tokyodisneyresort.jp/hotel/list/?showWay=&roomsNum=&adultNum=&childNum=&stayingDays=1&useDate=&cpListStr=&childAgeBedInform=&searchHotelCD=DHM&searchHotelDiv=&hotelName=&searchHotelName=&searchLayer=&searchRoomName=&hotelSearchDetail=true&detailOpenFlg=0&checkPointStr=&hotelChangeFlg=false&removeSessionFlg=true&returnFlg=false&hotelShowFlg=&displayType=hotel-search&reservationStatus=1'

    date = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    postmessage = f'\n{date}　空室状況\n'+message+hotelurl

    payload = {'message': postmessage}
    r = requests.post(url, headers=headers, params=payload, )


# googledriver読み込み
driver = webdriver.Chrome('chromedriver.exe')



# サイトへのアクセス
driver.get('https://reserve.tokyodisneyresort.jp/hotel/search/')
# ページ上のすべての要素が読み込まれるまで待機（15秒でタイムアウト判定）
WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
# 部屋選択画面へ移動
driver.find_element_by_class_name('dialogClose').click()
driver.find_element_by_id('js-callHotelSearch').click()
driver.find_element_by_xpath("//img[@src='/cgp/images/jp/pc/btn/btn_modal_hotel_02.png']").click()
time.sleep(3)

# 　部屋リストを作成
with open('roomname.txt', 'r', encoding='utf-8') as f:
    rooms = [line.rstrip('\n') for line in f]

status_list = {}
for room in rooms:
    # 空室状況を取得したい部屋を指定する
    select_room(driver, room)

    # 空室状況を取得したい月を指定する
    select_month(2021, 9)

    # 指定された月の空室状況状況を1か月分取得する
    status_list[room] = get_vacancy_status(driver, 2021, 9)

# 取得した空室状況から空室のみのリストを作成する
free_rooms = {}

for room_name, status_by_date in status_list.items():
    free_date = {}
    for date, status in status_by_date.items():
        if len(status) > 1:
            print(status)
            free_date[date] = status
    else:
        if len(free_date) > 0:
            free_rooms[room_name] = free_date

if free_rooms:
    free_rooms_message = create_message(free_rooms)
    post_message_by_line(free_rooms_message)
    print(free_rooms_message)
else:
    print(len(free_rooms))
    print(free_rooms)


