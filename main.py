from googleapiclient.discovery import build
import youtube_dl

class Video:
    def __init__(self, banned, bands):
        self.banned = self.read_from_file(banned)
        self.bands = self.read_from_file(bands)

    def read_from_file(self, file):
        with open(file) as f:
            content = f.readlines()
        content = set(x.strip() for x in content)
        return content

    def get_video_api(self, link):
        """Should get a list of links to songs in the Youtube playlist with the given address."""
        developer_key = "AIzaSyDQ52QLbxeB4FcSEDLLsNW5rrG2EMD-OUA"
        vid_id = link.split("=")
        service = build("youtube", "v3", developerKey=developer_key)
        request = service.videos().list(part="snippet", id=vid_id[1])
        response = request.execute()
        vid_response = response["items"][0]["snippet"]
        name = self.filter_name(vid_response["title"], vid_response["description"], link)
        if name[0]:
            if name[1] in self.banned:
                dislike = 1
            return name[1]
        else:
            return name[1]


    def filter_name(self, title, description, link):
        found = False
        band = title
        # checks title
        if " - " in title:
            lista = title.split(" - ")
            for i in lista:
                if i.lower() in self.bands:
                    band = i.lower()
                    found = True
                    return found, band
            dicta = {}
            for i in lista:
                dicta[i] = description.count(i)
            # what it thinks the band is
            band_u = sorted(dicta.items(), key=lambda x: x[0])[0][0]
            if band_u.lower() in self.bands:
                band = band_u
                found = True
                return found, band
        # checks if it is official yt song
        else:
            lista = description.split("\n")
            if "Provided to YouTube" in lista[0]:
                band = lista[2][len(title) + 3:].lower()
                found = True
                return found, band

        # if cant find by looking title and description
        ydl = youtube_dl.YoutubeDL({})
        with ydl:
            video = ydl.extract_info(link, download=False)
            if video['artist']:
                band = video['artist'].lower()
                found = True
                return found, band
        return found, band


if __name__ == "__main__":
    v = Video("banned.txt", "bands.txt")
    # print(v.banned)
    # print(v.bands)
    # print(v.read_from_file("banned.txt"))
    print(1,v.get_video_api("https://www.youtube.com/watch?v=2q0UcaKjXLw"))
    print(2,v.get_video_api("https://www.youtube.com/watch?v=J2Pdgy--Yus"))
    # print(3,v.get_video_api("https://www.youtube.com/watch?v=6jeV9szFyUY"))
    print(4,v.get_video_api("https://www.youtube.com/watch?v=2k5W-j9eHcY"))