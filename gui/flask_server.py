import json
import time

import pyaudio
from flask import Flask, render_template, request
from flask_cors import CORS

import fay_booter

from core.tts_voice import EnumVoice
from gevent import pywsgi
from scheduler.thread_manager import MyThread
from utils import config_util
from core import wsa_server
from core.interact import Interact
from core import fay_core
from utils import util

__app = Flask(__name__)
CORS(__app, supports_credentials=True)


def __get_template():
    return render_template('index.html')


def __get_device_list():
    audio = pyaudio.PyAudio()
    device_list = []
    for i in range(audio.get_device_count()):
        devInfo = audio.get_device_info_by_index(i)
        if devInfo['hostApi'] == 0:
            device_list.append(devInfo["name"])
    
    return list(set(device_list))


@__app.route('/api/submit', methods=['post'])
def api_submit():
    data = request.values.get('data')
    # print(data)
    config_data = json.loads(data)
    if(config_data['config']['source']['record']['enabled']):
        config_data['config']['source']['record']['channels'] = 0
        audio = pyaudio.PyAudio()
        for i in range(audio.get_device_count()):
            devInfo = audio.get_device_info_by_index(i)
            if devInfo['name'].find(config_data['config']['source']['record']['device']) >= 0 and devInfo['hostApi'] == 0:
                 config_data['config']['source']['record']['channels'] = devInfo['maxInputChannels']

    config_util.save_config(config_data['config'])


    return '{"result":"successful"}'


@__app.route('/api/get-data', methods=['post'])
def api_get_data():
    config_data = config_util.config
    if  wsa_server.new_instance().isConnect:
        config_data['interact']['playSound'] = False
    else:
        config_data['interact']['playSound'] = True
    config_util.save_config(config_data)
    wsa_server.get_web_instance().add_cmd({
        "voiceList": [
            {"id": EnumVoice.XIAO_XIAO_NEW.name, "name": "晓晓(azure)"},
            {"id": EnumVoice.XIAO_XIAO.name, "name": "晓晓"},
            {"id": EnumVoice.YUN_XI.name, "name": "云溪"},
            {"id": EnumVoice.YUN_JIAN.name, "name": "云健"},
            {"id": EnumVoice.XIAO_YI.name, "name": "晓伊"},
            {"id": EnumVoice.YUN_YANG.name, "name": "云阳"},
            {"id": EnumVoice.YUN_XIA.name, "name": "云夏"}
        ]
    })
    wsa_server.get_web_instance().add_cmd({"deviceList": __get_device_list()})
    return json.dumps({'config': config_util.config})


@__app.route('/api/start-live', methods=['post'])
def api_start_live():
    # time.sleep(5)
    fay_booter.start()
    time.sleep(1)
    wsa_server.get_web_instance().add_cmd({"liveState": 1})
    return '{"result":"successful"}'


@__app.route('/api/stop-live', methods=['post'])
def api_stop_live():
    # time.sleep(1)
    fay_booter.stop()
    time.sleep(1)
    wsa_server.get_web_instance().add_cmd({"liveState": 0})
    return '{"result":"successful"}'

wx_msg_msg_id = ''
@__app.route('/api/get-wx-msg', methods=['post'])
def api_get_wx_msg():
    global wx_msg_msg_id
    if fay_booter.__running:
        data = request.json
        info = data['events'][0]
        if wx_msg_msg_id != info['msg_id']:
            wx_msg_msg_id = info['msg_id']
            if info['decoded_type'] == 'enter':
                #进入
                interact = Interact("live", 2, {"user": info['nickname'], "msg": "来了"})
            elif info['decoded_type'] == 'comment':
                #留言
                interact = Interact("live", 1, {"user": info['nickname'], "msg": info['content']})
                fay_core.new_instance().last_quest_time = time.time()
            elif info['decoded_type'] == 'gift':
                #礼物
                interact = Interact("live", 3, {"user": info['nickname'], "msg": "礼物", "gift": '礼物', "amount": info['gift_num'],})
            MyThread(target=fay_core.new_instance().on_interact, args=[interact]).start()
    else:
        util.log(1, "请先进行开启")    
    return '{"result":"successful"}' 


@__app.route('/', methods=['get'])
def home_get():
    return __get_template()


@__app.route('/', methods=['post'])
def home_post():
    return __get_template()

def run():
    server = pywsgi.WSGIServer(('0.0.0.0',5000), __app)
    server.serve_forever()

def start():
    MyThread(target=run).start()
