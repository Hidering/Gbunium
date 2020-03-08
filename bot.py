#-*- coding:utf-8 -*-
import discord
from discord.ext import commands
from discord.ext.commands import Bot

import asyncio
import time, os
import json
import pathlib
import pymysql

from bs4 import BeautifulSoup as bs
import lxml
from selenium import webdriver
import numpy as np
import pandas as pd
import pickle

from gbunium import *

client = discord.Client() # 디스코드 연동

async def make_embed(article):    
    global HOST, USER, PW, DB, CHARSET

    title = article['title']
    content = article['content']
    file_url = article["file_url_list"][0]
    author_url = f"http://www.ilbe.com/list/animation?search={article['author']}&searchType=nick_name"
    
    embed=discord.Embed(color=0xffffff)
    embed.set_author(name=title, url=author_url)    
    embed.set_footer(text=f"{article['author']}")

    # Embed에 삽입, 이미지가 없을경우 예외처리
    if (article['src_url_list'][0] is not None) and (article['src_url_list'][0] != ""): # 이미지나 영상이 있다면, 이미지면 set_image method 사용, 영상이면 embed에 불가. 따로 본문에 링크써주기
        extension = article['src_url_list'][0][-3:]
        if extension in ["jpg", "gif", "png", "peg"]: 
            embed.set_image(url = article['src_url_list'][0]) # image = 가운데
        else:
            content = content + "\n" + article['src_url_list'][0]
        embed.add_field(name = article['date'], value = content) # name = 제목 # value = 글내용 (이경우에는 본문 + 사진 다운로드 링크)
    else:
        embed.add_field(name = article['date'], value = content) # name = 제목 # value = 글내용

        
    # ============== DB부 ============

    conn = pymysql.connect(host=HOST, user=USER, password=PW, db=DB, charset=CHARSET)
    cur = conn.cursor()

    fileText=""
    srcText=""
    for file_url in article["file_url_list"]:
        fileText += file_url +","
    for src_url in article["src_url_list"]:
        srcText += src_url +","

  

    sql = "INSERT INTO GGBTLIST_TBL VALUES"
    sql += f"('{article['date']}','{article['author']}','{title}'"
    sql += f",'{content}','{fileText}','{srcText}')"
    cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()

    print("  [DB 저장 완료]")
    print("[종료] make_embed")

    return embed

#################################
# 모니터링
async def monitoring():
    await client.wait_until_ready()
    global bot, oldUrlList
    
    sleep_time = 60
    counter = 0 
    channel = client.get_channel(585218618216808462)
    channel_ani = client.get_channel(681843358267604992)
        
    while not client.is_closed():
        counter += 1
        print('monitoring 횟수 :', counter)
        print('sleep 시간:', sleep_time)        
        try:
            articles = bot.get_articles(list_size = 5)
            
            # 메인화면에서 30개 글을 가져오고 아이디 체크
            for i in range(0, len(articles)):
                author = articles.iloc[i]['author']
                title = articles.iloc[i]['title']
                url = articles.iloc[i]['url']

                if url not in oldUrlList:
                    if (author not in gbu_force):
                        gbu_force[author] = 0
                        dict_file = open("gbu_force.dict", "wb")
                        pickle.dump(gbu_force, dict_file)
                        dict_file.close()
                    if (gbu_force[author] > 2):
                        embed_color = discord.Colour(color_palettes[4])
                    elif (gbu_force[author] > 0):
                        embed_color = discord.Colour(color_palettes[3])
                    elif (gbu_force[author] == 0):
                        embed_color = discord.Colour(color_palettes[2])
                    elif (gbu_force[author] < -2):
                        embed_color = discord.Colour(color_palettes[0])
                        continue
                    else:
                        embed_color = discord.Colour(color_palettes[1])
                    embed = discord.Embed(title=author, colour=embed_color, \
                                          description=title + f"  [\[>>\]]({url})")
                    await channel_ani.send(embed=embed)
                    oldUrlList.append(url)
#                    msg = f'[{author}] {title}'
#                    await channel_ani.send(msg)
                    if (author in watchingList):
                        new_head = f'[알림] {author} : {title} \n {url}'
                        article = bot.get_article(url)
                        embed = await make_embed(article) # 글, 첨부파일
                        await channel.send(new_head, embed=embed)

            if len(oldUrlList) > 11: # 중복 리스트 갯수는 10개 이하로 관리
                del oldUrlList[0:len(oldUrlList) - 11]
            sleep_time = 10
            for i in range(0, sleep_time):
                await asyncio.sleep(1)

        except Exception as e:
            print("모니터링 에러 발생")
            print(e)
            sleep_time = sleep_time*2

            for i in range(0, sleep_time):
                await asyncio.sleep(1)


