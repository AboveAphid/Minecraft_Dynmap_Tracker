import math, requests
from PIL import Image
import urllib.parse
        

class UsefulFunctions():
    def __init__(self, base_url) -> None:
        self.base_url = base_url

    def Minecraft_XZ_to_Chunk_XZ(self, x, z, chunk_size=-32) -> tuple[int, int]:
        """
        chunk_size is negative 32 because if you go to the map you will notice that every increase in ChunkZ the PosZ changes by -32. And same for X
        """
        chunk_x = -math.floor(x / chunk_size) - 1
        chunk_z = math.floor(z / chunk_size)

        return chunk_x, chunk_z
    
    def url_join(self, base_url, path):
        return urllib.parse.urljoin(base_url, path)

    def findMissingChunks(self, knownChunks):
        """
        Warning this function is somewhat buggy / doesn't work very well in negatives.
        """

        upper_left = knownChunks[0] # Temp
        for c in knownChunks:
            current_x = upper_left[0]
            current_z = upper_left[1]

            if c[0] + c[1] > current_x + current_z:
                upper_left = c

        lowest_right = knownChunks[0] # Temp
        for c in knownChunks:
            current_x = lowest_right[0]
            current_z = lowest_right[1]

            if c[0] + c[1] < current_x + current_z:
                lowest_right = c

        all_chunks = []

        # TODO: This doesn't work properly when upper_left is a negative (specifically in upper_left[1]
        for x in range(lowest_right[0], upper_left[0]):
            for z in range(lowest_right[1], upper_left[1]):
                if (x, z) in knownChunks:
                    all_chunks.append((x, z, "HAD"))
                else:
                    all_chunks.append((x, z, "NEW"))

        print("Map chunks:", all_chunks)
        print("Lowest right:", lowest_right)
        print("Upper left:", upper_left)
        return all_chunks

    def getPILImageFromURL(self, url) -> Image.Image:
        return Image.open(requests.get(url, stream=True).raw)
    
    def createChunkURL(self, chunk_x, chunk_z, world="vanilla", timestamp=None, type_taken="flat") -> str:
        end = ""
        if timestamp:
            end = f"?timestamp={timestamp}"
        return self.url_join(self.base_url, f"/tiles/{world}/{type_taken}/0_0/{chunk_x}_{chunk_z}.jpg{end}")

    def createPosURL(self, x, z, world="vanilla"):
        return self.url_join(self.base_url, f"/?worldname={world}&mapname=flat&zoom=10&x={x}&y=64&z={z}#")
    
    def getPlayerFace(self, username, size="32x32", returnPILImage=True) -> Image.Image | str:
        # size = "32x32" # "16x16"
        request_url = self.url_join(self.base_url, f"/tiles/faces/{size}/{username}.png")
        if returnPILImage:
            return self.getPILImageFromURL(request_url)
        else:
            return request_url
        
    def getMinecraftTime(self, servertime:int) -> dict:
        """
        Returns minecraft time based on "servertime"
        """
        day = servertime >= 0 and servertime < 13700
        
        return {
            "servertime": servertime,
            "days": int((servertime+8000) / 24000),
            # Assuming it is day at 6:00
            "hours": (int(servertime / 1000)+6) % 24,
            "minutes": int(((servertime / 1000) % 1) * 60),
            "seconds": int(((((servertime / 1000) % 1) * 60) % 1) * 60),
            "day": day,
            "night": not day
        }

    def minecraftTimeToString(self, current_time:dict, servertime:int=None) -> str:
        """
        Make minecrafttime to a formatted string like:
        17:01:07:am
        """
        if not current_time and servertime != None:
            current_time = self.getMinecraftTime(servertime)

        day = current_time["day"]
        hours = str(current_time["hours"])
        minutes = str(current_time["minutes"])
        seconds = str(current_time["seconds"])

        amOrPm = ("am" if day == True else "pm")

        # Clean it so "17:1:7:am" becomes: "17:01:07:am"
        hours = '0'*(2-len(hours))     + hours
        minutes = '0'*(2-len(minutes)) + minutes
        seconds = '0'*(2-len(seconds)) + seconds
            
        return f"{hours}:{minutes}:{seconds}{amOrPm}"