import requests, json
from PIL import Image
from GoodFuncs import UsefulFunctions


class User():
    def __init__(self, username, createErrors=True) -> None:
        self.usefulFuncs = UsefulFunctions(base_url="NahManImNotUsingAnythingThatRequiresThisForThisSpecificPythonFile")
        self.createErrors = createErrors
        
        self.valid = True
        self.username = username
        self.UUID = self._getUUID()

        self.face_url = f"https://api.mineatar.io/face/{self.UUID}"
        self.head_url = f"https://api.mineatar.io/head/{self.UUID}"
        self.full_body_url = f"https://api.mineatar.io/body/full/{self.UUID}"
        self.skin_url = f"https://api.mineatar.io/skin/{self.UUID}"

        self.face = None
        self.head = None
        self.full_body = None
        self.skin = None

    def _getUUID(self):
        try:
            res = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{self.username}")
            jsonData = json.loads(res.content)
            print(jsonData)
            return jsonData["id"]
        except KeyError as e:
            self.valid = False
            if self.createErrors:
                raise NameError(f"Could not find user: {self.username}! \nError: {e}")
            return "N/A"
                
    def _getImage(self, url):
        return self.usefulFuncs.getPILImageFromURL(url)

    def refreshData(self):
        self.face = None
        self.head = None
        self.full_body = None
        self.skin = None

    def returnUsername(self):
        return self.username

    def returnUUID(self):
        return self.UUID
    
    def returnFace(self, returnurl=False):
        if returnurl:
            return self.face_url
        if not self.face:
            self.face = self._getImage(self.face_url)
        return self.face
    
    def returnHead(self, returnurl=False):
        if returnurl:
            return self.head_url
        if not self.head:
            self.head = self._getImage(self.head_url)
        return self.head
    
    def returnFullBody(self, returnurl=False):
        if returnurl:
            return self.full_body_url
        if not self.full_body:
            self.full_body = self._getImage(self.full_body_url)
        return self.full_body
    
    def returnSkin(self, returnurl=False):
        if returnurl:
            return self.skin_url
        if not self.skin:
            self.skin = self._getImage(self.skin_url)
        return self.skin
    
    def validUser(self):
        return self.valid
    

class Server():
    def __init__(self, server_address) -> None:
        self.valid = True
        self.server_address = server_address
        
        self.refreshData()

        self.players_usernames = []
        for p in self.players:
            self.players_usernames.append(p["name_clean"])

    def _getData(self):
        res = requests.get(f"https://api.mcstatus.io/v2/status/java/{self.server_address}")
        self.data = json.loads(res.content)

    def refreshData(self):
        self._getData()

        self.online = self.data["online"]
        self.server_ip_address = self.data["ip_address"]
        self.server_port = self.data["port"]

        self.server_name = ""
        self.mods = []
        self.plugins = []

        self.player_max = -1
        self.player_count = -1
        self.players = []

        if self.online:
            self.server_name = self.data["motd"]["clean"]

            self.mods = self.data["mods"]
            self.plugins = self.data["plugins"]

            self.player_max = self.data["players"]["max"]
            self.player_count = self.data["players"]["online"]
            self.players = self.data["players"]["list"]

    def serverOnline(self):
        return self.online

    def returnName(self):
        return self.server_name
    
    def returnAddress(self):
        return self.server_address
    
    def returnIPAddress(self):
        return self.server_ip_address
    
    def returnPort(self):
        return self.server_port

    def returnMods(self):
        return self.mods
    
    def returnPlugins(self):
        return self.plugins
    
    def returnPlayers(self):
        return self.players
    
    def returnPlayersUsernames(self):
        return self.players_usernames
    
    def returnPlayersOnline(self):
        return self.player_count
    
    def returnPlayerMax(self):
        return self.player_max
    
    def validServer(self):
        return self.valid
    