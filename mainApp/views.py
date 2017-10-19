# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from telebot import TeleBot

global bot

# Create your views here.
def index(request):
    bot = TeleBot("360267122:AAHmCyriJwzBpt5IsUIquGAxdkMtyor8xSk")
    bot.run()
    return HttpResponse("Hello", content_type='application/json')