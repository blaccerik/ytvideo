import youtube_dl
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import win32api
# import uiautomation as auto
# import codecs
# import win32api
# import googleapiclient.discovery
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os.path
from googleapiclient.discovery import build
# import re

class Youtube:
    def __init__(self, link, songslink, bannedbandslink, bannedwordslink, adblocklink, unknownlink):
        with open(link) as f:
            item = f.read().splitlines()
        self.name = item[0]
        self.password = item[1]
        self.songs = {}
        self.bands = set()
        self.songslink = songslink
        self.bannedbandslink = bannedbandslink
        self.unknownlink = unknownlink
        self.adblocklink = adblocklink
        self.read_from_file(songslink, songs=True)
        self.bannedbands = self.read_from_file(bannedbandslink, make_set=True)
        self.bannedwords = self.read_from_file(bannedwordslink, make_list=True)
        self.creds = self.register(r'C:\Users\theerik\PycharmProjects\ytvideo\credentials.json')
        self.key = self.read_from_file(r"C:\Users\theerik\PycharmProjects\ytvideo\key.txt")
        self.youtube = build("youtube", "v3", credentials=self.creds)
        self.service = build("youtube", "v3", developerKey=self.key)
        self.ydl = youtube_dl.YoutubeDL({})

    def read_from_file(self, file, songs=False, make_set=False, make_list=False):
        with open(file, encoding="utf8") as f:
            content = f.readlines()
        if songs:
            for i in content:
                i = i.replace("\n", "").lower()
                song = i.split(" -- ")[0]
                band = i.split(" -- ")[1]
                # if "(" in song:
                #     print(song, band)
                if band not in self.songs:
                    self.songs[band] = {song}
                    self.bands.add(band)
                if band in self.songs:
                    self.songs[band].add(song)
        elif make_set:
            return set(x.strip().lower() for x in content)
        elif make_list:
            return list(x.strip().lower() for x in content)
        else:
            return content[0]

    def register(self, cred_link):
        creds = None
        SCOPES = ['https://www.googleapis.com/auth/youtube']
        token_link = r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle'
        if os.path.exists(token_link):
            with open(token_link, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(cred_link, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_link, 'wb') as token:
                pickle.dump(creds, token)
        # ei saa aru miks see siin on
        # with open(r'C:\Users\theerik\PycharmProjects\ytvideo\token.pickle', 'rb') as token:
        #     creds = pickle.load(token)
        return creds

    def log_in(self, driver):
        driver.install_addon(self.adblocklink, temporary=True)
        while len(driver.window_handles) == 1:
            time.sleep(1)
        time.sleep(0.5)
        # sign in
        driver.get("https://accounts.google.com/signin")
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(0.5)
        email_phone = driver.find_element_by_xpath("//input[@id='identifierId']")
        email_phone.send_keys(self.name)
        driver.find_element_by_id("identifierNext").click()
        time.sleep(2)
        password = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='password']"))
        )
        password.send_keys(self.password)
        time.sleep(0.5)
        driver.find_element_by_id("passwordNext").click()

    def fix_song_name(self, song):
        if "(" in song or "[" in song:
            while song.count(")") >= 1 and song.count("(") >= 1:
                a = song.find("(")
                b = song.find(")")
                song_part = song[a + 1:b]
                while "(" in song_part:
                    song_part = song_part[song_part.find("(") + 1:]
                song = song.replace(f"({song_part})", "")
            while song.count("]") >= 1 and song.count("[") >= 1:
                a = song.find("[")
                b = song.find("]")
                song_part = song[a + 1:b]
                while "[" in song_part:
                    song_part = song_part[song_part.find("[") + 1:]
                song = song.replace(f"[{song_part}]", "")
        song = ' '.join(song.split())
        return song

    def song_not_found(self, song, id):
        info = f"\n{song} -- https://www.youtube.com/watch?v={id}"
        with open(self.unknownlink, "a", encoding="utf-8") as file:
            file.write(info)

    def dislike(self, id):
        """
        Dislike the video
        :param id:
        :return:
        """
        request = self.youtube.videos().rate(id=id, rating="dislike")
        try:
            request.execute()
            # print("disliked")
        except:
            print("cant dislike for some reason")

    def add_to_playlist(self, id):
        # kui video on vähemalt 2 min kestnud
        # youtube = googleapiclient.discovery.build("youtube", "v3", credentials=self.creds)
        # self.youtube
        playlist_link = "PL5jlSbUnZfpLH8Agff5wYyNGlFqTJfV0K"
        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={'snippet': {'playlistId': playlist_link, 'resourceId': {'kind': 'youtube#video', 'videoId': id}}})
        print(request.execute())
        # try:
        #     print(request.execute())
        #     print("added to playlist")
        # except:
        #     print("is in playlist")

    def rating(self, id):
        request = self.youtube.videos().getRating(id=id)
        res = request.execute()
        value = res["items"][0]["rating"]
        if value == "dislike":
            return False
        else:
            return True

    def skip_songs(self):
        """
        Decide which songs should be skipped at the song list at the right side of the screen
        Should use if you have watched the video prev or not
        :return:
        """

    def get_video_api(self, video_id):
        """
        Get api of the video
        :param video_id: Video id for example "fjhryr854" and NOT the full url
        :return: song, band, should skip, reason for skip
        """
        res = self.rating(video_id)
        if res:
            request = self.service.videos().list(part="snippet", id=video_id)
            response = request.execute()
            vid_response = response["items"][0]["snippet"]
            title = bytes(vid_response["title"], "utf-8").decode('utf-8', 'ignore')
            desc = bytes(vid_response["description"], "utf-8").decode('utf-8', 'ignore')
            title = title.lower()
            if self.title_has_banned_word(title):
                return True, False
            info = self.song_info(title, desc, video_id)
            found = info[0]
            if found:
                song = info[1]
                band = info[2]
                skip = self.should_skip_song(song, band)
                return skip, True, song, band
            else:
                song = info[1]
                self.song_not_found(song, video_id)
                return False, False, song
        else:
            return True, False

    def title_has_banned_word(self, title):
        """
        Check if title has a banned word in it
        :return:
        """
        for i in self.bannedwords:
            if i in title:
                return True
        return False

    def should_skip_song(self, song, band):
        """
        Decide if song should be skipped
        :param song:
        :param band:
        :return:
        """
        if band in self.bannedbands:
            return True
        if band in self.bands:
            if song in self.songs[band]:
                return True
        else:
            return False

    def song_info(self, title, desc, link):
        """
        filtreeri paremini nimi ära, isegi kui tuleb official youtube songist
        nt: nimi (midagi) siis eemalda sulud ära
        ning saa paremini aru mis bänd on
        äkki tee eraldi fail ja pane sinna ning siis ma pärast otsustan vms
        või kui saab uue bändi teada siis kontrollib sealt
        :param title:
        :param desc:
        :param link:
        :return:
        """
        # find Correct name of song and band
        found = False
        band = None
        song = None
        title = self.fix_song_name(title)
        if " - " in title:
            # title = self.fix_song_name(title)
            # print(title)
            if title.count(" - ") == 1:
                lista = title.split(" - ")
                band = lista[0]
                song = lista[1]
                if band in self.bands:
                    found = True
                    return found, song, band
                elif song in self.bands:
                    found = True
                    return found, band, song
                else:
                    band = None
                    song = None
        else:
            desc = desc.lower()
            lista = desc.split("\n")
            if "provided to youtube" in lista[0]:
                song = title
                band = lista[2][lista[2].find("·") + 2:]
                if "·" in band:
                    band = band[:band.find("·") - 1]
                found = True
                band = self.fix_song_name(band)
                return found, song, band

        with self.ydl:
            video = self.ydl.extract_info(link, download=False)
            if video['artist']:
                band = video['artist'].lower()
                song = video["track"].lower()
                song = self.fix_song_name(song)
                band = self.fix_song_name(band)
                while band[0].isalpha() is False:
                    band = band[1:]
                while song[0].isalpha() is False:
                    song = song[1:]
                found = True
                return found, song, band
        return found, title

    def skip(self, driver):
        element = driver.find_element_by_xpath('//*[@class="ytp-next-button ytp-button"]')
        element.click()

    def add_to_songs(self, song, band):
        if not self.should_skip_song(song, band):
            if band not in self.bands:
                self.bands.add(band)
                self.songs[band] = {song}
            else:
                self.songs[band].add(song)
            with open(self.songslink, "a", encoding="utf-8") as file:
                file.write(f"\n{song} -- {band}")

    def add_to_banned_bands(self, band):
        if band is not None:
            self.bannedbands.add(band)
            with open(self.bannedbandslink, "a", encoding="utf-8") as file:
                file.write(f"\n{band}")
        print(f"added {band} to banned bands")

    def main(self, link):
        """
        M ------
          kasuta apid et dislikida ja infot video kohta saada nt nimi jne
          vaata kui on dislike olemas siis skip (ei tea kas saab kontrollida)
          iga x loo tagant äkki vaata mis reccomended lood on ning pane nendele mis on stored remove
          keypress võiks kuidagi paremini detectida ning time arvutada ning ka see et kui palju loost olen kuulanud
          nt võtad loo pikkuse ja 3/4 sellest vms
          ning kui on lisatud siis lihtsalt update kiiremini et vaatata kas tuli uus lugu nt iga 10 sec tagant
          NING ka detecti kas läks main radio loopist välja ning siis lähed tagasi
        :param link:
        :return:
        """
        driver = webdriver.Firefox()
        self.log_in(driver)
        time.sleep(0.5)
        driver.get(link)
        input("Press any key")
        last_id = None
        wrote = False
        while True:
            url = driver.current_url
            url = url[:43]
            id = url[32:]
            # print(wrote)
            if last_id != id:
                if wrote:
                    with open(self.songslink, "a", encoding="utf-8") as file:
                        file.write(f" -- {time_listened}")
                    wrote = False
                data = self.get_video_api(id)
                skip = data[0]
                found = data[1]
                nth_time = 1
                time_listened = 0
            time.sleep(0.5)
            if skip:
                if found:
                    song = data[2]
                    band = data[3]
                    title = f"{song} -- {band}"
                    print(f"[SONG SKIPPED] {title}")
                else:
                    band = None
                    print(f"[SONG SKIPPED]")
                self.dislike(id)
                self.skip(driver)
            else:
                if found:
                    song = data[2]
                    band = data[3]
                    title = f"{song} -- {band}"
                    self.add_to_songs(song, band)
                    wrote = True
                else:
                    band = None
                    title = data[2]
                print(f"{title} -- [{nth_time}/3]")
                if nth_time == 3:
                    self.add_to_playlist(id)
                nth_time += 1
                n = 0
                time.sleep(1)
                while n < 60:
                    n += 1
                    time_listened += 1
                    pause = win32api.GetKeyState(0x13)  # pause/break
                    num = win32api.GetKeyState(0x90)  # numlock
                    if pause < 0:
                        with open(self.songslink, "a", encoding="utf-8") as file:
                            file.write(f" -- {time_listened}")
                        wrote = False
                        self.dislike(id)
                        self.skip(driver)
                        break
                    elif num < 0:
                        wrote = False
                        self.dislike(id)
                        self.add_to_banned_bands(band)
                        self.skip(driver)
                        break
                    time.sleep(0.1)
            last_id = id
            time.sleep(1)

