import sqlite3, time, keyboard, os
from datetime import datetime
from Minecraft import User, Server
from Monitor import MonitorThread
import json

with open("config.json", "r") as f:
    config = json.load(f)
    EXIT_KEYBIND = config["exit_keybind"]
    WEBSITE_BASE_URL = config["dynmap_website"]

# Write out process PID so it can be lookup with viewer script
with open("DatabaseUpdatorPID.txt", "w") as f:
    f.write(f"My PID is: {os.getpid()}\n")
    f.write(f"Time put here: {datetime.now()}")

# Connect to databases
mConnection = sqlite3.connect("Main.db")
mCursor = mConnection.cursor()

uConnection = sqlite3.connect("Users.db")
uCursor = uConnection.cursor()

# Create accounts table - This will store user's info like UUID, etc
mCursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    username TEXT PRIMARY KEY,
    uuid TEXT,
    account_creation_date TEXT,
    head_icon_url TEXT,
    skin_url TEXT,
    valid_user TEXT
);""")

def addNewUser(username, uuid, account_creation_date, head_icon_url, skin_url, valid_user=True):
    """
    Adds a new user to accounts table in Main.db
    """
    print("Adding new user:", username, "|", uuid)
    try:
        try:
            mCursor.execute(f"""
            INSERT INTO accounts (
                username, uuid, account_creation_date, head_icon_url, skin_url, valid_user
            )
            VALUES (
                '{username}', '{uuid}', '{account_creation_date}', '{head_icon_url}', '{skin_url}', '{str(valid_user).upper()}'
            );
            """)
            mConnection.commit()
        except Exception as e:
            print(f"Error while adding user (MAIN DB) (Method 1): {username} | Error: {e} | Will try to use Method 2..")
            mConnection.rollback()
            mCursor.execute(f"""
            UPDATE accounts
                SET uuid='{uuid}', account_creation_date='{account_creation_date}', head_icon_url='{head_icon_url}', skin_url='{skin_url}', valid_user='{str(valid_user).upper()}'
                    WHERE username='{username}';
            """)
            mConnection.commit()
            print(f"Method 2 for committing '{username}' was successful!!")
    except Exception as e:
        print(f"Error while adding user (MAIN DB) (Method 2): {username} | Error: {e}")
        mConnection.rollback()
    
    try:
        uCursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {username} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            x INTEGER,
            y INTEGER,
            z INTEGER,
            map_chunk_x INTEGER,
            map_chunk_z INTEGER,
            health INTEGER,
            armor INTEGER,
            region TEXT,
            world TEXT,
            servertime INTEGER,
            minecraft_time TEXT
        );""")
        uConnection.commit()
    except Exception as e:
        print(f"Error while adding user (USERS DB): {username} | Error: {e}")
        uConnection.rollback()
    

def addNewPart(username, timestamp, pos, chunk_pos, health, armor, region, world, servertime, minecraft_time):
    """
    Adds new data to Users.db for a specific user
    """
    x, y, z = round(pos[0]), round(pos[1]), round(pos[2])
    cx, cz = round(chunk_pos[0]), round(chunk_pos[1])
    try:
        uCursor.execute(f"""
        INSERT INTO {username} (
            timestamp, x, y, z, map_chunk_x, map_chunk_z, health, armor, region, world, servertime, minecraft_time
        )
        VALUES (
            '{timestamp}', {x}, {y}, {z}, {cx}, {cz}, {health}, {armor}, '{region}', '{world}', {servertime}, '{minecraft_time}'
        );
        """)
        uConnection.commit()
    except Exception as e:
        print(f"Error while updating user: {username} (USERS DB) | Error: {e}")
        uConnection.rollback()




monitorThread = MonitorThread(website_base_url=WEBSITE_BASE_URL)
monitorThread.daemon = True
monitorThread.start()

addedPlayers = {}

time.sleep(1)

print(f"Press {EXIT_KEYBIND} to exit...")
while not keyboard.is_pressed(EXIT_KEYBIND):
    
    data = monitorThread.returnCurrentPlayerDataCleaned()
    if not data:
        print("Data recieved was null!")
        continue


    timestamp = data["timestamp"]
    servertime = data["servertime"]
    minecraft_time = data["minecraft_time"]
    players = data["players"]
    player_count = data["player_count"]
    
    # players.append({
    #     "username": "_buildcraft1845",
    #     "pos": (1, 2, 3),
    #     "chunkpos": (0, 1),
    #     "world": "vanilla",
    #     "region": "overworld",
    #     "health": 10,
    #     "armor": 15,
    # })

    for p in players:
        username = p["username"]
        px, py, pz = p["pos"]
        cx, cz = p["chunkpos"]
        world = p["world"]
        region = p["region"]
        health = p["health"]
        armor = p["armor"]

        if not username in addedPlayers:
            try:
                user = User(username)
                uuid = user.returnUUID()
                head = user.returnHead(returnurl=True)
                skin = user.returnSkin(returnurl=True)
                valid_user = True
            except NameError:
                print(f"User isn't valid but is on server? Username: {username}")
                user = User(username, createErrors=False)
                valid_user = False
                uuid = "N/A"
                head = "N/A"
                skin = "N/A"

            addedPlayers[username] = user
            addNewUser(username, uuid, "Not Implemented", head, skin, valid_user=valid_user)
        else:
            user: User = addedPlayers[username]
            uuid = user.returnUUID()

        addNewPart(
            username,
            timestamp,
            (px, py, pz),
            (cx, cz),
            health,
            armor,
            region,
            world,
            servertime,
            minecraft_time
        )

        print(f"{username} has been updated!")

print("Exiting...")

# Close SQL Databases
mCursor.close()
uCursor.close()
mConnection.close()
uConnection.close()