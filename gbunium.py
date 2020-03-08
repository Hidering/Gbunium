import lxml
from pandas import DataFrame
from urllib import parse

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import time
import json

class Gbubot():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")

    driver = webdriver.Chrome('/usr/bin/chromedriver', chrome_options=chrome_options)
    print("[Gbubot 생성] ")
    driver.implicitly_wait(3)

    selector={"date":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-count > div.count > span.date",
              "author":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-header > span > a",
              "title":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-header > h3 > a",
              "content":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-content",
              "ncomment":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-count > div.count > span.comment-num > a",
              "nrecommend":"#btn_vote_up > span.btn__txt > em",
              "fileUrl":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.attached-file > ul > li > a",
              "srcUrl":"#content-wrap > div.board-wrap > div.board-view > div.post-wrap > div.post-content"                
              }
    
    def __init__(self):
        pass

    def get_comment(self, soup):
        '''
        soup에서 댓글들(comments)을 찾아 반환합니다.
        '''
        commentItems = soup.find_all("div", {"class":"comment-item"})
        result = []

        for i in range(0,len(commentItems)-1):
            try:
                to = commentItems[i].get("data-head")
                author = commentItems[i].find("span", {"class":"global-nick nick"})
                content = commentItems[i].find("span", {"class":"cmt"})
                date = commentItems[i].find("span", {"class":"date-line"})        

                author = author.text.strip()
                content = content.text.strip()
                date = date.text.strip()

                result.append([author, content, date, to])
            except:
                result.append(["","삭제 된 댓글입니다.","",""])            

        return result

    def get_title(self, soup):
        '''
        soup에서 title(제목)을 찾아서 반환합니다.
        '''
        title = soup.select(self.selector["title"])
        title = title[0].text or "-"
        title = title.replace("'", "^")
        title = title.replace('"', "^")

        return title

    def get_content(self, soup):
        '''
        soup에서 내용(content)을 찾아서 반환합니다.
        '''
        content = soup.select(self.selector["content"])
        content = content[0].text.strip() or "-"
        content = content.replace("'", "^")
        content = content.replace('"', "^")

        return content

    def get_file_list(self, soup):
        ourl = "http://www.ilbe.com"
        fileUrl = soup.select(self.selector["fileUrl"])

        if (fileUrl is None) or (fileUrl == []):
            fileUrl = [""]            
        else:
            i = 0
            for file_url in fileUrl:
                fileUrl[i] = ourl+file_url.get("href")
                i += 1
        
        return fileUrl
    
    def get_source_list(self, soup):
        srcList = [] 
        srcUrl = soup.select(self.selector["srcUrl"])

        # 본문에 삽입한 이미지 또는 영상 url (이미지인지, 유튜브영상인지 조건에따라 구분해줘야함)        
        for src in srcUrl:
            # iframe 태그
            if src.find("iframe") is None:
                pass
            else:
                srcList.append(src.find("iframe").get("src"))

            # image 태그
            if src.find("img") is None:
                pass
            else:
                srcList.append(src.find("img").get("src"))
        
        if srcList is None or len(srcList) == 0:
            srcList = [""]

        return srcList

    def get_article(self, url):
        self.driver.get(url)
        time.sleep(3)
        html = self.driver.page_source
        soup = bs(html, 'lxml')  

        date = soup.select(self.selector["date"])
        author = soup.select(self.selector["author"])
        ncomment = soup.select(self.selector["ncomment"])
        nrecommend = soup.select(self.selector["nrecommend"])        

        date = date[0].text or "-"
        author = author[0].text or "-"     
        ncomment = ncomment[0].text or "-"
        nrecommend = nrecommend[0].text or "-"

        result_dict = {
            "date": date, 
            "author": author, 
            "title": self.get_title(soup),
            "content": self.get_content(soup), 
            "ncomment": ncomment, 
            "nrecommend": nrecommend, 
            "url": url,
            "file_url_list": self.get_file_list(soup),
            "src_url_list": self.get_source_list(soup),
            }

        return result_dict

    def login(self):
        print('[실행] bot.login')

        # 1. 로그인 페이지 요청
        self.driver.get('http://www.ilbe.com/member/loginform')
        time.sleep(3)
        # print(self.driver.page_source)
        
        # 2. 로그인 정보 입력
        user_id = '*'
        pw = '*'
        self.driver.execute_script("document.getElementsByName('user_id')[0].value=\'" + user_id + "\'")
        self.driver.execute_script("document.getElementsByName('password')[0].value=\'" + pw + "\'")
        time.sleep(2)

        # 3. 제출 버튼 클릭
        self.driver.find_element_by_xpath("//*[@id='loginForm']/div/button/span").click()


    def write(self, title, content, img_src=''):
        print("[실행] bot.write")
        
        # 1. 글작성 페이지 요청
        self.driver.get("http://www.ilbe.com/writeform/animation")
        time.sleep(2)
        
        # 2. 제목 작성
        self.driver.execute_script("document.getElementsByName('title')[0].value=\'" + title + "\'")
        time.sleep(1)

        # 3. 사진 첨부
        # html 편집 모드     
        self.driver.find_element_by_xpath('//*[@id="cke_37_label"]').click()
        write_form_element = self.driver.find_element_by_xpath('//*[@id="cke_1_contents"]')
        ActionChains(self.driver).click(write_form_element).pause(1).perform()

        # print(img_src)
        html_content = f'<img src="{img_src}" /><br />{content}<br />'

        ActionChains(self.driver).send_keys(html_content).send_keys(Keys.RETURN).perform() 
        time.sleep(1)
        
        # 4. 제출 버튼 클릭
        submit_element = self.driver.find_element_by_xpath("//*[@id='writeForm']/div[4]/div[2]/div/button[4]")
        submit_element.click()
        time.sleep(2)

        return self.driver.current_url

    def search_articles(self, search_target, search_type="nick_name",list_size=5, list_style="list", page="1"):
        '''
        닉네임 검색
        '''
        url = "http://www.ilbe.com/list/animation"
        # 한글을 %인코딩으로 변환
        search_target_enc = parse.quote(search_target)
        
        search_url = f'{url}?search={search_target_enc}&searchType=nick_name&listSize={list_size}&listStyle={list_style}&page={page}'
        
        # print("search_url", url)
        self.driver.get(search_url)
        time.sleep(2)
        
        if list_style == "list":
            
            xpath = '/html/body/div[1]/div[2]/div[1]/div[1]/div[3]/ul/li/span[2]/a'
            elements = self.driver.find_elements_by_xpath(xpath)            
            title_list = [element.text for element in elements]
            url_list = [element.get_attribute('href')[0:36] for element in elements]

            # 공지사항 제거            
            nickname_xpath = '//*[@id="content-wrap"]/div[1]/div[3]/ul/li/span[3]'
            elements = self.driver.find_elements_by_xpath(nickname_xpath)
            nickname_list = [element.text for element in elements]            

            # 작성자가 일치하는 글 갯수 확인
            article_counter = 0
            for nickname in nickname_list:
                if nickname.lower() == search_target:
                    article_counter += 1

            # 일치하는 글 갯수가 0이면 작성글 없음
            if article_counter == 0:
                return '작성글이 없습니다.'

            # 아니라면 슬라이싱으로 가져오기            
            else:
                title_list = title_list[-article_counter:]
                url_list = url_list[-article_counter:]

            for i in range(len(title_list)):
                title_list[i] = title_list[i].replace("'", "^")
                title_list[i] = title_list[i].replace('"', "^")                
                        
            result_dict = {
                'title_list' : title_list,
                'url_list' : url_list,
                'url' : f'{url}?search={search_target}&searchType=nick_name&listSize=50&listStyle=webzine&page=1'
            }
         
        return result_dict


    def get_articles(self, list_size=5, list_style="list", page="1"):
        ourl = "http://www.ilbe.com"
        url = "http://www.ilbe.com/list/animation"

        url = f'{url}?listSize={list_size}&listStyle={list_style}&page={page}'
        self.driver.get(url)
        time.sleep(3)
        html = self.driver.page_source

        soup = bs(html, 'lxml')
        soup2 = soup.select('#content-wrap > div.board-wrap')
        titleList = soup2[0].select('li > span > a.subject')
        authorList = soup2[0].select('li > span.global-nick > a')
        urlList = soup2[0].select('li > span.title > a')

        # 공지사항, 광고 제거
        # 공지사항이나 광고는 맨 위에 있으므로 아래에서부터 가져오도록 하면 된다.
        titleList = titleList[-list_size:]
        urlList = urlList[-list_size:]
        for i in range(0, list_size):
            authorList[i] = authorList[i].text.strip()  
            titleList[i] = titleList[i].text.strip()
            titleList[i] = titleList[i].replace("'", "^")
            titleList[i] = titleList[i].replace('"', "^")

            urlList[i] = ourl+ (urlList[i].get("href"))[0:17]        

        articles = DataFrame({'author':authorList, 'title':titleList, 'url':urlList})

        return articles


def get_db_login_info():
    '''
    DB 로그인 정보
    '''
    with open("./config.json") as json_file:
        json_data = json.load(json_file)

    db_info = json_data['db_info']
    HOST = db_info['HOST']
    USER = db_info['USER']
    PW = db_info['PW']
    DB = db_info['DB']
    CHARSET = db_info['CHARSET']    

    return HOST, USER, PW, DB, CHARSET

def get_token():
    '''
    bot token값
    '''
    with open("./config.json") as json_file:
        json_data = json.load(json_file)

    token = json_data["bot_token"]    
    return token

def get_watching_list():
    f = open("ggbuta_list.txt", 'rt')

    watching_list = [name.strip() for name in f.readlines()]
    f.close()

    return watching_list

