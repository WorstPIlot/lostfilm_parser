#!/usr/bin/python3
# -*- coding: utf-8 -*-

import telebot
import os
from datetime import datetime
from telebot import types
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
from credentials import mail, password
from api_token import token

bot = telebot.TeleBot(token)
url = 'https://www.lostfilm.tv'
temp_dict = {}


def exists(filename):
    # Проверяем существет ли файл
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)):
        return True
    else:
        return False


def write_file_from_dict(dict_name, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for item in dict_name.items():
            file.write(str(item) + '\n')


def read_saved_dict(filename):
    if exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                symbol = ['(', ')', '\'', '\n']
                for i in symbol:
                    line = line.replace(i, '')
                userid = line.split(',')[0]
                firstname = line.split(',')[1]
                temp_dict[userid] = firstname
        return True
    else:
        return False


def save_dict_to_file(dict_name, filename):
    read_saved_dict(filename)
    if temp_dict != dict_name:
        write_file_from_dict(dict_name, filename)
    temp_dict.clear()


def error_apologies(message):
    bot.send_message(message.chat.id, 'Похоже сайт ответил не так как мы ожидали, или упал. Попробуйте ещё раз позже.')


def time_date_now():
    return str(datetime.date(datetime.now())) + ' ' + str(datetime.time(datetime.now()))


read_saved_dict('users.txt')
users = temp_dict.copy()
print(users)
if len(temp_dict) > 0:
    temp_dict.clear()
read_saved_dict('admins.txt')
admins = temp_dict.copy()
print(admins)
if len(temp_dict) > 0:
    temp_dict.clear()


@bot.message_handler(commands=['start'])
def start_message(message):
    text = ''
    if str(message.chat.id) not in users.keys():
        text = ('Добро пожаловать ' + message.chat.first_name + '! Для поиска по сериалам на сайте lostfilm, '
                                                                'воспользуйтесь командой /search')
        users[str(message.chat.id)] = message.chat.first_name
        save_dict_to_file(users, 'users.txt')
    elif str(message.chat.id) in users.keys():
        text = 'Я вас помню ' + message.chat.first_name + ', нет нужды отправлять start дважды)'
    bot.send_message(message.chat.id, text)
    print(users)


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, '''/search для поискового запроса
    /help для вывода этой справки''')
    

@bot.message_handler(commands=['search'])
def start_message(message):
    bot.send_message(message.chat.id, 'Хорошо, какой сериал мы ищем?')
    bot.register_next_step_handler(message, search_tv_shows)


