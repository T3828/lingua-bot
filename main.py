import time
import requests
from bs4 import BeautifulSoup
from urllib3 import disable_warnings
import json
import os
import random
import sys
disable_warnings()

def ans_error(ms):
    raise ValueError(ms)

def get_value(element):
    return element["value"]

class Bot:
    def __init__(self):
        self.session=requests.session()
        self.url='https://www.linguaporta.jp/user/seibido/index.php'
        self.header={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
        }
        self.unit_num=0

    def login(self,user:str,pswd:str):
        data={
            "login":"login",
            "id":user,
            "password":pswd
        }
        r=self.session.post(self.url,data=data,verify=False)
        return r

    def main_post(self,main:str,num=70):
        data={
            "main":main,
            "reference_num":num
        }
        r=self.session.post(self.url,data=data,headers=self.header)
        return r

    def action(self,action:str):
        data={
            "action":action
        }
        r=self.session.post(self.url,data=data,headers=self.header)
        return r

    def select_unit(self,unit_num:int,type_num:int,sub:int):
        self.unit_num=unit_num
        unit_type=[1812,1813,1814,1815,1816]
        sub=["drill","history"][sub]
        data={
            "reference_num":70,
            "unit_num":unit_type[type_num]+4*(unit_num-1)//25,
            "sub":sub,
            "category_tag":True
        }
        r=self.session.post(self.url,data=data,headers=self.header)
        if sub=="history":
            data={
                "sub":"review",
                "reference_num":70,
                "unit_num":unit_type[type_num]+4*(unit_num-1)//25,
                "set_display_num":1
            }
            r=self.session.post(self.url,data=data,headers=self.header)

        return r

    def check_question(self,r):
        return "問題が有りません。" in BeautifulSoup(r.text,"lxml").find('td',{"id":"question_td"}).text

    def save_answers(self,data):
        with open("answers/{start:04d}-{end:04d}.json".format(start=self.unit_num,end=self.unit_num+24),"w",encoding='utf-8') as f:
            json.dump(data,f,indent=4,sort_keys=False,ensure_ascii=False)
            f.close()

    def load_answers(self):
        path="answers/{start:04d}-{end:04d}.json".format(start=self.unit_num,end=self.unit_num+24)
        if os.path.isfile(path):
            with open(path,"r",encoding='utf-8') as f:
                answers=json.load(f)
        else:
            data={
                "word":None,
                "meaning":None,
                "blank_word":None,
                "blank_sentence":None,
                "reorder":None,
                "dictation":None
            }
            answers={}
            for i in range(1,26):
                answers.setdefault(str(i),data.copy())

        return answers

    def meaning(self,unit:int):
        c=0
        self.main_post('study')
        r=self.select_unit(unit,1,0)
        answers=self.load_answers()
        if self.check_question(r):
            self.main_post('study')
            r=self.select_unit(unit,1,1)
            print("復習します")

        while True:
            print("正解数:{count}".format(count=c))
            b=BeautifulSoup(r.text,"lxml")
            check_time=b.find('input',{"name":"check_time"})["value"]
            q_num=int(b.find('b').text.replace(' ','').split('：')[1])
            print("問題番号:{num}".format(num=q_num))
            word=b.find('div',{"id":"question_area"}).find('div',{"id":"qu02"}).text
            print(word)
            option=list(map(get_value,b.find('div',{"id":"drill_form"}).find_all("input")))
            print(option)
            if answers[str(q_num)]["meaning"]==None:
                select=option[0]
            else:
                select=answers[str(q_num)]["meaning"]
            print(select)

            data={
            "action":"check",
            "check_time":check_time,
            "answer[0]":select
            }
            r=self.session.post(self.url,data=data,headers=self.header)
            b=BeautifulSoup(r.text,"lxml")
            if b.find("div",{"id":"true_msg"})==None:
                print("不正解")
                r=l.action('answer')
                b=BeautifulSoup(r.text,"lxml")
                select=b.find('div',{"id":"drill_form"}).text.replace('\n','').split('：')[1]
                print("正解は{ans}".format(ans=select))
            else:
                print("正解")
                c+=1

            answers[str(q_num)]["meaning"]=select
            answers[str(q_num)]["word"]=word
            r=l.action('次の問題へ')
            #time.sleep(random.randint(5,20))
            if self.check_question(r) or 25==c:
                self.save_answers(answers)
                self.main_post('study')
                print("終了")
                break

    def blank(self,unit:int):
        c=0
        self.main_post('study')
        r=self.select_unit(unit,2,0)
        answers=self.load_answers()
        if self.check_question(r):
            self.main_post('study')
            r=self.select_unit(unit,2,1)
            print("復習します")

        while True:
            print("正解数:{count}".format(count=c))
            b=BeautifulSoup(r.text,"lxml")
            check_time=b.find('input',{"name":"check_time"})["value"]
            q_num=int(b.find('b').text.replace(' ','').split('：')[1])
            print("問題番号:{num}".format(num=q_num))
            q=b.find('div',{"id":"question_area"}).find('div',{"id":"qu02"}).text
            print(q)
            sentence=b.find('div',{"id":"drill_form"}).text.replace('\n','').split('  ')
            print(sentence)
            if answers[str(q_num)]["blank_word"]==None:
                select=answers[str(q_num)]["word"]
            else:
                select=answers[str(q_num)]["blank_word"]
            if len(sentence)==1:
                select=select[0].upper()+select[1:]
            print(select)

            data={
            "action":"check",
            "check_time":check_time,
            "answer[0]":select
            }
            r=self.session.post(self.url,data=data,headers=self.header)
            b=BeautifulSoup(r.text,"lxml")
            if b.find("div",{"id":"true_msg"})==None:
                print("不正解")
                r=l.action('answer')
                b=BeautifulSoup(r.text,"lxml")
                q=b.find('div',{"class":"qu03"})
                select=q.find('input')["value"].replace(' ','')
                print("正解は{ans}".format(ans=select))
            else:
                print("正解")
                c+=1

            answers[str(q_num)]["blank_word"]=select
            if len(sentence)==1:
                answers[str(q_num)]["blank_sentence"]=select+sentence[0]
            elif sentence[1]=='.' or sentence[1]=='?':
                answers[str(q_num)]["blank_sentence"]="{} {}{}".format(sentence[0],select,sentence[1])
            else:
                answers[str(q_num)]["blank_sentence"]="{} {} {}".format(sentence[0],select,sentence[1])
            r=l.action('次の問題へ')
            #time.sleep(random.randint(5,20))
            if self.check_question(r) or 25==c:
                self.save_answers(answers)
                print("終了")
                self.main_post('study')
                break

    def reorder(self,unit:int):
        c=0
        self.main_post('study')
        r=self.select_unit(unit,3,0)
        answers=self.load_answers()
        if self.check_question(r):
            self.main_post('study')
            r=self.select_unit(unit,3,1)
            print("復習します")

        while True:
            print("正解数:{count}".format(count=c))
            b=BeautifulSoup(r.text,"lxml")
            script=b.find('script',{"language":"javascript"}).contents[0].split('\n')
            for i in script:
                if "CheckTime" in i:
                    check_time=i.split('"')[1]
            q_num=int(b.find('b').text.replace(' ','').split('：')[1])
            print("問題番号:{num}".format(num=q_num))
            if answers[str(q_num)]["reorder"]==None:
                select=answers[str(q_num)]["blank_sentence"]
            else:
                select=answers[str(q_num)]["reorder"]
            select=select.replace(' ','<>')
            print(select)

            data={
            "action":"check",
            "check_time":check_time,
            "answer":select
            }
            r=self.session.post(self.url,data=data,headers=self.header)
            b=BeautifulSoup(r.text,"lxml")
            if b.find("div",{"id":"true_msg"})==None:
                print("不正解")
                r=l.action('answer')
                b=BeautifulSoup(r.text,"lxml")
                select=b.find("div",{"class":"qu03"}).text.replace(' ','<>')
                print("正解は{ans}".format(ans=select))
            else:
                print("正解")
                c+=1

            answers[str(q_num)]["reorder"]=select
            r=l.action('次の問題へ')
            #time.sleep(random.randint(5,20))
            if self.check_question(r) or 25==c:
                self.save_answers(answers)
                print("終了")
                self.main_post('study')
                break

    def dictation(self,unit:int):
        c=0
        self.main_post('study')
        r=self.select_unit(unit,4,0)
        answers=self.load_answers()
        if self.check_question(r):
            self.main_post('study')
            r=self.select_unit(unit,4,1)
            print("復習します")

        while True:
            print("正解数:{count}".format(count=c))
            b=BeautifulSoup(r.text,"lxml")
            check_time=b.find('input',{"name":"check_time"})["value"]
            q_num=int(b.find('b').text.replace(' ','').split('：')[1])
            print("問題番号:{num}".format(num=q_num))
            if answers[str(q_num)]["dictation"]==None:
                select=answers[str(q_num)]["blank_sentence"]
            else:
                select=answers[str(q_num)]["dictation"]
            print(select)

            data={
            "action":"check",
            "check_time":check_time,
            "answer[0]":select
            }
            r=self.session.post(self.url,data=data,headers=self.header)
            b=BeautifulSoup(r.text,"lxml")
            if b.find("div",{"id":"true_msg"})==None:
                print("不正解")
                r=l.action('answer')
                b=BeautifulSoup(r.text,"lxml")
                select=b.find('div',{"id":"question_area"}).find('div',{"class":"qu03"}).find('input')["value"][1:-1]
                print("正解は{ans}".format(ans=select))
            else:
                print("正解")
                c+=1

            answers[str(q_num)]["dictation"]=select
            r=l.action('次の問題へ')
            #time.sleep(random.randint(5,20))
            if self.check_question(r) or 25==c:
                self.save_answers(answers)
                print("終了")
                self.main_post('study')
                break


l=Bot()

l.login('ユーザー名',"パスワード")
c=1
while c<2600:
    print('現在のユニット',c)
    l.meaning(c)
    l.blank(c)
    l.reorder(c)
    l.dictation(c)
    c+=25