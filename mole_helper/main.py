# 20210702
import json
from json import encoder
import time
import requests

# config = {}
gift = []
weather = []
rain_list = []
gift_list = []
old_gift_list = []
new_gift_list = []

week_dict = {
    1:"本周一",
    2:"本周二",
    3:"本周三",
    4:"本周四",
    5:"本周五",
    6:"本周六",
    7:"本周日",
    8:"下周一",
    9:"下周二",
    10:"下周三",
    11:"下周四",
    12:"下周五",
    13:"下周六",
    14:"下周日"
}

merge_list = [
    "-04:00 04:00-",
    "-08:00 08:00-",
    "-12:00 12:00-",
    "-16:00 16:00-",
    "-20:00 20:00-"
]

hour_dict = {
    1:"00:00-04:00",
    2:"04:00-08:00",
    3:"08:00-12:00",
    4:"12:00-16:00",
    5:"16:00-20:00",
    6:"20:00-00:00"
}

# 写日志 log
def log(status, log_data):
    today = time.strftime("%Y%m%d", (time.localtime()))
    with open('log/'+today, 'a') as f:
        now = time.strftime("%Y.%m.%d %H:%M:%S", (time.localtime()))
        if status:
            f.write('[+]' + now + ' ' + log_data + '\n')
        else:
            f.write('[-]' + now + ' ' + log_data + '\n')

    return


# 读取密令历史记录 gift.json
def get_gift():
    try:
        with open('gift.json', 'r') as f:
            gift = json.load(f)
    except:
        gift = []

    return gift


# 读取天气历史记录 weather.json
def get_weather():
    try:
        with open('weather.json', 'r') as f:
            weather = json.load(f)
    except:
        weather = []

    return weather


# 校验更新
def check_new():
    global old_gift_list, rain_list, gift_list, new_gift_list
    headers = {
        "Host": "www.gankeapp.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
    }

    url = 'https://www.gankeapp.com/common_data/mole_weather'
    req = requests.get(url, headers=headers, timeout=10)
    req_dict = json.loads(req.text)
    # _rain = False
    rain_list = []

    # 覆盖为最新天气
    try:
        if req_dict['lastTime'] != weather['lastTime']:
            with open('weather.json', 'w', encoding='utf-8') as f:
                json.dump(req_dict, f, ensure_ascii=False)
                # _rain = True
    except:
        with open('weather.json', 'w', encoding='utf-8') as f:
            json.dump(req_dict, f, ensure_ascii=False)
            # _rain = True

    # 记录雨天
    # 20210816 将雨天只推送一次修改为每天推送
    # if _rain:
    rain_week = 1
    for weather_list in req_dict['data']:
        if not isinstance(weather_list[0], int):
            continue
        rain_hour = 0
        rain_hour_list = []
        for i in weather_list:
            if i == "下雨":
                rain_hour_list.append(rain_hour)
            rain_hour += 1

        rain_data = ''
        for i in rain_hour_list:
            rain_data = rain_data + hour_dict[i] + ' '
        if rain_data:
            time_data = rain_data[:-1]
            # rain_data[:-1] 08:00-12:00 16:00-20:00 20:00-00:00
            for merge_time in merge_list:
                if merge_time in time_data:
                    time_data = time_data.replace(merge_time, "-")
            rain_list.append(week_dict[rain_week] + "({})".format(time_data))
            log(True, week_dict[rain_week] + "({})".format(time_data))
        rain_week += 1

    # 记录新增密令
    url = 'https://www.gankeapp.com/common_data/molegift'
    req = requests.get(url, headers=headers, timeout=10)
    req.encoding = 'utf-8'
    req_dict = json.loads(req.text)
    _gift = False
    try:
        if req_dict['lastTime'] != gift['lastTime']:
            with open('gift.json', 'w', encoding='utf-8') as f:
                json.dump(req_dict, f, ensure_ascii=False)
                _gift = True
    except:
        with open('gift.json', 'w', encoding='utf-8') as f:
            json.dump(req_dict, f, ensure_ascii=False)
            _gift = True

    new_gift_list = []

    # 没有新的密令
    if not _gift:
        return

    req_dict['data'].pop(0)
    req_dict['data'].pop(0)
    for gift_lists in req_dict['data']:
        gift_data = gift_lists[0]
        gift_key = gift_lists[1]
        gifts = ''
        if '，' in gift_data:
            for i in gift_data.split('，'):
                if "&gt;" in i:
                    i = i.split("&gt;", 1)[1].rsplit("&lt;", 1)[0]
                gifts = gifts + i + ' '
        elif '、' in gift_data:
            for i in gift_data.split('、'):
                if "&gt;" in i:
                    i = i.split("&gt;", 1)[1].rsplit("&lt;", 1)[0]
                gifts = gifts + i + ' '
        else:
            i = gift_data
            if "&gt;" in i:
                i = i.split("&gt;", 1)[1].rsplit("&lt;", 1)[0]
            gifts = gifts + i + ' '

        gift_list.append(gift_key+' ({})'.format(gifts[:-1]))

    gift_list.reverse()
    if not old_gift_list:
        new_gift_list = gift_list
        for i in new_gift_list:
            log(True, i)
    else:
        for i in gift_list:
            if i not in old_gift_list:
                new_gift_list.append(i)
                log(True, i)
            else:
                break

    old_gift_list = gift_list
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(old_gift_list, f, ensure_ascii=False)

    return


