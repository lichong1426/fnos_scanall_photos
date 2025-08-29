 飞牛OS的相册十分好用，我是远程挂载某NAS上的目录，奈何美中不足的是无法自动扫描和刷新，浏览论坛官方好像也没有相关计划，只能自己想办法了。
 刚开始准备使用API，但是签名机制没有研究出来且二次登录不好弄，又不想继续耗费太多精力，干脆使用简单粗暴的selenium模拟登录点击。
 
## 功能介绍
自动触发扫描相册
1. 配置文件写入参数
2. 支持2FA登录
3. 支持自定义触发时间（当前只支持每天触发）
4. 基于FnOS 0.9.22验证
5. 使用selenium获取页面元素路径，如果页面发生变化可能导致功能不可能，需要重新配置元素路径。

## 配置文件

config.json
```
{
    "host":"http://192.168.xxx.xxx:5666", //Fnos地址或域名
    "users":[
        {
            "username": "usera",
            "password": "password"
        },
        {
            "username": "userb",
            "password": "password",
            "secret_key": "7G2JSOSWJFFADFDFCVRVDAS75B6M6EE"  //2FA密钥，没有可以不写会跳过
        }
    ],
    "timer":["02:18","12:00","19:00"] //定时时间，24小时制，每天执行。不建议设置太多。
}
```

> [!warning]
> 配置文件为明文用户名密码和密钥，务必存放在安全的地方


## 环境部署
理论上可以部署在任何环境，可自行选择。
我选择直接部署在fnos内。

> [!warning]
> 再次提示：玩机有风险，搞机需谨慎


1. ssh登录后创建目录

```
su root
cd /usr/local/src
mkdir fnos_scanall_photos
cd fnos_scanall_photos
```

将`config.json`和`fnscanpotos.py`放入，并赋予py可执行权限


2. 安装依赖
避免污染系统 Python 环境
```bash
python3 -m venv myenv

source myenv/bin/activate
pip3 install selenium webdriver-manager schedule pyotp

deactivate #使用完后退出
```
`myenv/bin/python -V` 查看版本

修改`fnscanpotos.py`头为`myenv/bin/python`的绝对路径

3. 安装chrome及chromedriver
```
# 进入临时目录
cd /tmp

# 下载最新版 Google Chrome（稳定版）
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

apt update && apt install ./google-chrome-stable_current_amd64.deb
```

查看版本号
```
google-chrome --version
Google Chrome 139.0.7258.154
```

前往 https://googlechromelabs.github.io/chrome-for-testing/ 选择对应平台的chromedriver

```
wget https://storage.googleapis.com/chrome-for-testing-public/139.0.7258.154/linux64/chromedriver-linux64.zip

unzip chromedriver-linux64.zip

mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver

# 添加执行权限
sudo chmod +x /usr/local/bin/chromedriver
```

4. 测试环境
直接运行fnscanpotos.py，出现如下打印，并登录页面查看确实触发了，则说明环境没有问题。

```
注册定时任务: ['08:59', '19:00', '02:00']
已添加: 每天 08:59 执行扫描
已添加: 每天 19:00 执行扫描
已添加: 每天 02:00 执行扫描
当前时间: 2025-08-29 08:58:24
等待执行定时任务
定时任务在 2025-08-29 08:59:24 执行了！
开始登录: usera
检测到2FA验证码输入框
输入2FA验证码: 819113
已输入2FA验证码
2FA验证码已登录成功
开始点击相册
已切换到新窗口: http://192.168.xx.xx:5666/p
进入相册，寻找设置按钮
已点击设置按钮
寻找扫描全部按钮
点击扫描全部按钮完成
浏览器已关闭，资源已释放
```


5. 配置systemd启动
vim /etc/systemd/system/scanallphotos.service
```bash
[Unit]
Description=scanallphotos service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/src/fnos_scanall_photos/fnscanpotos.py
User=root
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
没有配置失败自动重启，如果发现哪天相册没有自动扫描了建议自行排查。

让创建的服务生效，更新systemd目录  
systemctl daemon-reload

开启服务  
systemctl enable scanallphotos.service

启动服务  
systemctl start scanallphotos.service

查看服务状态  
systemctl status scanallphotos.service

如下则已经启动
```
systemctl status scanallphotos.service

● scanallphotos.service - scanallphotos service
     Loaded: loaded (/etc/systemd/system/scanallphotos.service; enabled; preset: enabled)
     Active: active (running) since Fri 2025-08-29 09:50:43 CST; 4s ago
   Main PID: 54914 (fnscanpotos.py)
      Tasks: 1 (limit: 4562)
     Memory: 18.8M
        CPU: 628ms
     CGroup: /system.slice/scanallphotos.service
             └─54914 /usr/local/src/fnos_scanall_photos/myenv/bin/python /usr/local/src/fnos_scanall_photos/fnscanpotos.py

Aug 29 09:50:43 FnOS systemd[1]: Started scanallphotos.service - scanallphotos service.
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 注册定时任务: ['02:00', '13:00', '19:00']
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 已添加: 每天 02:00 执行扫描
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 已添加: 每天 13:00 执行扫描
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 已添加: 每天 19:00 执行扫描
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 当前时间: 2025-08-29 09:50:44
Aug 29 09:50:44 FnOS fnscanpotos.py[54914]: 等待执行定时任务
```


如果修改了配置文件，则需要重启服务
systemctl restart scanallphotos.service

## 其他说明（叠buff）

本小程序完全是出于方便自用的角度编写，所以不提供后续维护，随机更新。还是更希望官方能够出定时刷新的功能。
**如果飞牛或其它组织联系删除会立即删除**

