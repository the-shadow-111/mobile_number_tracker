from django.shortcuts import render
from tracker.models import bot_user
from django.http import HttpResponse
from django.views.decorators.csrf import  csrf_exempt
import string
import requests

import json

import apiai

from pymessenger import Bot

main_url='http://api.mobilenumbertracker.com/v1/person'
page_access_token='EAABnZAOX3GmIBAH8lNZChHT4RqYaCtadUPrnStVCMWZCrb5SY5FTIkHqeAVPYZCFQkNOal2aDAmWlmUk76heEsJy00dvnA0i6Ar9IZBpHcavWbG1vq9Qdqwp6yhZCCqmV0aGV6B4PhQDY1kr6CLK6dWHAlzG8ZBZATQfHhqVH7ud9QZDZD'
number_emojis=['0️⃣','1️⃣','2️⃣','3️⃣', '4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']

messenger_bot=Bot(page_access_token)

apiai_token='6c5a7c9503f14468b1a62fb74dafdfae'

@csrf_exempt
def webhook(request):

    # this one is used to authenticate the webhook on messenger
    if request.method == 'GET':
        if 'hub.mode' in request.GET and 'hub.verify_token' in request.GET:
            if request.GET['hub.mode'] == 'subscribe' and request.GET['hub.verify_token'] == 'mobile_tracker':
                return HttpResponse(request.GET['hub.challenge'])
            else:
                return HttpResponse("Wrong verification code")
        else:
            return HttpResponse("Something went wrong")

    elif request.method == 'POST':
        print("I am here")
        # decodes the request and then converts it into json format
        request_body = request.body.decode('utf-8')
        req = json.loads(request_body)
        print(req)
        recipient_id = req['entry'][0]['messaging'][0]['sender']['id']
        post_back = None
        quick_reply_message = None
        text_message = None
        attachments = None

        # The following block of try-except blocks just checks for what type of message we are receiving
        try:
            current_bot_user = bot_user.objects.get(facebook_id=recipient_id)
        except:
            current_bot_user=create_new_bot_user(recipient_id=recipient_id)
        try:
            post_back = req['entry'][0]['messaging'][0]['postback']
        except:
            pass

        try:
            quick_reply_message = req['entry'][0]['messaging'][0]['message']['quick_reply']
        except:
            pass

        try:
            text_message = req['entry'][0]['messaging'][0]['message']['text']
        except:
            pass

        # If we received  a text message then we call api.ai

        if text_message and not quick_reply_message:
            handle_text_message(recipient_id, text_message)

        elif post_back:
            payload=post_back['payload']
            if payload=='get_started':
                first_name=current_bot_user.first_name
                message="Hi "+ first_name+" welcome to mobile/number bot :) Type a number/name to get details"
                messenger_bot.send_text_message(recipient_id=recipient_id, message=message)


        return HttpResponse('')

    else:
        return HttpResponse("Something went Wrong")


def create_new_bot_user(recipient_id):
    user_details = get_facebook_details(recipient_id)

    # Store the user details in the database

    print(user_details)

    current_user = bot_user()
    current_user.first_name = user_details['first_name']
    current_user.facebook_id = recipient_id
    current_user.last_name = user_details['last_name']
    current_user.profile_pic = user_details['profile_pic']
    current_user.locale = user_details['locale']
    current_user.timezone = user_details['timezone']
    current_user.gender = user_details['gender']

    current_user.apiai_status = json.dumps({})

    current_user.save()

    return current_user


