# Import packages
import requests, json, time, os, urllib.parse
from GoodFuncs import UsefulFunctions
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from threading import Thread
from PIL import Image

class ValueUpdater():
    def __init__(self, website_base_url) -> None:
        
        self.url_format = urllib.parse.urljoin(website_base_url, "/up/world") + "/{world}/{timestamp}"

        self.vanilla = self.url_format.format(world="vanilla", timestamp="")
        self.nether = self.url_format.format(world="vanilla_nether", timestamp="")
        self.the_end = self.url_format.format(world="vanilla_the_end", timestamp="")


    def updateValues(self, region="overworld"):
        
        
        match (region):
            case "overworld":
                url_choosen = self.vanilla
            case "nether":
                url_choosen = self.nether
            case "end":
                url_choosen = self.the_end
            case _:
                url_choosen = self.vanilla    
        res = requests.get(url_choosen)

        if res.status_code != 200:
            raise ConnectionRefusedError("Status code for updateValues was not 200!")
        
        content = res.content
        data = json.loads(content)
        timestamp = data["timestamp"]
        servertime = data["servertime"]
        confighash = data["confighash"]
        player_count = data["currentcount"]
        isThundering = data["isThundering"]
        players = data["players"]
        updates = data["updates"]
        
        return {
            "timestamp": timestamp,
            "servertime": servertime,
            "confighash": confighash,
            "player_count": player_count,
            "is_thundering": isThundering,
            "players": players,
            "updates": updates
        }

class ChunkManager():
    def __init__(self, website_base_url, num_of_workers=20) -> None:

        self.NUMBER_OF_WORKERS = num_of_workers

        self.useFulFunctions = UsefulFunctions(base_url=website_base_url)

        self.timestamp = None
        self.players = None
        self.updates = None

        self.chunks: list[dict] = []

        self.transcribe_world_types = {
            "overworld": "vanilla",
            "nether": "vanilla_nether",
            "end": "vanilla_the_end",
        }

    def updateValues(self, data) -> bool:
        self.updates = data["updates"]
        self.timestamp = data["timestamp"]

    def get_chunk_image(self, chunk_x, chunk_z, region="overworld") -> Image.Image:
        currentXZ = f"{chunk_x}-{chunk_z}"
        for c in self.chunks:
            xz = f"{c['x']}-{c['z']}"
            r = c["region"]
            if currentXZ == xz and region == r:
                return c["image"]
        
        request_url = self.useFulFunctions.createChunkURL(chunk_x, chunk_z, self.transcribe_world_types[region])
        image: Image.Image = self.useFulFunctions.getPILImageFromURL(request_url).convert('RGB')

        self.chunks.append(
            {
                "x": chunk_x,
                "z": chunk_z,
                "image": image,
                "region": region,
                "world": self.transcribe_world_types[region]
            }
        )

        return image

