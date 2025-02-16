from matplotlib.animation import FuncAnimation,PillowWriter
import streamlit as st
import imageio
import tempfile,os
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from functools import partial
from scipy.interpolate import interp1d
import random
#from IPython.display import HTML
from matplotlib.animation import FFMpegWriter
from datetime import datetime
import http.client, json
from urllib.parse import urlparse
import os
#os.environ["PATH"] += os.pathsep + r'C:\ffmpeg-master-latest-win64-gpl\bin'

def converter(gif_path):
    #os.popen("pip install imageio[ffmpeg]")
    #imageio.plugins.ffmpeg.download()
    try:
        with open(gif_path, 'rb') as f:
            st.write("Found GIF file:", gif_path)
    except FileNotFoundError:
        st.error("GIF file not found!")
        return

    try:
        # Create a temporary file to save the converted video
        with tempfile.NamedTemporaryFile(suffix=".mp4",prefix=gif_path[:-4]) as temp_file:
            gif_reader = imageio.get_reader(gif_path, format='GIF')
            fps = gif_reader.get_meta_data().get('fps', 1)  # Default to 1 FPS if metadata is missing

            #st.write(f"Temporary file created: {temp_file.name}")

            # Create a video writer for MP4 format
            with imageio.get_writer(temp_file.name, format='mp4', fps=fps) as video_writer:
                for frame in gif_reader:
                    video_writer.append_data(frame)

            st.success("Conversion successful!")
            st.video(temp_file.name)

            # Provide a download link for the converted MP4 file
            with open(temp_file.name, "rb") as f:
                st.download_button(label="Download MP4", data=f.read(), file_name=f"{gif_path[:-4]}.mp4", mime="video/mp4")
    except Exception as e:
        st.error(f"An error occurred during conversion: {e}")

def get_time():
# Get the current time in GMT
  current_time = datetime.utcnow()

# Format the time in the desired format
  formatted_time = current_time.strftime('%a, %d %b %Y %H:%M:%S GMT')

  print(formatted_time)
  return formatted_time


def interpolate_positions(player_data, total_minutes):
    positions = player_data['positions']
    num_positions = len(positions)
    minutes_played = player_data['minutesPlayed']
    start_frame = 0 if player_data['started'] else total_minutes - minutes_played
    end_frame = start_frame + minutes_played

    # Distribute positions evenly over the minutes played
    time_indices = np.linspace(start_frame, end_frame, num=num_positions)

    # Create DataFrame for interpolation
    df = pd.DataFrame(positions, columns=['x', 'y'])
    df['minute'] = time_indices
    df.set_index('minute', inplace=True)

    # Reindex to cover the entire duration and interpolate positions
    df = df.reindex(np.arange(total_minutes + 1)).interpolate(method='linear').ffill().bfill()

    return df[['x', 'y']].values

def get_all_positions(mid, pid):
    # (same as before)
    try:
        response = requests.get(f"https://www.sofascore.com/api/v1/event/{mid}/player/{pid}/heatmap")
        response.raise_for_status()
        heatmap_data = response.json().get("heatmap", [])
        print(f"https://www.sofascore.com/api/v1/event/{mid}/player/{pid}/heatmap")
        positions = [(point['x'], point['y']) for point in heatmap_data]
        return positions
    except requests.exceptions.RequestException as e:
        print(f"Error fetching heatmap data for player {pid}: {e}")
        return []
def init(ax,players_scatter):
    #global ax
    #ax.set_xlim(0, 100)
    #ax.set_ylim(0, 100)
    try:
        img = plt.imread("football-field-png-clipart_1494762.png")
    except FileNotFoundError:
        print("Error: ‘football-field-png-clipart_1494762.png’ not found. Using a blank background.")
        img = None
    #ax = plt.gca()
    if img is not None:
        ax.imshow(img, extent=[-2.5, 105, -5, 105])
        ax.set_xlim(-2.5, 105)
        ax.set_ylim(-5, 105)
    else:
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        #ax.set_aspect('equal')
        ax.set_facecolor('green')
    ax.set_aspect('equal')
    return players_scatter,ax

