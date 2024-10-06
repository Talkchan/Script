# Author: Chunbing
# Update:2024-10-6
# 广西职业院校学生实习签到
# 添加账号说明(青龙/本地)二选一
#   青龙: 青龙变量cstoken 值{"ck":"xxxxxxxx"} 一行一个(回车分割)
#   本地: 脚本内置ck方法ck_token = [{"ck":"xxxxxxxx"},{"ck":"xxxxxxxx"}]
# 推送消息:
#   青龙变量linxi_push 值为WxPusher UID
# 脚本声明: 仅供学习交流，如用于违法违规操作与本作者无关,请勿用于非法用途,请在24小时内删除该文件!
# 软件版本
version = "0.0.1"
name = "广西职业院校学生实习签到"
linxi_token = "sxqdtoken"
linxi_tips = '{"Authorization":"Bearer eyjalkgnlanlxxxxxxxx"}'


import os
import re
import json
import time
import requests
from urllib.parse import quote
from multiprocessing import Pool
from geopy.distance import geodesic
import random
import math

# 变量类型(本地/青龙)
Btype = "本地"
# 域名(无法使用时请更换)
domain = 'https://gxzjsx.gxibvc.net/api/studentapp'
# 保持连接,重复利用
ss = requests.session()
# 全局基础请求头
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.52(0x18003425) NetType/4G Language/zh_CN",
    "Origin": "https://gxzjsxs.gxibvc.net",
    "Referer": "https://gxzjsxs.gxibvc.net/",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}

# 用于生成随机经纬度
def generate_random_location(lat, lng, radius):
    earth_radius = 6371000
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    for _ in range(100):
        random_angle = random.uniform(0, 2 * math.pi)
        random_radius = radius * random.uniform(0, 1)
        new_lat = math.asin(math.sin(lat_rad) * math.cos(random_radius / earth_radius) +
                            math.cos(lat_rad) * math.sin(random_radius / earth_radius) * math.cos(random_angle))
        new_lat_deg = math.degrees(new_lat)
        new_lng = lng_rad + math.atan2(math.sin(random_angle) * math.sin(random_radius / earth_radius) * math.cos(lat_rad),
                                      math.cos(random_radius / earth_radius) * math.sin(lat_rad))
        new_lng_deg = math.degrees(new_lng)
        if geodesic((new_lat_deg, new_lng_deg), (lat, lng)).meters <= radius:
            return new_lat_deg, new_lng_deg
    return lat, lng

def user_info(i, ck):
    headers['Authorization'] = ck['Authorization']
    results = {
        "Info": ss.post(domain + "/Info", headers=headers).json(),
        "Settings": ss.post(domain + "/Settings", headers=headers).json()
    }

    # 检查请求是否成功
    if results['Info']['Code'] == 0 and results['Settings']['Code'] == 0:
        print(f"账号【{i + 1}】✅")
        info_message = f"学校：{results['Settings']['Data']['SchoolName']} 学号：{results['Settings']['Data']['StudentNo']} 姓名：{results['Settings']['Data']['StudentName']}\n实习单位：{results['Settings']['Data']['CompanyName']} 实习职位：{results['Info']['Data']['Post']} 签到天数：{results['Info']['Data']['TotalSignCount']}"
        print(info_message)
        if os.getenv("linxi_push"):
            Wxpusher(name, os.getenv("linxi_push"), info_message)
    else:
        info_error = results['Info'].get('Msg', '没有返回信息') if 'Code' in results['Info'] and results['Info']['Code'] != 0 else ""
        settings_error = results['Settings'].get('Msg', '没有返回信息') if 'Code' in results['Settings'] and results['Settings']['Code'] != 0 else ""
        error_message = f"获取信息失败: {info_error}, 获取设置失败: {settings_error}"
        print(f"账号【{i + 1}】🚫 {error_message}")
        if os.getenv("linxi_push"):
            Wxpusher(name, os.getenv("linxi_push"), error_message)


def do_read(i, ck):
    headers["Authorization"] = ck["Authorization"]
    results = {
        "Info": ss.post(domain + "/Info", headers=headers).json(),
        "Settings": ss.post(domain + "/Settings", headers=headers).json()
    }

    if results['Info'] and 'Data' in results['Info'] and results['Info']['Code'] == 0:
        sign_today = results['Info']['Data'].get('SignToday', False)
        if sign_today:
            print(f"账号【{i + 1}】✅今天已经签到过了")
            return
    else:
        print(f"账号【{i + 1}】❌获取签到状态失败: {results['Info'].get('Msg', '无错误信息')}")
        return

    if results['Settings'] and 'Data' in results['Settings'] and results['Settings']['Code'] == 0:
        random_lat, random_lng = generate_random_location(results['Settings']['Data']['CompanyLat'],results['Settings']['Data']['CompanyLng'],results['Settings']['Data']['SignRange'])

        if geodesic((random_lat, random_lng), (results['Settings']['Data']['CompanyLat'], results['Settings']['Data']['CompanyLng'])).meters <= results['Settings']['Data']['SignRange']:
            sign_data = {"Lat": random_lat, "Lng": random_lng}
            sign_response = requests.post(domain + "/Sign", headers=headers, json=sign_data)
            result = sign_response.json()

            if result and 'Code' in result and result['Code'] == 0:
                sign_message = f"账号【{i + 1}】✅签到成功\n签到位置：({random_lat}, {random_lng})"
                print(sign_message)
                if os.getenv("linxi_push"):
                    Wxpusher(name, os.getenv("linxi_push"), sign_message)
            else:
                message = f"账号【{i + 1}】❌签到失败: {result.get('Msg', '未知错误')}"
                print(message)
                if os.getenv("linxi_push"):
                    Wxpusher(name, os.getenv("linxi_push"), message)
        else:
            print(f"生成的随机位置不在签到范围内")
    else:
        message = f"账号【{i + 1}】获取签到信息失败: {results['Settings'].get('Msg', '无错误信息')}"
        print(message)
        if os.getenv("linxi_push"):
            Wxpusher(name, os.getenv("linxi_push"), message)