#################################
# 봇 로그인

@client.event
async def on_ready():
#### 봇 로그인    
    print("[디스코드 연결]")
    # print(client.user.name)
    # print(client.user.id)
    # print("==========")
    # 이미지용 Embed 객체 생성    

#### 봇 상태메세지 설정
    act = discord.Game("애니메이션 게시판")
    await client.change_presence(status=discord.Status.online, activity=act)

#####################################################################################
@client.event
async def on_message(message):
    global lastHiTime, hiCount, watchingList, bot
    print(f'[{message.author.name}] {message.content}')

##### 0. 초기 변수설정
    if message.content == "애하":
        await message.channel.send("안녕")        

##### 1. 봇이 보낸 메세지는 무시한다.
    if message.author.bot: 
        if message.author.bot:
            return None
            
##### 2. 인사
    if message.content == "ㅎㅇ":
        
        if time.time() - lastHiTime > 10:
            await asyncio.sleep(2)
            await message.channel.send("어서오고")
            lastHiTime = time.time()
            hiCount = 0
        elif hiCount >= 5:
            await message.channel.send("적당히해라")
            hiCount += 1
            lastHiTime = time.time()
        else:
            hiCount += 1
            return None 
        
##### 3. 애게 탐색
    if message.content == "!애게":
        result_message = ""
        articles = bot.get_articles(list_size=15)
        
        for i in range(0, len(articles)):
            author = articles.iloc[i]['author']
            title = articles.iloc[i]['title']
            
            temp = f'{author} : {title}'    
            result_message = result_message + temp + "\n"      
                
        await message.channel.send(result_message)

##### 4. 추적하기 : 닉네임 검색. 글 보여주기 인덱스 추가 (190611)
    if message.content.startswith("!추적해 "):
        channel = client.get_channel(585218618216808462)         
        target_nickname = message.content[5:]
        target_nickname = target_nickname.lower()

        black_list = ['ump9']

        if target_nickname in black_list:
            search_result_url = f'http://www.ilbe.com/list/animation?search={target_nickname}&searchType=nick_name&listSize=50&listStyle=webzine&page=1'
            await channel.send(search_result_url)
        else:
            try:
                articles = bot.search_articles(target_nickname)
                embed=discord.Embed(color=0x84FA31, title=target_nickname, url=articles['url'])
                embed.set_footer(text=f'by {message.author.name}')
                if type(articles) == type('str'):
                    await message.channel.send(articles)
                else:                
                    for i in range(0, len(articles['title_list'])):  
                        title = articles['title_list'][i]
                        embed.add_field(name = articles['url_list'][i], value = title, inline=False) 
                    await message.channel.send(embed=embed)
            except:
                await channel.send("추적중 오류발생!")

##### 5. 댓글 보여주기 : 글 전체 읽기. 댓글포함
    if message.content.startswith("!댓글 "):        
        targetUrl = message.content[4:]
        commentList = bot.get_comment(targetUrl) # 댓글 리스트
        for comment in commentList:
            temp = temp + "\n ㄴ " + comment[0] + " : " + comment[1]
            
        await message.channel.send(temp)

##### 6. 감시 리스트 추가
    if message.content.startswith("!감시해 "):
        watchingTarget = message.content[5:]

        f = open("./ggbuta_list.txt", 'rt')
        watchingList = [name.strip() for name in f.readlines()]
        f.close()
        
        if watchingTarget not in watchingList:
            watchingList.append(watchingTarget)         
            f = open("./ggbuta_list.txt", 'wt')
            for user_id in watchingList:
                f.write(user_id+"\n")
            f.close()            
            await message.channel.send("감시! " + watchingTarget)
        else:
            await message.channel.send("이미 감시중임..")

##### 6-2. 감시 리스트에서 삭제
    if message.content.startswith("!감시해제 "):
        watchingTarget = message.content[6:]
        f = open("./ggbuta_list.txt", 'rt')
        watchingList = [name.strip() for name in f.readlines()]
        f.close()

        if watchingTarget in watchingList:
            watchingList.remove(watchingTarget)
            f = open("./ggbuta_list.txt", 'wt')            
            for user_id in watchingList:
                f.write(user_id+"\n")
            f.close()
            await message.channel.send("감시해제! " + watchingTarget)
        
        else:
            await message.channel.send("오류발생!")

