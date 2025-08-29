#!myenv/bin/python

from selenium import webdriver
from selenium.webdriver.chromium.service import ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
import schedule
import time
import datetime
import pyotp
import json
import os


service = ChromiumService(executable_path='/usr/local/bin/chromedriver')
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 启用无头模式
options.add_argument("--disable-gpu")  # 禁用GPU加速
options.add_argument("--no-sandbox")  # 禁用沙箱模式，解决某些环境下的启动问题

dir = os.path.dirname(__file__)
config = json.loads(open(os.path.join(dir, 'config.json')).read()) # 运行时目录下的 config.json


def do_scan():
    print(f"定时任务在 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 执行了！")

    # 遍历用户
    for user in config['users']:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)  # 最多等待 10 秒
        driver.set_window_size(1400, 800)
        driver.get(config['host'])

        try:
            print("开始登录:",user['username'])
            driver.find_element(By.ID, 'username').send_keys(user['username'])
            driver.find_element(By.ID, 'password').send_keys(user['password'])
            driver.find_element(By.XPATH, "//span[text()='登录']").click()

            # 如果页面有2FA
            elements = driver.find_elements(By.XPATH, "//h4[text()='请输入验证码']")
            if len(elements) > 0:
                print("检测到2FA验证码输入框")
                if "secret_key" in user and user['secret_key']:
                    totp = pyotp.TOTP(user['secret_key'])
                    code = totp.now()
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input.semi-input-large")
                    print(f"输入2FA验证码: {code}")
                    for i, digit in enumerate(code):
                        inputs[i].send_keys(digit)
                    print("已输入2FA验证码")
                    driver.find_element(By.XPATH, "//span[text()='登录']").click()
                    # 等待10秒后如果还在验证码页面，则认为登录失败，继续下一个用户
                    time.sleep(10)
                    elements = driver.find_elements(By.XPATH, "//h4[text()='请输入验证码']")
                    if len(elements) > 0:
                        print("2FA验证码输入错误，请检查密钥，继续下一个用户。")
                        continue    
                    print("2FA验证码已登录成功")
                else:
                    print("用户未配置2FA密钥，跳过登录，继续下一个用户")
                    continue    
            else:
                print("未检测到2FA验证码输入框")

            # settings
            print("开始点击相册")
            driver.find_element(By.XPATH, "//div[text()='相册']").click()

            # 等待新窗口出现（至少2个窗口）
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)

            # 切换到新窗口（通常是最后一个打开的）
            new_window = driver.window_handles[-1]  # 最新打开的窗口
            driver.switch_to.window(new_window)

            print(f"已切换到新窗口: {driver.current_url}")
            # ================== 在新窗口中操作 ==================
            #class会重复，使用d属性匹配
            print("进入相册，寻找设置按钮")
            driver.find_element(By.XPATH, "//*[@id='root']/main/div/div/div[2]/div[2]/div[2]").click()
            print("已点击设置按钮")
            print("寻找扫描全部按钮")
            driver.find_element(By.XPATH, "//span[text()='扫描全部' and contains(@class, 'semi-button-content-right')]").click()
            print("点击扫描全部按钮完成")
            
        except Exception as e:
            print("发生错误:", e)

        finally:
            # 释放所有资源
            if driver is not None:
                driver.quit()  # 关闭所有窗口并释放资源
                print("浏览器已关闭，资源已释放\n\n")
                time.sleep(30)

def main():
    timers = config.get("timer", [])
    if not timers:
        print("未配置定时时间")
        return

    print(f"注册定时任务: {timers}")
    for t in timers:
        # 校验时间格式（简单校验）
        if len(t) == 5 and t[2] == ':':
            schedule.every().day.at(t).do(do_scan)
            print(f"已添加: 每天 {t} 执行扫描")
        else:
            print(f"时间格式错误: {t}")
    print(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("等待执行定时任务")
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == '__main__':
    main()