def get_money(i,ck):
    print(f"账号【{i+1}】❌ {ck}")
    pass

# 微信Wxpusher 推送 UID扫码获取: https://wxpusher.zjiecode.com/demo/
def Wxpusher(name,key,message,ipinfo=""):
    # 通知标题,Wxpusher UID,通知消息内容
    code = f'''{name}
        <body style="font-family: 'Arial', sans-serif; background-color: #f2f2f2; margin: 0; padding: 20px;">
            <div class="notification" style="background-color: #ffffff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #333; text-align: center;"> 任务执行结束 </h2>
                <h3 style="color: #666; text-align: center;"> {name} </h3>
                <div class="code-block" style="background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-top: 15px; overflow: auto;">
                    <pre style="color: #333;">{message}</pre></div>
                <div class="ip-address" style="margin-top: 15px; text-align: center; font-weight: bold; color: #007bff;">推送IP: {ipinfo}</div></div>
            <div class="separator" style="margin: 20px 0; border-top: 1px solid #ddd;"></div>
            <div class="end-message" style="text-align: center; color: #28a745; font-weight: bold;">任务已完成</div>
        </body>
    '''
    result = ss.get(f"https://wxpusher.zjiecode.com/demo/send/custom/{key}?content={quote(code)}").json()
    if result['code'] == 1000:
        return True, f"微信Wxpusher 通知: 推送成功!"
    else:
        return False, f"微信Wxpusher 通知: 推送失败!"

def handle_exception(e,i):
    print(f"账号【{i+1}】🆘 程序出现异常: {e}")
    if os.getenv("linxi_push") == None:
        print(f"账号【{i+1}】✴️ 未配置Wxpusher推送!")
    else:
        ipinfo = ss.get("https://v4.ip.zxinc.org/info.php?type=json").json()
        ipcity = ipinfo['data']['location']
        ip = ipinfo['data']['myip']
        Wxpusher(name,os.getenv("linxi_push"),f"账号【{i+1}】🆘 程序出现异常: {e}",f"{ipcity} [{ip}]")

def process_wrapper(func, args):
    try:
        func(*args)
    except Exception as e:
        handle_exception(e,args[0])


if __name__ == "__main__":
    print(f"""     ██████╗██╗  ██╗██╗   ██╗███╗   ██╗██████╗ ██╗███╗   ██╗ ██████╗ 
    ██╔════╝██║  ██║██║   ██║████╗  ██║██╔══██╗██║████╗  ██║██╔════╝ 
    ██║     ███████║██║   ██║██╔██╗ ██║██████╔╝██║██╔██╗ ██║██║  ███╗
    ██║     ██╔══██║██║   ██║██║╚██╗██║██╔══██╗██║██║╚██╗██║██║   ██║
    ╚██████╗██║  ██║╚██████╔╝██║ ╚████║██████╔╝██║██║ ╚████║╚██████╔╝
     ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
    项目:{name}           BY-春冰          Verion: {version}(并发)
    提示:脚本仅供技术交流学习使用，严禁用于任何商业用途或非法活动!
    Github仓库地址: https://github.com/Talkchan/Script
    """)

    if Btype == "青龙":
        if os.getenv(linxi_token) == None:
            print(f'⛔ 青龙变量异常: 请添加{linxi_token}变量示例:{linxi_tips} 确保一行一个')
            exit()
        # 变量CK列表
        #ck_token = [json.loads(line) for line in os.getenv(linxi_token).splitlines()]
        ck_token = [json.loads(li) if "&" in line else json.loads(line) for line in os.getenv(linxi_token).splitlines() for li in re.findall(r'{.*?}', line)]
    else:
        # 本地CK列表
        ck_token = [
            # 这里填写本地变量
            {"Authorization":"Bearer eyjalkgnlanlxxxxxxxx"}
        ]
        if ck_token == []:
            print(f'⛔ 本地变量异常: 请添加本地ck_token示例:{linxi_tips}')
            exit()
    # 创建进程池
    with Pool() as pool:
        print("==================👻获取账号信息👻=================")
        pool.starmap(process_wrapper, [(user_info, (i, ck)) for i, ck in enumerate(ck_token)])
        print("==================💫开始执行任务💫=================")
        pool.starmap(process_wrapper, [(do_read, (i, ck)) for i, ck in enumerate(ck_token)])
        print("==================🐣获取账号信息🐣=================")
        pool.starmap(process_wrapper, [(user_info, (i, ck)) for i, ck in enumerate(ck_token)])
        # print("==================🐋开始账号提现🐋=================")
        # pool.starmap(process_wrapper, [(get_money, (i, ck)) for i, ck in enumerate(ck_token)])


        # 关闭进程池
        pool.close()
        # 等待所有子进程执行完毕
        pool.join()

        # 关闭连接
        ss.close
        # 输出结果
        print(f"================[{name}V{version}]===============")