if __name__ == "__main__":
    y = Youtube(r"C:\Users\theerik\PycharmProjects\ytvideo\namepass.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\songs.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\bannedbands.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\bannedwords.txt",
                r'C:\Users\theerik\PycharmProjects\ytvideo\adblock.xpi',
                r'C:\Users\theerik\PycharmProjects\ytvideo\not_found_songs.txt')
    link = "https://www.youtube.com/watch?v=V0g6AQ3kD8Q&list=RDV0g6AQ3kD8Q&start_radio=1&rv=V0g6AQ3kD8Q&t=2"
    response = str(input("Last? [y]: "))
    if response != "y":
        link = response
    y.main(link)
    
    # print(y.fix_song_name("erik() erik"))
    # print(y.fix_song_name("erikxx (Composite Edit (do not put on a/w))"))
    # print(y.fix_song_name("(aaa) erik (bb(ccc)bb)"))
    # print(y.fix_song_name("erik [Composite Edit [do not put on a/w]]"))
    # print(y.fix_song_name("[aaa] erik [bb[ccc]bb]"))

    # print(y.get_video_api("e4UKtfiX_wM"))
    # y.add_to_playlist("e4UKtfiX_wM")
    # print(y.add_to_songs('monsters', 'all time low'))

    # print(y.get_video_api("e4UKtfiX_wM"))
    # print(y.get_video_api("nLmiLR9lPf4"))
    # print(y.get_video_api("lz7JFCVPL9s"))
    # print(y.get_video_api("DHMCqPH7ksQ"))
    # print(y.get_video_api("1dcXmkco5ko"))
    # print(y.get_video_api("6jeV9szFyUY"))
    # print(y.get_video_api("y9aecCCxlnc"))

    # y.dislike("uMme1L7bvj4")

    # title = bytes("erikk(erikkkk) - test1(42443)", "utf-8").decode('utf-8', 'ignore')
    # print(title)
    # print(y.song_info("Nightcore - Ievan Polkka (VSNS Remix)", "text", "QwdbFNGCkLw"))

    # print(y.add("gold","imagine dragons", 123))
    # print(y.add("gold2", "imagine dragons2", 123))
    # print(y.video("Goodbye - Imagine dragons", "imagine dragons"))
    # print(y.fix_song_name("ero(deee)le(eeee)(wewe)[ewewew]"))
    # y.video("Imagine dragons - Goodbye", "imagine dragons")
    # y.main("https://www.google.com/")