def handle_text_message(recipient_id, text_message):
    ai=apiai.ApiAI(client_access_token=apiai_token)
    request=ai.text_request()

    request.query=text_message

    response=request.getresponse().read().decode('utf-8')

    res=json.loads(response)


    if res['result']['action']=='phone-number':
        message=get_by_phone(phone_number=text_message)
        print(message)

    else:
        message=get_by_name(name=text_message)


    if type(message) is not str:
        mes=message['message']
        url=message['url']

        button=web_button(
            title="Click for more results",
            url=url
        )

        buttons=[button]
        messenger_bot.send_action(recipient_id=recipient_id, action="typing_on")
        re=messenger_bot.send_button_message(recipient_id=recipient_id, buttons=buttons, text=mes)
        print(re)



    else:
        if message:
            messenger_bot.send_action(recipient_id=recipient_id, action="typing_on")
            messenger_bot.send_text_message(recipient_id=recipient_id, message=message)

            message="Sorry, I couldn't understand your input. Type your person's full name or mobile number to get details."
            messenger_bot.send_action(recipient_id=recipient_id, action="typing_on")
            messenger_bot.send_text_message(recipient_id=recipient_id, message=message)

        else:
            message="Looks like there is a little bit of a problem. Type your name/ phone number to get details"
            messenger_bot.send_action(recipient_id=recipient_id, action='typing_on')
            messenger_bot.send_text_message(recipient_id=recipient_id, message=message)



def get_facebook_details(user_id):
    fields = 'first_name,last_name,profile_pic,locale,timezone,gender'

    base_url = 'https://graph.facebook.com/v2.6/' + user_id

    my_data = {
        'fields': fields,
        'access_token': page_access_token
    }

    r = requests.get(url=base_url, params=my_data)

    profile_data = r.json()

    return profile_data


def get_emoji(number):
    size = 0
    temp = number

    # get the size of the number.....
    while (number) > 0:
        size += 1
        number = number // 10

    res = []
    div = pow(10, size - 1)

    # break the number down........
    for l in range(size - 1):
        res.append(temp // div)
        temp = temp % div
        div = div // 10

    res.append(temp)

    # the final emoji here
    emoji = ''
    for l in res:
        emoji += number_emojis[l]
    return emoji


def get_by_phone(phone_number):
    if len(phone_number)>10:
        phone_number=phone_number[-10:]

    print(phone_number)

    data = {
        'auth_token': 'A525CKA30B760953CC8018C57C49FDA8',
    }

    url=main_url+'/mobile/'+phone_number

    res=requests.get(url=url, params=data)

    if res.status_code==200:
        try:
            res = res.json()
        except:
            res = {}

        message = ''

        print(res)

        for k, v in res.items():
            if v is not None and v is not "":
                message = message + "❇️" + k.upper() + "➡️" + str(v) + "\n\n"

        if message == '':
            message = "Looks like we could not find any details. Make sure the provided number is correct"

        return message

    else:
        message='Looks like we could not find any details. Make sure the provided number is correct'

        return message


def get_by_name(name):
    name=name.strip(' ').lower()
    data = {
        'auth_token': 'A525CKA30B760953CC8018C57C49FDA8',
    }

    url=main_url+'/name/'+name

    res=requests.get(url=url, params=data)

    try:
        res=res.json()
    except:
        res=[]


    message = ''



    if len(res)>2:
        for l in range(2):
            title = "RESULT   " + get_emoji(l + 1) + "\n\n"
            message = message + title
            for k, v in res[l].items():
                if v is not None and v is not "":
                    message = message + "❇️" + k.upper() + "➡️" + str(v) + "\n\n"

        res={}
        url='http://www.mobilenumbertracker.com/person-finder?query='+name
        res['message']=message
        res['url']=url

        return res

    else:
        for l in range(len(res)):
            title = "RESULT   " + get_emoji(l + 1) + "\n\n"
            message = message + title
            for k, v in res[l].items():
                if v is not None and v is not "":
                    message = message + "❇️" + k.upper() + "➡️" + str(v) + "\n\n"


    if message=='':
        message='Looks like we could not find any details. Make sure the provided name is correct'

    return message

def web_button(title, url):
    button={
        'type': 'web_url',
        'title': title,
        'url': url
    }

    return button





