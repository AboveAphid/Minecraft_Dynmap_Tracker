import sqlite3, time, sys, keyboard, os, psutil, requests, colorama, json
from pathvalidate import sanitize_filename
from System import Clear, Terminal
from Minecraft import Server
from GoodFuncs import UsefulFunctions
from datetime import datetime
from queue import Queue, Empty
from threading import Thread
from PIL import Image

with open("config.json", "r") as f:
    config = json.load(f)

DATABASE_UPDATER_EXE_NAME = config["database_exe_name"]
MINECRAFT_SERVER_SERVER_ADDRESS = config["minecraft_server_address"]
MINECRAFT_WEBSITE_MAP_REQUEST_URL = config["dynmap_website"]
NUMBER_OF_THREADS = config["max_number_of_threads"]
ONLY_SHOW_CHUNKS_WITH_PLAYER_WHEN_MAKING_MAP = True

terminalClearer = Clear()
terminal = Terminal()
usefulFunctions = UsefulFunctions(base_url=MINECRAFT_WEBSITE_MAP_REQUEST_URL)

second_threshold_until_offline = 3

terminalClearer.clear_full_terminal()


BANNER = colorama.Fore.MAGENTA + r"""
 ___                            ___                _             
| . \ _ _ ._ _ ._ _ _  ___  ___|_ _|_ _  ___  ___ | |__ ___  _ _ 
| | || | || ' || ' ' |<_> || . \| || '_><_> |/ | '| / // ._>| '_>
|___/`_. ||_|_||_|_|_|<___||  _/|_||_|  <___|\_|_.|_\_\\___.|_|  
     <___'                 |_|                                   
""" + colorama.Style.RESET_ALL

### CONNECT TO SQL DATABASES
connectedToMainDatabase = True
connectedToUsersDatabase = True

def connect_databases():
    global connectedToMainDatabase, connectedToUsersDatabase, mConnection, mCursor, uConnection, uCursor
    try:
        mConnection = sqlite3.connect("Main.db")
        mCursor = mConnection.cursor()
    except: connectedToMainDatabase = False

    try:
        uConnection = sqlite3.connect("Users.db")
        uCursor = uConnection.cursor()
    except: connectedToUsersDatabase = False

    return connectedToMainDatabase, connectedToUsersDatabase

connect_databases()

def displayBannerCentred():
    offset = os.get_terminal_size().columns
    for line in BANNER.splitlines():
        print(line.center(offset))


menu_options = ["Track", "Check Database Status", "Refresh/Reconnect Databases", "Check Database Updater Status", "See All Processes", "Check Minecraft Server Status", "Check Website Map Status", "Player Map"]