##### 6-3. 감시 리스트 조회하기
    if message.content == "!리스트" or message.content == "!ls":                
        temp2 = ""
        for nick in watchingList:
            temp2 = (temp2+" "+nick)
        await message.channel.send("감시중! "+ temp2)

##### 8. 명령어 리스트 출력
    if message.content == "!명령어":
        text  = "!감시해 !감시해제 !리스트 \n"
        text += "!추적해 \n"
        text += "!모링 : 현재 애게글"
        await message.channel.send(text)

    if message.content.startswith("!ㅇㅂ "):
        user_nickname = message.content[4:]
        if user_nickname not in gbu_force:
            gbu_force[user_nickname] = 1
        else:
            gbu_force[user_nickname] += 1
        dict_file = open("gbu_force.dict", 'wb')
        pickle.dump(gbu_force, dict_file)
        dict_file.close()
        await message.channel.send(f'{user_nickname} 지부력: {gbu_force[user_nickname]}')

    if message.content.startswith("!ㅁㅈㅎ "):
        user_nickname = message.content[5:]
        if user_nickname not in gbu_force:
             gbu_force[user_nickname] = -1
        else:
            gbu_force[user_nickname] -= 1
        dict_file = open("gbu_force.dict", 'wb')
        pickle.dump(gbu_force, dict_file)
        dict_file.close()
        await message.channel.send(f'{user_nickname} 지부력: {gbu_force[user_nickname]}')

##### 9. DB 조회
    if message.content.startswith("!조회 "):
        global dbTime, HOST, USER, PW, DB, CHARSET

        if time.time() - dbTime > 10 :
            target = message.content[4:]            

            #####################################################################################
            conn = pymysql.connect(host=HOST, user=USER, password=PW, db=DB, charset=CHARSET)
            cur = conn.cursor()

            sql = "SELECT gbu_title, gbu_content FROM GGBTLIST_TBL WHERE gbu_author="
            sql += "'"+target+"'"
            cur.execute(sql)
            
            val = cur.fetchall()
            
            tempText = ""
            for v in val:
                if len(tempText) > 1500:
                    break
                tempText += str(v) +"\n"                

            # 6. DB 연결해제
            cur.close()
            conn.close()

            print('[DB 전송 성공]')
            await message.channel.send(tempText)
            dbTime = time.time()
        else:
            await message.channel.send("ㄱㄷ")
    
# 글 작성기능 추가
    if message.content.startswith("!글작성 ") or message.content.startswith("!ㄱㅈㅅ "):

        msg = message.content[5:]
        msgs = msg.split("|")
        url = bot.write(msgs[0], msgs[1], msgs[2])
        await message.channel.send(url)

ourl = "http://www.ilbe.com"

# Crawler - getPage에서 쓰이는 셀렉터들 (getComment에선 셀렉터가 아니라 find를 사용해서 찾음)
selector={"date":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-count > div.count > span.date",
              "author":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-header > span > a",
              "title":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-header > h3 > a",
              "content":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-content",
              "ncomment":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-count > div.count > span.comment-num > a",
              "nrecommend":"#btn_vote_up > span.btn__txt > em",
              "fileUrl":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.attached-file > ul > li > a",
              "srcUrl":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-content"                
              }

# Discord 제어
if __name__ == '__main__':
    global gbu_force, color_palettes

    color_palettes = [0xff8c94, 0xffaaa6, 0xffd3b5, 0xdcedc2, 0xa8e6ce]
    sleepTime = 1 # 동작 간격
    token = get_token()
    watchingList = get_watching_list()
    oldUrlList = [] # 실시간 감시에서 중복 방지용
    dict_file = open("./gbu_force.dict", 'rb')
    gbu_force = pickle.load(dict_file)
    dict_file.close()

    lastHiTime = time.time() # ㅎㅇ 시간체크
    dbTime = time.time()
    hiCount = 0 # ㅎㅇ 농담용 

    HOST, USER, PW, DB,CHARSET = get_db_login_info()
    print("[DB 연결]")
    # print(HOST, USER, PW, DB, CHARSET)

    bot = Gbubot()
    print("[지부봇 생성]")
    bot.login()

    client.loop.create_task(monitoring())
    client.run(token)