# 发送推送信息-企业微信接口
def send_msg():
    global rain_list, new_gift_list
    today = time.strftime("%Y%m%d", (time.localtime()))
    access_token = get_access_token()

    desp = "摩尔庄园助手({})\n".format(today)
    desp = desp + "下雨天：\n"
    for i in rain_list:
        desp = desp + "- " + i + "\n"
    desp = desp + "新增密令：\n"
    for i in new_gift_list:
        desp = desp + "- " + i + "\n"

    raw = {
        "touser" : "@all",
        "msgtype" : "text",
        "agentid" : 1000002,
        "text" : {
            "content" : desp
        }
    }
    data = json.dumps(raw)
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(access_token)
    requests.post(url, data=data, timeout=10)

    return


def get_access_token():
    access_token = ''
    # corpid 填入 企业ID 参考：https://work.weixin.qq.com/api/doc/90000/90135/90665#corpid
    # corpsecret 填入 应用的凭证密钥 参考：https://work.weixin.qq.com/api/doc/90000/90135/90665#secret
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=123456&corpsecret=abcde"
    req = requests.get(url, timeout=10)
    req_dict = json.loads(req.text)
    if req_dict['errmsg'] != "ok":
        return access_token
    
    access_token = req_dict['access_token']

    return access_token


while True:
    # 晚上23-早上9 不运行(免打扰)
    hour = int(time.strftime("%H", (time.localtime())))
    if hour>=23 or hour<9:
        time.sleep(600) # 休眠10分钟
        continue

    # 取消了配置文件 20210826
    # 查看是否存在配置文件
    # if not config:
    #     time.sleep(60) # 休眠1分钟
    #     continue

    # 获取今日日期
    today = time.strftime("%Y%m%d", (time.localtime()))
    # 获取今日日志
    today_log = ''
    try:
        with open('log/'+today, 'r') as f:
            today_log = f.read()
    except:
        today_log = ''
    
    if today_log:
        # 今天已经运行过了，明天再运行吧(防喝茶)
        time.sleep(600) # 休眠10分钟
        continue

    # 读取历史数据
    gift = get_gift()
    weather = get_weather()

    # 读取历史密令
    try:
        with open('history.json', 'r') as f:
            old_gift_list = json.load(f)
    except:
        old_gift_list = []

    # 校验更新
    check_new()

    # 推送信息
    send_msg()

    time.sleep(600) # 休眠10分钟