def update(frame,ax,player_movements,players_scatter,total_minutes,interpolated_positions):
  ax.clear()
  ax.set_xlim(0, 100)
  ax.set_ylim(0, 100)
  for i, (player, scatter) in enumerate(zip(player_movements.keys(), players_scatter)):
    data = player_movements[player]
    positions = interpolated_positions[player] # Calculate the start and end frame for each player
    start_frame = 0 if data['started'] else total_minutes - data['minutesPlayed']
    end_frame = start_frame + data['minutesPlayed']
    if start_frame <= frame < end_frame:
      ax.scatter(positions[frame, 0], positions[frame, 1], label=player)
      ax.text(positions[frame, 0], positions[frame, 1], data['jerseyNumber'], fontsize=9, ha='center')
    else: # Position player off the pitch
      ax.scatter(-10, -10, label=player)
      ax.text(-10, -10, data['jerseyNumber'], fontsize=9, ha='center')
      ax.set_title(f'Minute: {frame}')
      ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
  return players_scatter
def away(mid,jdata,subs):
    st.markdown("# AWAY TEAM")
    st.markdown("---")
    adata = {}
    for i in jdata['away']['players']:
        if i["statistics"] != {}:
            adata.update({i['player']['name']: [i['player']["jerseyNumber"], i["statistics"]["minutesPlayed"],
                                                i['player']['id']]})
        # if (i["substitute"]==False or i["substitute"]=="false") and i["statistics"]!={}:
        # adata.update({i['player']['name']:[i['player']["jerseyNumber"],90,i['player']['id']]})
        else:
            print("NOT", i['player']['name'], i["statistics"])
    print(adata)
    all_players = []
    substitutions = []
    with st.spinner("Processing data.."):
        for player_name, data in adata.items():
            player_id = player_name  # using the player name as id for now
            all_players.append(
                {"id": player_id, "name": player_name, "jerseyNumber": data[0], "minutesPlayed": data[1], "id": data[2]})

        for player_out, player_in in subs.items():
            try:
                minute_out = adata[player_out][1]
            except KeyError:
                continue
            substitutions.append({"playerIn": player_in, "playerOut": player_out, "minute": minute_out})

        player_movements = {}
        for player in all_players:
            print(player["name"])
            positions = get_all_positions(mid, player['id'])  # use name as id
            if positions:
                # player_movements[player['name']] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"], "positions": positions, "minutesPlayed": player["minutesPlayed"]}
                if player["name"] in list(subs.values()):
                    player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                        "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                        "started": False}
                else:
                    player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                        "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                        "started": True}
            else:
                print(f"No heatmap data for {player['name']}")
    print(substitutions)
    print(all_players)
    for a in player_movements:
        print(a, player_movements[a])
    adata = {}
    for i in jdata['away']['players']:
        if i["statistics"] != {}:
            adata.update({i['player']['name']: [i['player']["jerseyNumber"], i["statistics"]["minutesPlayed"],
                                                i['player']['id']]})
        # if (i["substitute"]==False or i["substitute"]=="false") and i["statistics"]!={}:
        # adata.update({i['player']['name']:[i['player']["jerseyNumber"],90,i['player']['id']]})
        else:
            print("NOT", i['player']['name'], i["statistics"])
    print(adata)
    all_players = []
    substitutions = []
    for player_name, data in adata.items():
        player_id = player_name  # using the player name as id for now
        all_players.append(
            {"id": player_id, "name": player_name, "jerseyNumber": data[0], "minutesPlayed": data[1], "id": data[2]})

    for player_out, player_in in subs.items():
        try:
            minute_out = adata[player_out][1]
        except KeyError:
            continue
        substitutions.append({"playerIn": player_in, "playerOut": player_out, "minute": minute_out})

    player_movements = {}
    for player in all_players:
        print(player["name"])
        positions = get_all_positions(mid, player['id'])  # use name as id
        if positions:
            # player_movements[player['name']] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"], "positions": positions, "minutesPlayed": player["minutesPlayed"]}
            if player["name"] in list(subs.values()):
                player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                    "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                    "started": False}
            else:
                player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                    "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                    "started": True}
        else:
            print(f"No heatmap data for {player['name']}")
    print(substitutions)
    print(all_players)
    with st.spinner("Interpolating data.."):
        for a in player_movements:
            print(a, player_movements[a])
        total_minutes = 90
        interpolated_positions = {
            player: interpolate_positions(data, total_minutes) for player, data in player_movements.items()
        }
    # Visualize interpolated positions for debugging
    for player, positions in interpolated_positions.items():
        print(f"Interpolated positions for {player}:")
        for minute, pos in enumerate(positions):
            print(f"Minute {minute}: {pos}")
        print("\n")
    with st.spinner("Generating video..Please wait"):
        # Visualization code (unchanged)
        fig, ax = plt.subplots(figsize=(10, 8))
        players_scatter = [ax.scatter([], [], label=player) for player in player_movements]
        ani = FuncAnimation(fig, partial(update,ax=ax,player_movements=player_movements,players_scatter=players_scatter,total_minutes=total_minutes,interpolated_positions=interpolated_positions), frames=total_minutes + 1, init_func=partial(init,ax=ax,players_scatter=players_scatter), blit=False, repeat=False)

        gif_writer = PillowWriter(fps=1)
        ani.save(f'away_player_movements.gif', writer=gif_writer)
        converter(f'away_player_movements.gif')
    st.success("Process complete!")