def search_tv_shows(message):
    bot.send_message(message.chat.id, 'Выполняю запрос...')
    print(time_date_now(), message.chat.id, ' searched for ', message.text)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('user-data-dir=' + str(message.chat.id))
    with webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) as driver:
        driver.get(url)
        links_on_start_page = driver.find_elements(By.CLASS_NAME, "link")
        if links_on_start_page[4].text == 'Вход':
            links_on_start_page[4].click()
            driver.find_element(By.NAME, 'mail').send_keys(mail)
            driver.find_element(By.NAME, 'pass').send_keys(password)
            driver.find_element(By.CLASS_NAME, 'primary-btn').click()
        driver.get(url)
        search_box = driver.find_element(By.NAME, 'q')
        search_box.clear()
        search_box.send_keys(message.text)
        search_box.submit()
        if driver.title != 'Результаты поиска по запросу \'' + message.text.lower() + '\'':
            error_apologies(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            result_list = []
            for name in driver.find_elements(By.CLASS_NAME, 'name-ru'):
                if name.text.isupper():
                    result_list.append(name.text)
            if len(result_list) != 0:
                for name in result_list:
                    markup.add(types.KeyboardButton(name))
                bot.send_message(message.chat.id, 'Вот что предлагает lostfilm по вашему запросу:', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, 'К сожалению по вашему запросу мы не нашли ни одного сериала, '
                                                  'но вы можете запустить новый поиск, воспользовавшись '
                                                  'командой /search')
            bot.register_next_step_handler(message, find_seasons)


def find_seasons(message):
    bot.send_message(message.chat.id, 'Выполняю запрос...')
    print(time_date_now(), message.chat.id, ' request: ', message.text)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('user-data-dir=' + str(message.chat.id))
    with webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) as driver:
        driver.get(url)
        search_box = driver.find_element(By.NAME, 'q')
        search_box.clear()
        search_box.send_keys(message.text)
        search_box.submit()
        if driver.title != 'Результаты поиска по запросу \'' + message.text.lower() + '\'':
            error_apologies(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            driver.find_element(By.CLASS_NAME, 'name-ru').click()
            global tv_show_url
            tv_show_url = driver.current_url
            try:
                driver.find_elements(By.CLASS_NAME, 'item')[6].click()
                seasons_list = driver.find_elements(By.TAG_NAME, 'h2')
                latest_season = 1
                latest_season_name = seasons_list[latest_season]
                count_of_unavailable_episodes = driver.find_elements(locate_with(By.CLASS_NAME, 'not-available'))
                if len(count_of_unavailable_episodes) != 0:
                    child = count_of_unavailable_episodes[0].find_elements(By.XPATH, ".//*")
                    if child[3].text == latest_season_name.text + ' 1 серия':
                        latest_season = 2
                if seasons_list[latest_season:] == 0:
                    bot.send_message(message.chat.id, 'Мы не смогли найти у сериала ни одного сезона. Может быть '
                                                      'сериал ещё только-только анонсирован?')
                for season in seasons_list[latest_season:]:
                    markup.add(types.KeyboardButton(season.text))
                bot.send_message(message.chat.id, 'Какой сезон вы хотите?:', reply_markup=markup)
                bot.register_next_step_handler(message, search_for_torrents)
                global tv_show_name
                tv_show_name = driver.find_element(By.CLASS_NAME, 'title-ru').text
            except IndexError:
                error_apologies(message)


def search_for_torrents(message):
    bot.send_message(message.chat.id, 'Выполняю запрос...')
    print(time_date_now(), message.chat.id, ' request: ', message.text)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('user-data-dir=' + str(message.chat.id))
    with webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) as driver:
        driver.get(tv_show_url)
        if not tv_show_name.lower() in driver.title.lower():
            error_apologies(message)
        else:
            driver.find_elements(By.CLASS_NAME, 'item')[6].click()
            seasons_list = driver.find_elements(By.TAG_NAME, 'h2')
            for season in seasons_list:
                if season.text == message.text:
                    break
            download_season = driver.find_element(locate_with(By.CLASS_NAME, 'external-btn').below(season))
            if download_season.get_attribute('class') == 'external-btn inactive':
                bot.send_message(message.chat.id, 'Сезон ещё не завершён. Пытаюсь получить ссылки '
                                                  'на уже вышедшие серии неполного сезона...')
                download_episodes = driver.find_elements(locate_with(By.CLASS_NAME, 'beta').below(season))
                list_of_episodes = []
                for episode in download_episodes:
                    if message.text in episode.text:
                        download_episode = driver.find_element(locate_with(By.CLASS_NAME, 'external-btn').to_right_of(
                            episode))
                        if download_episode.get_attribute('class') != 'external-btn inactive':
                            list_of_episodes.append(episode)
                    else:
                        break
                for title in list_of_episodes:
                    download_episode = driver.find_element(locate_with(By.CLASS_NAME, 'external-btn').to_right_of(
                        title))
                    download_episode.click()
                    driver.switch_to.window(driver.window_handles[1])
                    WebDriverWait(driver, random.randint(15, 30)).until(EC.presence_of_element_located((By.TAG_NAME, 'a'
                                                                                                        )))
                    text = []
                    for i in driver.find_elements(By.TAG_NAME, 'a'):
                        if i.text != '':
                            text.append(i.text)
                    description = []
                    for i in driver.find_elements(By.CLASS_NAME, 'inner-box--desc'):
                        description.append(i.text)
                    position = 0
                    for i in range(2, len(text) + len(description), 3):
                        text.insert(i, description[position])
                        if not position + 1 > len(description):
                            position += 1
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    bot.send_message(message.chat.id, '\n'.join(text))
            else:
                download_season.click()
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                WebDriverWait(driver, random.randint(15, 30)).until(EC.presence_of_element_located((By.TAG_NAME, 'a'
                                                                                                    )))
                text = []
                for i in driver.find_elements(By.TAG_NAME, 'a'):
                    if i.text != '':
                        text.append(i.text)
                description = []
                for i in driver.find_elements(By.CLASS_NAME, 'inner-box--desc'):
                    description.append(i.text)
                position = 0
                for i in range(2, len(text) + len(description), 3):
                    text.insert(i, description[position])
                    if not position + 1 > len(description):
                        position += 1
                bot.send_message(message.chat.id, '\n'.join(text))


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, 'Пожалуйста отправьте сначала /search')


bot.polling()
