import youtube_dl
from selenium import webdriver
# import uiautomation as auto
import codecs
import time
import win32api
import googleapiclient.discovery
import pickle
import os.path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Video:
    def __init__(self, key, banned_bands, banned_words, songs):
        self.banned_bands_file = banned_bands
        self.banned_words_file = banned_words
        self.songs_file = songs
        self.banned_bands = self.read_from_file(banned_bands)
        self.banned_words = self.read_from_file(banned_words, make_list=True)
        self.songs = {}
        self.read_from_file(songs, songs=True)
        self.key = list(self.read_from_file(key))[0]
        self.creds = self.register()

    def read_from_file(self, file, songs=False, make_list=False):
        if songs:
            with open(file, encoding="utf8") as f:
                content = f.readlines()
            for i in content:
                song = i.split(" -- ")[0]
                band = i.split(" -- ")[1].replace("\n", "")
                if band not in self.songs:
                    self.songs[band] = {song}
                if band in self.songs:
                    self.songs[band].add(song)
            return
        with open(file, encoding="utf8") as f:
            content = f.readlines()
        content = set(x.strip() for x in content)
        if make_list:
            return list(content)
        return content

    def register(self):
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/youtube']
        if os.path.exists(r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle'):
            with open(r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    r'C:\Users\theerik\PycharmProjects\ytvideo\credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        with open(r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle', 'rb') as token:
            creds = pickle.load(token)
        return creds

    def add_to_playlist(self, link):
        # kui video on vähemalt 2 min kestnud
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=self.creds)
        request = youtube.playlistItems().insert(part="snippet",
                                                          body={'snippet': {'playlistId': "WL",
                                                                            'resourceId': {'kind': 'youtube#video',
                                                                                           'videoId': link}}})
        try:
            request.execute()
            print("added to playlist")
        except:
            print("is in playlist")

    def add(self, song, band):
        if "(" in song or "[" in song:
            while song.count("(") == song.count(")") and song.count("(") >= 1:
                a = song.find("(")
                b = song.find(")")
                song = song[:a] + song[b + 1:]
            while song.count("[") == song.count("]") and song.count("[") >= 1:
                a = song.find("[")
                b = song.find("]")
                song = song[:a] + song[b + 1:]
        song = ' '.join(song.split())
        if band in self.songs:
            if song in self.songs[band]:
                return True
            self.songs[band].add(song)
        else:
            self.songs[band] = {song}
        with codecs.open(self.songs_file, "a", "utf-8") as file:
            file.write(f"\n{song} -- {band}")
        return False

    def add_to_banned_bands(self, band):
        if band is not None:
            self.banned_bands.add(band)
            with codecs.open(self.banned_bands_file, "a", "utf-8") as file:
                file.write(f"\n{band}")
        print(f"added {band} to banned bands")

    def dislike(self, link):
        """dislikes the video"""
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=self.creds)
        request = youtube.videos().rate(id=link, rating="dislike")
        try:
            request.execute()
            print("disliked")
        except:
            print("cant dislike for some reason")

    def get_video_api(self, link):
        """Should get a list of links to songs in the Youtube playlist with the given address."""
        vid_id = link.split("=")
        service = build("youtube", "v3", developerKey=self.key)
        request = service.videos().list(part="snippet", id=vid_id[1])
        response = request.execute()
        vid_response = response["items"][0]["snippet"]
        title = bytes(vid_response["title"],"utf-8").decode('utf-8', 'ignore')
        desc = bytes(vid_response["description"],"utf-8").decode('utf-8', 'ignore')
        for i in self.banned_words:
            if i.lower() in title.lower():
                return True, None, title, "Banned word"
        name = self.filter_name(title, desc, link)
        found = name[0]
        song = name[1]
        band = name[2]
        stored = name[3]
        if found:
            if band in self.banned_bands:
                # self.dislike(vid_id[1])
                return True, band, song, "Banned band"
            elif stored:
                return True, band, song, "Stored"
            else:
                return False, band, song
        else:
            return False, band, title

    def filter_name(self, title, description, link):
        found = False
        band = None
        song = None
        stored = False
        # checks title
        if " - " in title:
            if title.count(" - ") == 1:
                band = title.split(" - ")[0].lower()
                if band in self.songs:
                    song = title.split(" - ")[1].lower()
                    stored = self.add(song, band)
                    found = True
                    return found, song, band, stored
                band = title.split(" - ")[1].lower()
                if band in self.songs:
                    song = title.split(" - ")[0].lower()
                    stored = self.add(song, band)
                    found = True
                    return found, song, band, stored
                band = None

        # checks if it is official yt song
        else:
            lista = description.split("\n")
            if "Provided to YouTube" in lista[0]:
                song = title.lower()
                band = lista[2][lista[2].find("·") + 2:].lower()
                if "·" in band:
                    band = band[:band.find("·") - 1]
                found = True
                stored = self.add(song, band)
                return found, song, band, stored

        # if cant find by looking title and description
        ydl = youtube_dl.YoutubeDL({})
        with ydl:
            video = ydl.extract_info(link, download=False)
            if video['artist']:
                band = video['artist'].lower()
                song = video["track"].lower()
                while band[0].isalpha() is False:
                    band = band[1:]
                while song[0].isalpha() is False:
                    song = song[1:]
                found = True
                stored = self.add(song, band)
                return found, song, band, stored
        return found, song, band, stored

    def playlist_link(self, link):
        driver = webdriver.Firefox()
        driver.install_addon(r'C:\Users\theerik\PycharmProjects\ytvideo\adblock.xpi', temporary=True)
        input("Loaded...")
        # sign in
        driver.get("https://accounts.google.com/signin")
        with open(r"C:\Users\theerik\PycharmProjects\ytvideo\name.txt") as f:
            name = f.readlines()
        with open(r"C:\Users\theerik\PycharmProjects\ytvideo\pass.txt") as f:
            passs = f.readlines()
        email_phone = driver.find_element_by_xpath("//input[@id='identifierId']")
        email_phone.send_keys(name[0])
        driver.find_element_by_id("identifierNext").click()
        time.sleep(2)
        password = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='password']"))
        )
        password.send_keys(passs[0])
        driver.find_element_by_id("passwordNext").click()
        time.sleep(2)
        driver.get(link)
        input("Logged in...")
        last_url = None
        count = 1
        while True:
            url = driver.current_url
            url = url[:43]
            if last_url != url:
                count = 1
                stuff = self.get_video_api(url)
                value = stuff[0]
                band = stuff[1]
                song = stuff[2]
            else:
                count += 1

            if band is None:
                print(f"{song} [{count}/3]")
            else:
                print(f"{band} -- {song} [{count}/3]")
            n = 1000
            times = 0
            if value is False:
                while True:
                    times += 1
                    n -= 1
                    if n <= 0:
                        num2 = 2
                        b2 = 2
                        break
                    if count == 3:
                        vid_id = url.split("=")
                        count += 1
                        self.add_to_playlist(vid_id[1])
                    num = win32api.GetKeyState(0x13)  # pause/break
                    b = win32api.GetKeyState(0x90)  # numlock
                    if num < 0:
                        num2 = num
                        b2 = b
                        vid_id = url.split("=")
                        self.dislike(vid_id[1])
                        with codecs.open(self.songs_file, "a", "utf-8") as file:
                            file.write(f" -- {times}")
                        elem = driver.find_element_by_xpath('//*[@class="ytp-next-button ytp-button"]')
                        elem.click()
                        break
                    if b < 0:
                        num2 = num
                        b2 = b
                        vid_id = url.split("=")
                        self.add_to_banned_bands(band)
                        self.dislike(vid_id[1])
                        elem = driver.find_element_by_xpath('//*[@class="ytp-next-button ytp-button"]')
                        elem.click()
                        break
                    time.sleep(0.05)
                while True:
                    num = win32api.GetKeyState(0x13)
                    b = win32api.GetKeyState(0x90)
                    if num2 != num:
                        break
                    if b2 != b:
                        break
                    time.sleep(0.1)
            else:
                reason = stuff[3]
                print(f"skipping: {reason}")
                vid_id = url.split("=")
                self.dislike(vid_id[1])
                elem = driver.find_element_by_xpath('//*[@class="ytp-next-button ytp-button"]')
                elem.click()
            last_url = url
            time.sleep(1.5)

if __name__ == "__main__":
    v = Video(r"C:\Users\theerik\PycharmProjects\ytvideo\key.txt",
              r"C:\Users\theerik\PycharmProjects\ytvideo\bannedbands.txt",
              r"C:\Users\theerik\PycharmProjects\ytvideo\bannedwords.txt",
              r"C:\Users\theerik\PycharmProjects\ytvideo\songs.txt")
    print("loaded")
    link = str(input("link: "))
    v.playlist_link(link)