#def init_wrapper(ax,players_scatter):
    #return init(ax,players_scatter)[0]
colors = ['blue', 'red', 'cyan', 'magenta', 'yellow',  'maroon', 'olive', 'aqua', 'teal', 'navy', 'fuchsia', 'purple', 'orange', 'gold', 'pink', 'brown', 'coral', 'indigo', 'khaki', 'plum', 'salmon', 'violet', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'firebrick', 'forestgreen', 'goldenrod', 'hotpink', 'indianred', 'midnightblue', 'orangered', 'orchid', 'palevioletred', 'peru', 'rosybrown', 'royalblue', 'saddlebrown', 'sandybrown', 'seagreen', 'sienna', 'skyblue', 'slateblue', 'slategray', 'steelblue', 'tan', 'thistle', 'tomato', 'turquoise', 'wheat', 'yellowgreen']
def home(mid,jdata,subs):
    st.markdown("# HOME TEAM")
    st.markdown("---")
    hdata = {}
    for i in jdata['home']['players']:
        if i["statistics"] != {}:
            hdata.update({i['player']['name']: [i['player']["jerseyNumber"], i["statistics"]["minutesPlayed"],
                                                i['player']['id']]})
        # if (i["substitute"]==False or i["substitute"]=="false") and i["statistics"]!={}:
        # hdata.update({i['player']['name']:[i['player']["jerseyNumber"],90,i['player']['id']]})
        else:
            print("NOT", i['player']['name'], i["statistics"])
    print(hdata)
    all_players = []
    substitutions = []
    with st.spinner("Processing data.."):
        for player_name, data in hdata.items():
            player_id = player_name  # using the player name as id for now
            all_players.append(
                {"id": player_id, "name": player_name, "jerseyNumber": data[0], "minutesPlayed": data[1], "id": data[2]})

        for player_out, player_in in subs.items():
            try:
                minute_out = hdata[player_out][1]
            except KeyError:
                continue
            substitutions.append({"playerIn": player_in, "playerOut": player_out, "minute": minute_out})

        player_movements = {}
        for player in all_players:
            print(player["name"])
            positions = get_all_positions(mid, player['id'])  # use name as id
            if positions:
                # player_movements[player['name']] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"], "positions": positions, "minutesPlayed": player["minutesPlayed"]}
                if player["name"] in list(subs.values()):
                    player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                        "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                        "started": False}
                else:
                    player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                        "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                        "started": True}
            else:
                print(f"No heatmap data for {player['name']}")
    print(substitutions)
    print(all_players)
    for a in player_movements:
        print(a, player_movements[a])
    hdata = {}
    for i in jdata['home']['players']:
        if i["statistics"] != {}:
            hdata.update({i['player']['name']: [i['player']["jerseyNumber"], i["statistics"]["minutesPlayed"],
                                                i['player']['id']]})
        # if (i["substitute"]==False or i["substitute"]=="false") and i["statistics"]!={}:
        # hdata.update({i['player']['name']:[i['player']["jerseyNumber"],90,i['player']['id']]})
        else:
            print("NOT", i['player']['name'], i["statistics"])
    print(hdata)
    all_players = []
    substitutions = []
    for player_name, data in hdata.items():
        player_id = player_name  # using the player name as id for now
        all_players.append(
            {"id": player_id, "name": player_name, "jerseyNumber": data[0], "minutesPlayed": data[1], "id": data[2]})

    for player_out, player_in in subs.items():
        try:
            minute_out = hdata[player_out][1]
        except KeyError:
            continue
        substitutions.append({"playerIn": player_in, "playerOut": player_out, "minute": minute_out})

    player_movements = {}
    for player in all_players:
        print(player["name"])
        positions = get_all_positions(mid, player['id'])  # use name as id
        if positions:
            # player_movements[player['name']] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"], "positions": positions, "minutesPlayed": player["minutesPlayed"]}
            if player["name"] in list(subs.values()):
                player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                    "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                    "started": False}
            else:
                player_movements[player["name"]] = {"name": player["name"], "jerseyNumber": player["jerseyNumber"],
                                                    "positions": positions, "minutesPlayed": player["minutesPlayed"],
                                                    "started": True}
        else:
            print(f"No heatmap data for {player['name']}")
    print(substitutions)
    print(all_players)
    with st.spinner("Interpolating data.."):
        for a in player_movements:
            print(a, player_movements[a])
        total_minutes = 90
        interpolated_positions = {
            player: interpolate_positions(data, total_minutes) for player, data in player_movements.items()
        }
    # Visualize interpolated positions for debugging
    for player, positions in interpolated_positions.items():
        print(f"Interpolated positions for {player}:")
        for minute, pos in enumerate(positions):
            print(f"Minute {minute}: {pos}")
        print("\n")
    with st.spinner("Generating video..Please wait"):
        # Visualization code (unchanged)
        fig, ax = plt.subplots(figsize=(10, 8))
        players_scatter = [ax.scatter([], [], label=player) for player in player_movements]
        ani = FuncAnimation(fig, partial(update,ax=ax,player_movements=player_movements,players_scatter=players_scatter,total_minutes=total_minutes,interpolated_positions=interpolated_positions), frames=total_minutes + 1, init_func=partial(init,ax=ax,players_scatter=players_scatter), blit=False, repeat=False)

        writer = FFMpegWriter(fps=1, metadata=dict(artist='Me'), bitrate=1800)
        gif_writer = PillowWriter(fps=1)
        ani.save(f'home_player_movements.gif', writer=gif_writer)
        converter(f'home_player_movements.gif')
    st.success("Process complete!")