class PlayerManager():
    def __init__(self, website_base_url, data_folder="data", chunks_folder="chunks") -> None:
        
        self.base_url = website_base_url

        self.DATA_OUT_FOLDER_PATH = data_folder
        
        i = 1
        while os.path.exists(self.DATA_OUT_FOLDER_PATH):
            self.DATA_OUT_FOLDER_PATH = f"{data_folder}-{i}"
            i += 1

        if not os.path.exists(self.DATA_OUT_FOLDER_PATH):
            os.makedirs(self.DATA_OUT_FOLDER_PATH)


        self.CHUNKS_OUT_FOLDER_PATH = os.path.join(self.DATA_OUT_FOLDER_PATH, f"{chunks_folder}")
        i = 1
        while os.path.exists(self.CHUNKS_OUT_FOLDER_PATH):
            self.CHUNKS_OUT_FOLDER_PATH = os.path.join(self.DATA_OUT_FOLDER_PATH, f"{chunks_folder}-{i}")
            i += 1

        if not os.path.exists(self.CHUNKS_OUT_FOLDER_PATH):
            os.makedirs(self.CHUNKS_OUT_FOLDER_PATH)

        self.transcribe = {
            "overworld": "vanilla",
            "nether": "vanilla_nether",
            "end": "vanilla_the_end",
        }

        self.chunk = self.setToDefault()

        self.timestamp = None
        self.servertime = None
        self.confighash = None
        self.player_count = None
        self.isThundering = None
        self.players = None
        self.updates = None

        self.useFulFunctions = UsefulFunctions(self.base_url)

        self.start_time_seconds = time.time()

    def updateValues(self, data) -> bool:
        self.timestamp = data["timestamp"]
        self.servertime = data["servertime"]
        self.confighash = data["confighash"]
        self.player_count = data["player_count"]
        self.isThundering = data["is_thundering"]
        self.players = data["players"]
        self.updates = data["updates"]

    def makeHealthBar(self, health=20) -> str:
        health = health / 2

        fullHearts = ""
        for i in range(int(health)):
            fullHearts += "❤ "

        halfHearts = ""
        hasHalfStar = False
        if str(health).endswith(".25"):
            hasHalfStar = True
            halfHearts += "💔 "

        emptyHearts = ""
        for i in range(10-int(health)):
            emptyHearts += "♡ "
        if hasHalfStar:
            emptyHearts = emptyHearts[:-1]

        return fullHearts + halfHearts + emptyHearts

    def makeArmourBar(self, armor=20) -> str:
        armor = armor / 2

        fullArmors = ""
        for i in range(int(armor)):
            fullArmors += "⛊ "

        halfArmors = ""
        hasHalfArmor = False
        if str(armor).endswith(".25"):
            hasHalfArmor = True
            halfArmors += "🛡️ "

        emptyArmors = ""
        for i in range(10-int(armor)):
            emptyArmors += "🛡 "
        if hasHalfArmor:
            emptyArmors = emptyArmors[:-1]

        return fullArmors + halfArmors + emptyArmors

    def export(self, data) -> None:
        print("\nExporting...")

        st = time.time()

        outName = f"{self.CHUNKS_OUT_FOLDER_PATH}\\chunk"
        chunk_out_path = f"{outName}-0.json"

        i = 1
        while os.path.exists(chunk_out_path):
            chunk_out_path = f"{outName}-{i}.json"
            i += 1

        with open(chunk_out_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        print("Dump time taken:", time.time() - st, "(seconds)")
        print("Outpath:", chunk_out_path)

    def setToDefault(self) -> dict:
        self.start_time_seconds = time.time()

        return {
            "start_time": str(datetime.now()),
            "end_time": "",
            "time_taken": "",
            "data": {
                
            }
        }

    def gatherChunk(self, verbose=False) -> dict:
        """Make sure to update values before running this!"""

        start_time_seconds = time.time()

        self.chunk = self.setToDefault()

        st = time.time()

        minecraftTime = self.useFulFunctions.minecraftTimeToString(self.useFulFunctions.getMinecraftTime(self.servertime))

        currentTimestamp_inreallife = str(datetime.now())

        if verbose: print(minecraftTime)

        playerPoints = {}

        for p in self.players:

            username = p["account"]
            health = p["health"]
            health_bar = self.makeHealthBar(health)
            armor = p["armor"]
            armor_bar = self.makeArmourBar(armor)
            world = p["world"]
        
            if world == "vanilla":
                region = "overworld"
            if world == "vanilla_nether":
                region = "nether"
            if world == "vanilla_the_end":
                region = "end"
            

            x,y,z = p["x"], p["y"], p["z"]

            info_print = f"[The {region.title()}] {username}: {x}, {y}, {z} | {health_bar} ({health}) | {armor_bar} {armor}"
            if verbose: print(info_print)

            playerPoints[username] = {
                "health": health,
                "health_bar": health_bar,
                "armor": armor,
                "armor_bar": armor_bar,
                "world": world,
                "region": region,
                "username": username,
                "pos": (x, y, z),
                "info_print": info_print,
                "player_head_url": self.useFulFunctions.getPlayerFace(username, size="32x32", returnPILImage=False)
            }

        self.chunk["data"][currentTimestamp_inreallife] = {
            "start_scan": currentTimestamp_inreallife,
            "end_scan": str(datetime.now()),
            "time_taken": time.time() - st,
            "minecraft_time": minecraftTime,
            "servertime": self.servertime,
            "players": playerPoints,
            "player_count": self.player_count,
            "timestamp_recieved": self.timestamp,
            # "updates": self.updates
        }

        self.chunk["end_time"] = str(datetime.now())
        self.chunk["time_taken"] = time.time() - start_time_seconds

        return self.chunk


class MonitorThread(Thread):
    def __init__(self, website_base_url, group = None, target = None, name = None, args = ..., kwargs = None, *, daemon = None) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.processing = False
        self.processedData = None
        self.base_url = website_base_url

    def run(self, saveChunks=False, chunkSavepath="data\\chunks"):
        self.running = True
        self.chunk_manager = ChunkManager(website_base_url=self.base_url)
        self.player_manager = PlayerManager(website_base_url=self.base_url)
        self.usefulFunctions = UsefulFunctions(base_url=self.base_url)
        self.valueUpdater = ValueUpdater(website_base_url=self.base_url)
        self.request_region = "Overworld"

        self.extraSecondDelayBetweenUpdates = 0.1

        self.player_head_images_cache = {}
        self.chunk_images_cache = {}
        self.processing = True

        self.running = True
        print("Now Monitoring!")
        while self.running:
            
            self.processing = True

            # Update values!
            while 1:
                try:
                    requestData = self.valueUpdater.updateValues(self.request_region)
                    break
                except ConnectionRefusedError as e:
                    print(f"Failed to get data (ConnectionRefusedError)! Trying again... | Error: {e}")
                except ConnectionError as e:
                    print(f"Failed to get data (ConnectionError)! Trying again... | Error: {e}")
                except ConnectionResetError as e:
                    print(f"Failed to get data (ConnectionResetError)! Trying again... | Error: {e}")
                except ConnectionAbortedError as e:
                    print(f"Failed to get data (ConnectionAbortedError)! Trying again... | Error: {e}")
                except Exception as e:
                    print(f"Failed to get data (Unknown / Unaccounted for)! Trying again... | Error: {e}")


            self.player_manager.updateValues(requestData)

            # Get a sorted chunk of player info
            player_chunk_info = self.player_manager.gatherChunk()
            
            # Get latest data part
            self.latest_timestamp = list(player_chunk_info["data"].keys())[-1]
            self.data = player_chunk_info["data"][self.latest_timestamp]
            
            # Get other info
            self.player_count = self.data["player_count"]
            self.players = self.data["players"]

            self.servertime = self.data["servertime"]
            self.minecraft_time = self.data["minecraft_time"]

            self.processedData = {
                "timestamp": self.latest_timestamp,
                "servertime": self.servertime,
                "minecraft_time": self.minecraft_time,
                "players": [],
                "player_count": self.player_count
            }

            for username in self.players:
                player_data = self.players[username]

                px, py, pz = player_data["pos"]
                px, py, pz = round(px), round(py), round(pz)
                cx, cz = self.usefulFunctions.Minecraft_XZ_to_Chunk_XZ(px, pz)
                world = player_data["world"]
                region = player_data["region"]
                health = player_data["health"]
                armor = player_data["armor"]

                if saveChunks:
                    chunk_key = f"{cx}_{cz}"
                    if not chunk_key in self.chunk_images_cache:
                        self.chunk_images_cache[chunk_key] = self.usefulFunctions.getPILImageFromURL(self.usefulFunctions.createChunkURL(cx, cz))

                    chunk_image: Image.Image = self.chunk_images_cache[chunk_key]
                    if not os.path.exists(chunkSavepath):
                        os.makedirs(chunkSavepath)
                    with open(f"{chunkSavepath}\\{chunk_key}.jpg", "w") as f:
                        chunk_image.save(f)

                # print(f"[{username}] {health} | {armor} - {px} {py} {pz} - {cx} {cz}")

                players:list = self.processedData["players"]
                players.append({
                    "username": username,
                    "pos": (px, py, pz),
                    "chunkpos": (cx, cz),
                    "world": world,
                    "region": region,
                    "health": health,
                    "armor": armor
                })
                self.processedData["players"] = players

            self.processing = False
            time.sleep(self.extraSecondDelayBetweenUpdates)

        print("No longer monitoring!")

    def stopPlease(self):
        self.running = False

    def returnCurrentPlayerDataCleaned(self, wait=True):
        if wait:
            while self.processing:
                pass
        return self.processedData

    def changeRequestRegion(self, region="overworld"):
        self.request_region = region

    def changeDelayPerGrab(self, seconds):
        self.extraSecondDelayBetweenUpdates = seconds



if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)

    a = MonitorThread(website_base_url=config["dynmap_website"])
    a.daemon = True
    a.start()

    try:
        while 1:
            pass
    except KeyboardInterrupt:
        a.stopPlease()

    a.join()