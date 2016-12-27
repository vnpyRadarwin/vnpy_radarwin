# encoding: UTF-8

import requests
import json


def get_token():
    url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    values = {'corpid': 'wx3d90dc6f7ba7729d',
              'corpsecret': '9gXxwP0CEbXznP1hYjZRwnM8Ob2InUYcGvvQ-CMVk35kGBtlK-c8z6fY5VWdXqBZ',
              }
    req = requests.post(url, params=values)
    data = json.loads(req.text)
    return data["access_token"]


def send_msg(message):
    print "send_msg"
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + get_token()
    values = """{"touser" : "1" ,
      "toparty":"1",
      "msgtype":"text",
      "agentid":"4",
      "text":{
        "content": "%s"
      },
      "safe":"0"
      }""" % (str(message))

    data = json.loads(values)
    req = requests.post(url, values)


if __name__ == '__main__':
    send_msg('message')
