"""
Copyright 2020 belltreeSzk

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import json
import urllib.request
import time

# 検索ワード
# 複数ワードを入れている場合、最初の文字が検索の基準になる
# ex) チを見つけたらティとみなしてpostする
SEARCH_WORDS = ['ティ', 'チ']

# SlackBotのトークンと対象のチャンネルIDを指定してください
SLACK_BOT_TOKEN = 'xoxb-XXXXXXXXXXXXX'
SLACK_CHANNEL_ID = 'CXXXXXXXXX'

# COTOHAのclientIdとclientSecretを指定してください
COTOHA_CLIENT_ID = 'XXXXXXXX'
COTOHA_CLIENT_SECRET = 'XXXXXXX'

# チェック間隔
CHECK_SPAN = 120

# 起点
def checkMessage(event, context):
    sentences = getConversationsHistory()
    token = getAccessToken()
    bot_id = getBotId()

    for sentence in sentences:
        result = parse(token, sentence['text'])
        hitWord = searchWord(result)
        if hitWord != {}:
            if checkReplies(bot_id, sentence) :
                message = generateMessage(hitWord)
                postComment(message, sentence)

# BotIdを取得
# 既に通知を出していたら再送しないようにするため
def getBotId ():
    url = 'https://slack.com/api/auth.test'
    data = {
        'token': SLACK_BOT_TOKEN
    }
    headers = {
        'Content-Type': 'application/json',
        "Authorization": "Bearer " + SLACK_BOT_TOKEN
    }
    req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()

    str_body = body.decode()
    json_str_body = json.loads(str_body)
    return json_str_body['user_id']

# 通知を出す
# 投稿のThreadに投稿するためtsは必須
def postComment (message, sentence):
    url = 'https://slack.com/api/chat.postMessage'
    data = {
        'token': SLACK_BOT_TOKEN,
        'channel': SLACK_CHANNEL_ID,
        'text' : message,
        'thread_ts' : sentence['ts']
    }
    headers = {
        'Content-Type': 'application/json',
        "Authorization": "Bearer " + SLACK_BOT_TOKEN
    }
    
    req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()

    str_body = body.decode()
    json_str_body = json.loads(str_body)
    return json_str_body


# 既に通知を送ったかチェック
def checkReplies (bot_id, sentence):
    url = 'https://slack.com/api/conversations.replies?'
    data = {
        'token': SLACK_BOT_TOKEN,
        'channel': SLACK_CHANNEL_ID,
        'ts' : sentence['ts']
    }
    query = urllib.parse.urlencode(data)
    with urllib.request.urlopen(url+query) as res:
        body = res.read()

    str_body = body.decode()
    json_str_body = json.loads(str_body)

    isExec = True
    if 'replies' in json_str_body['messages'][0]:
        for reply in json_str_body['messages'][0]['replies']:
            if reply['user'] == bot_id:
                isExec = False
                break

    return isExec

# 投稿する文字を生成
def generateMessage (hitWord):
    # 検索している文字と一致している場合（ティを探して、ティがあった場合）
    if hitWord['search'] == SEARCH_WORDS[0] :
        # 既にカタカナ表記であればそのまま
        if hitWord['word'] == hitWord['kana']:
            message = hitWord['word']
        # 一度変換していれば、変換経路を書く
        else :
            message = hitWord['word'] + "…" + hitWord['kana'] 
    # 投稿する文字を生成（ティを探して、チがあった場合）
    else:
        # 変換経路（ケンチ → ケンティ） 
        replace = hitWord['kana'].replace(hitWord['search'], SEARCH_WORDS[0]) 
        # 既にカタカナ表記であればそのまま
        if hitWord['word'] == hitWord['kana']:
            message = hitWord['word'] + "…" +  replace
        # 一度変換していれば、変換経路を書く
        else :
            message = hitWord['word'] + "…" + hitWord['kana'] + "…" + replace

    message += "\nティーーーー！！！！"
    message += "\nティー！ティティー！ティーティティティーーーー！！"

    return message

# メッセージを取得する
def getConversationsHistory ():
    ut = time.time()
    ut = int(ut)- CHECK_SPAN
    url = 'https://slack.com/api/conversations.history?'
    data = {
        'token': SLACK_BOT_TOKEN,
        'channel': SLACK_CHANNEL_ID,
        'oldest' : ut,
        'inclusive' : True
    }
    query = urllib.parse.urlencode(data)
    with urllib.request.urlopen(url+query) as res:
        body = res.read()

    str_body = body.decode()
    
    json_str_body = json.loads(str_body)

    return json_str_body['messages']

# アクセストークンを取得する
def getAccessToken():
    url = 'https://api.ce-cotoha.com/v1/oauth/accesstokens'
    data = {
        'grantType': 'client_credentials',
        'clientId': COTOHA_CLIENT_ID,
        'clientSecret': COTOHA_CLIENT_SECRET,
    }
    headers = {
        'Content-Type': 'application/json',
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()

    str_body = body.decode()
    json_str_body = json.loads(str_body)
    return json_str_body['access_token']

# テキストをCOTOHAに送って、構文解析をする
def parse(token, sentence):
    url = 'https://api.ce-cotoha.com/api/dev/nlp/v1/parse'
    data = {
        'sentence': sentence,
        'type': 'default',
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read()

    str_body = body.decode('utf-8')
    json_str_body = json.loads(str_body)
    return json_str_body

# 受け取った結果から該当の文字列を探す
def searchWord(result): 
    hitWord = {}
    breakFlag = False
    for chunk in result['result']:
        for tokens in chunk['tokens']:
            for search in SEARCH_WORDS:
                if search in tokens['kana'] :
                    hitWord = {
                        'word' : tokens['form'],
                        'kana' : tokens['kana'],
                        'pos' : tokens['pos'],
                        'search' : search
                    }
                    breakFlag = True
                    break
            if breakFlag:
                break
        if breakFlag:
            break

    return hitWord