def match_ani(mid):
    st.warning("Players brought in late into the game may cause the site to fail!")
    #st.spinner("Getting average positions..")
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
        'baggage': 'sentry-environment=production,sentry-release=M4mJvBWRH0DaOAIR5pkTr,sentry-public_key=d693747a6bb242d9bb9cf7069fb57988,sentry-trace_id=1690b0fd312745c4a7b27a49f223bc9a',
        'cache-control': 'max-age=0',
        # 'cookie': '_gcl_au=1.1.325712268.1724831667; _fbp=fb.1.1724831667785.714237911590336157; _ga_LL3JHFY8FL=GS1.1.1724831667.1.1.1724833389.0.0.0; _ga=GA1.1.1716344257.1724831667; gcid_first=1a109337-6281-400d-a675-5843d4b21533; __browsiUID=c1346264-5d55-481e-ba9a-c6263535e313; __qca=P0-791554336-1727612017645; _au_1d=AU1D-0100-001730035850-EBJQIPE8-1VX8; cto_bundle=0GKr-l9XdHpnQ0lrS0x2VUdmcU93UGZNUWdsT0NXWEFGb1hvd01wTyUyRmMxU0gxUkdrNERNMmkzaW1TZlFET2d2QnRvUTQ5N0RIck5CbFh6Z1g0WXFwa3BBTFNrRUUzYkpoSkhzRkVJJTJCUFVydlkwb25iQ3NsUDhhbUxqVnBkJTJCQk1Wc3U4WDNTdk9NeGcwNzAlMkJiVHJKeWpsa25GZyUzRCUzRA; _ga_FVWZ0RM4DH=GS1.1.1730040525.2.1.1730041252.60.0.0; __browsiSessionID=92f6b3a3-9094-4dcf-89e1-04b2c5827a58&true&DEFAULT&in&desktop-4.33.528&false; __gads=ID=57304d5c4ddb3d3e:T=1727612021:RT=1731816932:S=ALNI_Mbt6i1vpZBOOsjYgBuV-dr_TfwslQ; __eoi=ID=f72143ddacbe1937:T=1727612021:RT=1731816932:S=AA-AfjYZQGDh7IRrMMRTrPPC0Df_; cto_bundle=uyVf9l9XdHpnQ0lrS0x2VUdmcU93UGZNUWdxRjlBRDJKYWxhbDJhNzF2Ulg3T1lsZjhNTm1jS01DSiUyRm0lMkY0WG0lMkIzZlNocGdseEtUdmt3cGZmJTJGdU5SVUNoVnlQVlF5MUVxZkMwcFA4TSUyQkRYRHYybUl4cVFuMDNpNlB2UGVET1BpdXBvQ3pCR20wR3JrOVdYRU9QVWtaaXBqcTd3JTNEJTNE; cto_bundle=uyVf9l9XdHpnQ0lrS0x2VUdmcU93UGZNUWdxRjlBRDJKYWxhbDJhNzF2Ulg3T1lsZjhNTm1jS01DSiUyRm0lMkY0WG0lMkIzZlNocGdseEtUdmt3cGZmJTJGdU5SVUNoVnlQVlF5MUVxZkMwcFA4TSUyQkRYRHYybUl4cVFuMDNpNlB2UGVET1BpdXBvQ3pCR20wR3JrOVdYRU9QVWtaaXBqcTd3JTNEJTNE; FCNEC=%5B%5B%22AKsRol-ZKP80s7Yhe8gizYOERsHv1sTk9H_T-N4XbmEWaj6GCanCs74ovC91tUT_aVBTGQziy5BpSyAPPo4vNTM3CgSJMSdfG2vj-XAuG1y7qkRVVYvLiIyxBW3PIHEBMI1ItYELQvXW6xr4JyYl3kK6Op7bChD94g%3D%3D%22%5D%5D; _ga_HNQ9P9MGZR=GS1.1.1731816927.4.1.1731817058.57.0.0',
        'priority': 'u=1, i',
        'referer': 'https://www.sofascore.com/',
        'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sentry-trace': '1690b0fd312745c4a7b27a49f223bc9a-88cdaff5546446b6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'x-requested-with': '54edb2',
    }
    headers['If-Modified-Since'] = get_time()
    response = requests.get(f'https://www.sofascore.com/api/v1/event/{mid}/average-positions', headers=headers)
    data = response.json()
    print(data)
    st.success("Got average positions.")
    #st.spinner("Getting subsitutes data..")
    # Extract players who are not substituted in
    substituted_in_players = {sub['playerIn']['name'] for sub in data['substitutions']}
    # Filter home and away players
    home_players = [player for player in data['home'] if player['player']['name'] not in substituted_in_players]
    away_players = [player for player in data['away'] if player['player']['name'] not in substituted_in_players]
    response = requests.get(f'https://www.sofascore.com/api/v1/event/{mid}/comments', headers)
    comments = response.json()['comments']
    # print(comments)
    subs = {}
    for i in range(len(comments)):
        if comments[i]["type"] == "substitution":
            subs.update({comments[i]["playerOut"]["name"]: comments[i]["playerIn"]["name"]})
    print("SUBS",subs)
    #return
    #st
    url = f"https://www.sofascore.com/api/v1/event/{mid}/lineups"
    parsed = urlparse(url)
    conn = http.client.HTTPSConnection(parsed.netloc)
    conn.request("GET", parsed.path)
    res = conn.getresponse()
    data = res.read()
    jdata = json.loads(data.decode("utf-8"))
    print(jdata)
    home(mid,jdata,subs)
    #return
    away(mid,jdata,subs)
    #return
