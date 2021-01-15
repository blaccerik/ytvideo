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
# import pickle
# import os.path


class Youtube:
    def __init__(self, link, songslink, bannedbandslink, bannedwordslink):
        with open(link) as f:
            item = f.read().splitlines()
        self.name = item[0]
        self.password = item[1]
        self.songs = {}
        self.songslink = songslink
        self.bannedbandslink = bannedbandslink
        self.read_from_file(songslink, songs=True)
        self.bannedbands = self.read_from_file(bannedbandslink, make_set=True)
        self.bannedwords = self.read_from_file(bannedwordslink, make_list=True)

    def read_from_file(self, file, songs=False, make_set=False, make_list=False):
        with open(file, encoding="utf8") as f:
            content = f.readlines()
        if songs:
            for i in content:
                i = i.replace("\n", "").lower()
                song = i.split(" -- ")[0]
                band = i.split(" -- ")[1]
                if "(" in song:
                    print(song, band)
                if band not in self.songs:
                    self.songs[band] = {song}
                if band in self.songs:
                    self.songs[band].add(song)
        elif make_set:
            return set(x.strip().lower() for x in content)
        elif make_list:
            return list(x.strip().lower() for x in content)

    def log_in(self, driver):
        # fixi et ta ei tule seda lisalehte lahti plz
        driver.install_addon(r'C:\Users\theerik\PycharmProjects\ytvideo\adblock.xpi', temporary=True)
        input("Loaded...")
        # sign in
        driver.get("https://accounts.google.com/signin")
        email_phone = driver.find_element_by_xpath("//input[@id='identifierId']")
        email_phone.send_keys(self.name)
        driver.find_element_by_id("identifierNext").click()
        time.sleep(2)
        password = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='password']"))
        )
        password.send_keys(self.password)
        driver.find_element_by_id("passwordNext").click()
        time.sleep(2)

    def fix_song_name(self, song):
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
        return song

    def video(self, title, desc, link):
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
        found = False
        band = None
        song = None
        if " - " in title:
            if title.count(" - ") == 1:
                lista = title.split(" - ")
                band = lista[0].lower()
                song = lista[1].lower()
                if band in self.songs:
                    song = self.fix_song_name(song)
                    found = True
                    return found, song, band
                # song = band
                # band = song
                elif song in self.songs:
                    band = self.fix_song_name(band)
                    found = True
                    return found, band, song
                else:
                    band = None
                    song = None
        else:
            lista = desc.split("\n")
            if "Provided to YouTube" in lista[0]:
                song = title.lower()
                band = lista[2][lista[2].find("·") + 2:].lower()
                if "·" in band:
                    band = band[:band.find("·") - 1]
                found = True
                return found, song, band

        ydl = youtube_dl.YoutubeDL({})
        with ydl:
            video = ydl.extract_info(link, download=False)
            if video['artist']:
                band = video['artist'].lower()
                song = video["track"].lower()
                song = self.fix_song_name(song)
                while band[0].isalpha() is False:
                    band = band[1:]
                while song[0].isalpha() is False:
                    song = song[1:]
                found = True
                return found, song, band
        return found, song, band

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
        time.sleep(1)
        driver.get(link)
        input("Loaded2..")
        last_url = None
        times = 0
        while True:
            # new video
            url = driver.current_url
            url = url[:43]
            skip = False
            if last_url != url:
                count = 1
                title = driver.find_element_by_xpath(
                    "//*[@class='title style-scope ytd-video-primary-info-renderer']").text
                desc = driver.find_element_by_xpath("//*[@id='content'][@class='style-scope ytd-expander']").text
                some = self.video(title, desc, url)
                found = some[0]
                song = some[1]
                band = some[2]
                if self.check_title(title):
                    self.skip(driver)
                    skip = True
                elif found:
                    if self.stored(song, band):
                        self.skip(driver)
                        skip = True
            else:
                count += 1
            if not skip:
                if found:
                    display = f"{song} -- {band} -- [{count}/3]"
                else:
                    display = f"{title} -- [{count}/3]"
                print(display)
                if count == 3:
                    print("add to playlist")
                # detect keypress
                n = 0
                while n < 900:
                    n += 1
                    times += 1
                    num = win32api.GetKeyState(0x13)  # pause/break
                    b = win32api.GetKeyState(0x90)  # numlock
                    if num < 0:
                        self.add(song, band, times)
                        self.skip(driver)
                        times = 0
                        break
                    if b < 0:
                        self.add(song, band, times)
                        self.add_to_banned_bands(band)
                        self.skip(driver)
                        times = 0
                        break
                    time.sleep(0.05)
            last_url = url
            time.sleep(1.5)

            # input("...")
            # driver.find_element_by_xpath("//*[@id='top-level-buttons']/ytd-toggle-button-renderer[2]/a").click()
            # input("tere")
            # driver.find_element_by_xpath('//*[@class="ytp-next-button ytp-button"]').click()
            # break


if __name__ == "__main__":
    y = Youtube(r"C:\Users\theerik\PycharmProjects\ytvideo\namepass.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\songs.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\bannedbands.txt",
                r"C:\Users\theerik\PycharmProjects\ytvideo\bannedwords.txt")
    print(y.songs)
    print(y.bannedbands)
    print(y.bannedwords)

    # self.songs = {}
    # self.songslink = songslink
    # self.bannedbandslink = bannedbandslink
    # self.read_from_file(songslink, songs=True)
    # self.bannedbands = self.read_from_file(bannedbandslink, make_set=True)
    # self.bannedwords = self.read_from_file(bannedwordslink, make_list=True)



    # link = "https://www.youtube.com/watch?v=_7ctaqEFJoA&list=RD_7ctaqEFJoA&start_radio=1&t=0"
    # link = input("Link: ")
    # y.main(link)

    # print(y.add("gold","imagine dragons", 123))
    # print(y.add("gold2", "imagine dragons2", 123))
    # print(y.video("Goodbye - Imagine dragons", "imagine dragons"))
    # print(y.fix_song_name("ero(deee)le(eeee)(wewe)[ewewew]"))
    # y.video("Imagine dragons - Goodbye", "imagine dragons")
    # y.main("https://www.google.com/")


    # print("loaded")
    # link = str(input("link: "))
    # v.playlist_link(link)