### MENU
while 1:
    offset = os.get_terminal_size().columns

    displayBannerCentred()

    print(f"|{'-'*20}Menu{'-'*20}|".center(offset))
    print(" "*(offset//3) + f'\n{" "*(offset//3)}'.join(f"[{i}] {option}" for i, option in enumerate(menu_options)))
    print(f"|{'-'*44}|".center(offset))


    try:
        targetID = int(input("Target: \n   ".center(offset)))
        targetOption = menu_options[targetID]
        print("Option choosen:", targetOption)
        time.sleep(0.2)
        break
    except IndexError:
        terminalClearer.clear_full_terminal()
        print("Choosen ID is out of range!")
    except ValueError:
        terminalClearer.clear_full_terminal()
        print("When choosing an ID please use INTEGERS only!")
    except KeyboardInterrupt:
        print("Exiting...")
        exit()




def trackPlayersOption():
    ### GET DESIRED PLAYER TO TRACK
    choosen_successfully = False
    while not keyboard.is_pressed("ctrl+enter"):
        offset = terminal.get_terminal_width()
        allUsers = mCursor.execute("SELECT username FROM accounts;").fetchall()

        print("|-----------Player List-----------|".center(offset))
        # print('\t' + '\n\t'.join(f"[{i}] {username[0]}" for i, username in enumerate(allUsers)))
        print(" "*(offset//3) + f'\n{" "*(offset//3)}'.join(f"[{i}] {username[0]}" for i, username in enumerate(allUsers)))
        
        print("\n\n")
        print("""Press CTRL+ENTER to go back to menu""".center(offset))
        print("|---------------------------------|".center(offset))


        try:
            targetID = int(input("Target: \n   ".center(offset)))
            targetUsername = allUsers[targetID][0]
            print("Target choosen:", targetUsername)
            time.sleep(0.2)
            choosen_successfully = True
            break
        except IndexError:
            terminalClearer.clear_full_terminal()
            print("Choosen ID is out of range!")
        except ValueError:
            terminalClearer.clear_full_terminal()
            print("When choosing an ID please use INTEGERS only!")
        except KeyboardInterrupt:
            print("Exiting...")
            choosen_successfully = False
            break


    if not choosen_successfully: # Caused by Ctrl+Enter being pressed. So we want to get back to the menu instead
        return

    getAll = f"SELECT * FROM {targetUsername};"
    getLatest = f"SELECT * FROM {targetUsername} ORDER BY id DESC LIMIT 1;"

    terminalClearer.clear_full_terminal()

    iteration = 0

    previous_terminal_width = terminal.get_terminal_width()
    previous_terminal_height = terminal.get_terminal_height()

    while not keyboard.is_pressed("ctrl+enter"):


        ### GET INFO OF PLAYER FROM THE SQL DATABASE/s

        tempCursor = uConnection.execute(getLatest)

        doStuff = False
        for row in tempCursor.fetchall():
            idOfRow = row[0]
            timestamp = row[1]
            timestamp_datetime_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            x, y, z = row[2], row[3], row[4]
            cx, cz = row[5], row[6]
            health, armor = row[7], row[8]
            region, world = row[9], row[10]
            servertime = row[11]
            minecrafttime = row[12]
            doStuff = True


        if not doStuff:
            continue
        
        
        ### CALCULATE IF THE USER IS STILL (most likely) ONLINE IN THE SERVER
        current_time = datetime.now()

        online = timestamp_datetime_obj.date().ctime() == current_time.date().ctime() \
                    and timestamp_datetime_obj.day == current_time.day \
                    and timestamp_datetime_obj.hour == current_time.hour \
                    and timestamp_datetime_obj.minute == current_time.minute \
                    and timestamp_datetime_obj.second >= current_time.second - second_threshold_until_offline




        ### MAKE SURE THE TERMINAL DOESN'T GO TO WACK!

        current_terminal_width = terminal.get_terminal_width()
        current_terminal_height = terminal.get_terminal_height()
        if current_terminal_width != previous_terminal_width or current_terminal_height != previous_terminal_height:
            terminalClearer.clear_full_terminal()
            previous_terminal_width = current_terminal_width
            previous_terminal_height = current_terminal_height

        resize_terminal_required = False
        if current_terminal_width < 65 or current_terminal_height < 30:
            resize_terminal_required = True




        #### WRITE INFO TO TERMINAL

        terminalClearer.move_mouse_to_top() # We use this to remove all previous info by writing over it

        info = f"""@----------------------------@            
    > {targetUsername}            

### Other
    User Online             : {online}        
    Terminal Size           : {current_terminal_width}, {current_terminal_height}
    Please Resize Terminal  : {str(resize_terminal_required).upper()}

### Time
    Current time      : {current_time}            
    Time of retrieval : {timestamp_datetime_obj}     
    Server Time       : {servertime}             
    Minecraft Time    : {minecrafttime}             

### Position
    XYZ      : {x, y, z}            
    Chunk    : {cx, cz}            
    Region   : {region}            
    World ID : {world}            

### Stats
    Health   : {health}            
    Armor    : {armor}            


Press CTRL+ENTER to go back to menu
@----------------------------@                        
"""

        # write the info out using sys.stdout (this allows us to easily clear it and stuff)
        sys.stdout.write(info)
        sys.stdout.flush()


        # Other ending parts of the loop
        iteration += 1
        time.sleep(0.1)



def checkDatabaseStatusOption():
    terminalClearer.clear_full_terminal()

    while not keyboard.is_pressed("ctrl+enter"):
        terminalClearer.move_mouse_to_top()

        info = f"""@----------------------------@
    > Database Statuses

MAIN
    Online: {str(connectedToMainDatabase).upper()}

USERS
    Online: {str(connectedToUsersDatabase).upper()}

Press CTRL+ENTER to go back to menu
@----------------------------@  
"""
        
        sys.stdout.write(info)
        sys.stdout.flush()

def refreshDatabasesOption():  
    print("Connecting databases...")
    st = time.time()
    mSuccessful, uSuccessful = connect_databases()
    time_taken = time.time() - st
    print("Attempted both database connections!")
    print("Showing results...")
    time.sleep(0.1)
    terminalClearer.clear_full_terminal()
    print(f"""@----------------------------@
    > Database Refresh Results
          
MAIN
    Database now connected: {mSuccessful}

USERS
    Database now connected: {uSuccessful}

### Other
    Time taken (seconds): {time_taken}

Press CTRL+ENTER to go back to menu
@----------------------------@
""")
    
    while not keyboard.is_pressed("ctrl+enter"):
        pass

def checkDatabaseUpdaterStatus():
    databaseUpdatorFound = False
    checkingForExe = input("Are you running the databaseupdator as an exe? (y/N) ").lower()[:1] == "y"
    pid = "N/A"
    nameToLookFor = "N/A"
    
    # https://stackoverflow.com/questions/7787120/check-if-a-process-is-running-or-not-on-windows
    if checkingForExe:
        print("Checking for exe...")
        nameToLookFor = DATABASE_UPDATER_EXE_NAME
        databaseUpdatorFound = nameToLookFor in (p.name() for p in psutil.process_iter())
    else:
        pid = str(input("What is the PID of the program? "))
        databaseUpdatorFound = pid in (str(p.pid) for p in psutil.process_iter())
    
    terminalClearer.clear_full_terminal()

    print(f"""@----------------------------@
    > Check status of Database Updator

### SEARCH PARAMETRES
    Looking for EXE: {checkingForExe}
    Looking with PID: {not checkingForExe}
    NAME: {nameToLookFor}
    PID: {pid}

### RESULTS
    Database Updator online: {databaseUpdatorFound}


*Please know some of these results may be incorrect.
Press CTRL+ENTER to go back to menu
@----------------------------@""")
    while not keyboard.is_pressed("ctrl+enter"):
        pass

def checkMinecraftServerStatus():
    online = True
    error_occurred = False
    error = "No error occurred!"

    server_name = "N/A"
    server_ip_address = "N/A"
    server_port = "N/A"
    mods = "N/A"
    plugins = "N/A"
    player_count = -1
    max_player_count = -1
    players_names = []

    try:
        server = Server(MINECRAFT_SERVER_SERVER_ADDRESS)

        server_name = server.returnName()
        server_ip_address = server.returnIPAddress()
        server_port = server.returnPort()
        mods = server.returnMods()
        plugins = server.returnPlugins()
        player_count = server.returnPlayersOnline()
        max_player_count = server.returnPlayerMax()

        players_names = [player["name_clean"] for player in server.returnPlayers()]

    except Exception as e:
        online = False
        error_occurred = True
        error = e
        pass
    print(f"""@----------------------------@
    > Minecraft Server
          
### STATUS
    Online: {online}
    
### SERVER INFO
    Server Name: {server_name}
    Server Address: {MINECRAFT_SERVER_SERVER_ADDRESS}
    IP Address: {server_ip_address}
    Port: {server_port}
          
### PLAYERS
    Player Count: {player_count}/{max_player_count}    
    Players: {players_names}

### NON-VANILLA
    Mods: {mods}
    Plugins: {plugins}

### ERRORS
    Error Occurred: {error_occurred}
    Error: {error}


Press CTRL+ENTER to go back to menu
@----------------------------@""")

    while not keyboard.is_pressed("ctrl+enter"):
        pass

def checkWebsiteMapStatus():
    res = requests.get(MINECRAFT_WEBSITE_MAP_REQUEST_URL)
    online = res.status_code == 200

    print(f"""@----------------------------@
    > Website Status
          
### STATUS
    Online: {online}

### REQUEST INFO
    Url: {MINECRAFT_WEBSITE_MAP_REQUEST_URL}
    Status Code: {res.status_code}
    Response: {res.reason}
          
Press CTRL+ENTER to go back to menu
@----------------------------@""")
    
    while not keyboard.is_pressed("ctrl+enter"):
        pass

def seeAllProcessesOption():
    # https://www.tutorialspoint.com/how-to-check-if-an-application-is-open-in-python#:~:text=Using%20subprocess%20module,using%20the%20check_output()%20method.
    print("@----------------------------@")
    processes = psutil.process_iter()
    for process in processes:
        print(f"Process name: {process.name()} | PID: {process.pid}")
    cpu_percent = psutil.cpu_percent()
    print(f"CPU usage: {cpu_percent}%")
    memory_usage = psutil.virtual_memory()
    print(f"Total memory: {memory_usage.total / 1024 / 1024:.2f} MB")
    print(f"Available memory: {memory_usage.available / 1024 / 1024:.2f} MB")
    print(f"Memory usage: {memory_usage.percent}%")

    print("""

Press CTRL+ENTER to go back to menu
@----------------------------@
""")
    
    while not keyboard.is_pressed("ctrl+enter"):
        pass


maps_chunks_and_images = []
chunks_to_process_queue = Queue()

# (Basically modified code from ChunkManager > CManager)
def worker_chunk_downloader():
    """
    Used in playerMapOption()

    This worker is made to help download mass amounts of chunks
    """

    global maps_chunks_and_images
    while 1:
        try:
            chunk_x, chunk_z, request_url = chunks_to_process_queue.get(timeout=5)
        except Empty:
            break

        print(f"Processing chunk: {chunk_x}, {chunk_z} | {request_url}")
        image = usefulFunctions.getPILImageFromURL(request_url).convert('RGB')

        maps_chunks_and_images.append({
            "x": chunk_x,
            "z": chunk_z,
            "image": image
        })

        print(f"Chunk - {chunk_x}, {chunk_z} - has now been processed!")

        chunks_to_process_queue.task_done()

# (Also modified code from ChunkManager > CManager) - I'll be honest to ya guys I did have to use some ChatGPT when modifying this function. I've been at this one thing for hours alright, I've tried so many different ideas and things! Don't judge me >:( I was loosing hope 
def mergeMapImages(images_and_chunkxz:list[tuple], savename="Full-Map"):
    """
    images_and_chunkxz: [
        {"x":CHUNK_X_INT, "z":CHUNK_Z_INT, "image":PIL.Image.Image}
    ]
    """

    test_image:Image.Image = images_and_chunkxz[0]["image"]

    assumed_width_of_chunk_image = test_image.size[0]
    assumed_height_of_chunk_image = test_image.size[1]

    # Step 1: Find the minimum x and z values to normalize the coordinates
    min_x = min(item['x'] for item in images_and_chunkxz)
    min_z = min(item['z'] for item in images_and_chunkxz)

    # Step 2: Normalize the x and z values so that they start at (0, 0)
    normalized_list = [
        {'x': item['x'] - min_x, 'z': item['z'] - min_z, 'image': item['image']}
        for item in images_and_chunkxz
    ]

    # Step 3: Sort the list by the new normalized x and z values
    sorted_normalized_list = sorted(normalized_list, key=lambda item: (item['x'], item['z']))

    # Output the final sorted and normalized list
    for item in sorted_normalized_list:
        print(f"x: {item['x']}, z: {item['z']}, image: {item['image']}")

    number_of_chunks_width = sorted_normalized_list[-1]["x"] + 1
    number_of_chunks_height = sorted_normalized_list[-1]["z"] + 1

    total_width = assumed_width_of_chunk_image * number_of_chunks_width
    total_height = assumed_height_of_chunk_image * number_of_chunks_height

    new_image = Image.new('RGB', (total_width, total_height))

    print(f"""
          
All Images:
    > {'\n> '.join((str(p) for p in images_and_chunkxz))}
    Total: {len(images_and_chunkxz)}

Number of Chunks:
    W: {number_of_chunks_width}
    h: {number_of_chunks_height}

Total Size:
    W: {total_width}
    H: {total_height}

""")

    for item in sorted_normalized_list:
        x = item["x"]
        z = item["z"]
        im = item["image"]  # Open the image from the item
        
        x_offset = x * assumed_width_of_chunk_image
        z_offset = (total_height - z * assumed_height_of_chunk_image) - assumed_height_of_chunk_image  # Calculate correct Y offset

        new_image.paste(im, (x_offset, z_offset))  # Paste the image at the correct offset

    new_image = new_image.convert("RGB")

    i = 1
    savename2 = sanitize_filename(f"{savename}.jpg")
    while 1:
        savename2 = f"{savename}-{i}.jpg"
        if not os.path.exists(savename2):
            break
        i += 1

    out_path = os.path.join(os.getcwd(), savename2)

    # Save the final merged image
    with open(out_path, "w") as f:
        new_image.save(f)

    return new_image, out_path

def playerMapOption():
    global maps_chunks_and_images, chunks_to_process_queue

    ### GET DESIRED PLAYER TO MAP
    choosen_successfully = False
    while not keyboard.is_pressed("ctrl+enter"):
        offset = terminal.get_terminal_width()
        allUsers = mCursor.execute("SELECT username FROM accounts;").fetchall()

        print("|-----------Player List-----------|".center(offset))
        # print('\t' + '\n\t'.join(f"[{i}] {username[0]}" for i, username in enumerate(allUsers)))
        print(" "*(offset//3) + f'\n{" "*(offset//3)}'.join(f"[{i}] {username[0]}" for i, username in enumerate(allUsers)))
        
        print("\n\n")
        print("""Press CTRL+ENTER to go back to menu""".center(offset))
        print("|---------------------------------|".center(offset))


        try:
            targetID = int(input("Target: \n   ".center(offset)))
            targetUsername = allUsers[targetID][0]
            print("Target choosen:", targetUsername)
            time.sleep(0.2)
            choosen_successfully = True
            break
        except IndexError:
            terminalClearer.clear_full_terminal()
            print("Choosen ID is out of range!")
        except ValueError:
            terminalClearer.clear_full_terminal()
            print("When choosing an ID please use INTEGERS only!")
        except KeyboardInterrupt:
            print("Exiting...")
            choosen_successfully = False
            break

    if not choosen_successfully:
        return
    

    terminalClearer.clear_full_terminal()

    regions = ["overworld", "nether", "end"]
    choosen_successfully = True
    while 1:
        offset = terminal.get_terminal_width()

        print("|---------------------------------|".center(offset))
        print(" "*(offset//3) + f'\n{" "*(offset//3)}'.join(f"[{i}] {region.title()}" for i, region in enumerate(regions)))
        print("|---------------------------------|".center(offset))

        try:
            targetID = int(input("Target: \n   ".center(offset)))
            targetRegion = regions[targetID]
            print("Target choosen:", targetRegion)
            time.sleep(0.2)
            choosen_successfully = True
            break
        except IndexError:
            terminalClearer.clear_full_terminal()
            print("Choosen ID is out of range!")
        except ValueError:
            terminalClearer.clear_full_terminal()
            print("When choosing an ID please use INTEGERS only!")
        except KeyboardInterrupt:
            print("Exiting...")
            choosen_successfully = False
            break



    if not choosen_successfully:
        return

    region_to_world = {
        "overworld": "vanilla",
        "nether": "vanilla_nether",
        "end": "vanilla_the_end"
    }

    targetWorld = region_to_world[targetRegion]

    print(f'Target world: {targetWorld}')

    terminalClearer.clear_full_terminal()

    

    getAllChunks = f"SELECT map_chunk_x, map_chunk_z, timestamp FROM {targetUsername} WHERE world='{targetWorld}';"
    
    tempCursor = uConnection.execute(getAllChunks)
    rows = tempCursor.fetchall()

    if len(rows) == 0:
        offset = terminal.get_terminal_width()
        print("@----------------------------@".center(offset))
        print(f"The player has not been spotted in: {targetRegion} | {targetWorld}...".center(offset))
        print("Maybe we haven't been tracking them when they were there?".center(offset))
        print("\n")
        print("Press CTRL+ENTER to go back to menu".center(offset))
        print("@----------------------------@".center(offset))
        while not keyboard.is_pressed("ctrl+enter"):
            pass

        return


    chunks_seen_in_no_dupes = []
    for row in rows:
        x, z, _ = row
        if not (x, z) in chunks_seen_in_no_dupes:
            chunks_seen_in_no_dupes.append((x, z))

    for c in chunks_seen_in_no_dupes:
        print(c)

    map_chunks = usefulFunctions.findMissingChunks(chunks_seen_in_no_dupes)

    # Reset values
    maps_chunks_and_images = []
    chunks_to_process_queue = Queue()

    # TODO: add player head on chunks the player has been spotted in

    for c in map_chunks:
        x, z, type_of_chunk = c
        person_was_here = type_of_chunk == "HAD"
        # Only get images for the chunks that the player has been seen in (unless "ONLY_SHOW_CHUNKS_WITH_PLAYER_WHEN_MAKING_MAP" is False). 
        # This makes the process faster and more efficient. Also black chunks will appear in the missing spots (which was what I intended)
        if person_was_here or ONLY_SHOW_CHUNKS_WITH_PLAYER_WHEN_MAKING_MAP == False:
            print(person_was_here)
            request_url = usefulFunctions.createChunkURL(x, z, targetWorld)
            chunks_to_process_queue.put((x, z, request_url))


    threads = []
    for _ in range(NUMBER_OF_THREADS):
        wt = Thread(target=worker_chunk_downloader)
        wt.daemon = True
        threads.append(wt)
        wt.start()

    st = time.time()

    try:
        chunks_to_process_queue.join()
    except KeyboardInterrupt:
        print("Processing interrupted by keyboard!")
        print("\n")
        print("Press CTRL+ENTER to go back to menu".center(offset))

        
        while not keyboard.is_pressed("ctrl+enter"):
            try: pass
            except KeyboardInterrupt: pass
        
        return
    
    if len(maps_chunks_and_images) == 0:
        terminalClearer.clear_full_terminal()

        offset = terminal.get_terminal_width()
        print("No chunks have been found for this user...".center(offset))
        print(f"Seen in chunks (no dupes): {chunks_seen_in_no_dupes}".center(offset))
        print(f"Map chunks: {map_chunks}".center(offset))
        print(f"Map chunks and images: {maps_chunks_and_images}".center(offset))

        print("Press CTRL+ENTER to go back to menu".center(offset))
        while not keyboard.is_pressed("ctrl+enter"):
            pass
        return

    time_taken = time.time() - st

    terminalClearer.clear_full_terminal()

    offset = terminal.get_terminal_width()

    print("@----------------------------@".center(offset))
    print(f"All chunks in map complete! \nProcess time: {time_taken}")

    print("Merging to create full map image...")
    st = time.time()
    full_map, outpath = mergeMapImages(maps_chunks_and_images, savename=f"{targetUsername}-{targetRegion}-FullMap")
    time_taken = time.time() - st
    print(f"Merging completed! \nProcess time: {time_taken}")
    print("Map saved to:", outpath)
    print("Press CTRL+ENTER to go back to menu".center(offset))
    print("@----------------------------@".center(offset))

    full_map.show("Full Map")
    while not keyboard.is_pressed("ctrl+enter"):
        pass





### RUN SELECTED MENU OPTION
terminalClearer.clear_full_terminal()
match (targetOption):
    case "Track":
        trackPlayersOption()
    case "Check Database Status":
        checkDatabaseStatusOption()

    case "Refresh/Reconnect Databases":
        refreshDatabasesOption()

    case "Check Database Updater Status":
        checkDatabaseUpdaterStatus()

    case "Check Minecraft Server Status":
        checkMinecraftServerStatus()

    case "Check Website Map Status":
        checkWebsiteMapStatus()

    case "See All Processes":
        seeAllProcessesOption()

    case "Player Map":
        playerMapOption()

    case _:
        print("""@----------------------------@
This option does not exist!
Maybe it isn't implemented yet?        

              
Press CTRL+ENTER to go back to menu
@----------------------------@
""")
        
        while not keyboard.is_pressed("ctrl+enter"):
            pass





### GO BACK TO MENU BY RE-RUNNING SCRIPT (unless KeyboardInterrupt occurs, then it full exits)
try:
    # Re-run the script (to get to menu)
    terminalClearer.clear_full_terminal()
    os.system("python " + ' '.join(sys.argv))

except KeyboardInterrupt:
    pass