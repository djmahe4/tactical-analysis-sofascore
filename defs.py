import requests
import datetime
import random
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import streamlit as st
colors = ['blue', 'red', 'cyan', 'magenta', 'yellow',  'maroon', 'olive', 'aqua', 'teal', 'navy', 'fuchsia', 'purple', 'orange', 'gold', 'pink', 'brown', 'coral', 'indigo', 'khaki', 'plum', 'salmon', 'violet', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'firebrick', 'forestgreen', 'goldenrod', 'hotpink', 'indianred', 'midnightblue', 'orangered', 'orchid', 'palevioletred', 'peru', 'rosybrown', 'royalblue', 'saddlebrown', 'sandybrown', 'seagreen', 'sienna', 'skyblue', 'slateblue', 'slategray', 'steelblue', 'tan', 'thistle', 'tomato', 'turquoise', 'wheat', 'yellowgreen']
def most_frequent_positions(pid,mid, max_clusters=3):
    # ... (rest of the function, including frequency map creation and sorting)
    response = requests.get(f"https://www.sofascore.com/api/v1/event/{mid}/player/{pid}/heatmap")
    st.write("https://www.sofascore.com/api/v1/event/{mid}/player/{pid}/heatmap")
    st.write(response.text)
    heatmap_data = response.json()["heatmap"]
    print(heatmap_data)
    frequency_map = {}
    for point in heatmap_data:
        x, y = point['x'], point['y']
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                new_x, new_y = x + dx, y + dy
                if (new_x, new_y) in [(p['x'], p['y']) for p in heatmap_data]:
                    frequency_map[(new_x, new_y)] = frequency_map.get((new_x, new_y), 0) + 1

  
    n=0
    s=0
    for x,y in frequency_map.items():
        n+=1
        s+=y
    print(s/n)
    print(frequency_map)
    high_frequency_positions = [[(x, y),count] for (x, y), count in frequency_map.items() if count > int(s/n)]
    return high_frequency_positions
def home(home_players,mid):
        # Create a figure for the home team
    fig, ax = plt.subplots(figsize=(10, 8))
    # Draw the pitch
    pitch = Pitch(pitch_type='statsbomb', line_color='black', pitch_color='#d9ead3')#,label=True)
    pitch.pitch_length=100
    pitch.pitch_width=100
    pitch.draw(ax=ax)
    # Ensure player positions are within pitch boundaries
    #for player in home_players:
        #player['averageX'] = player['averageX'] * 1.2
        #player['averageY'] = player['averageY'] * 0.8

    # Plot player positions with varying marker sizes
    for player in home_players:
        random_color = random.choice(colors)
        ax.scatter(player['averageX']* 1.2, player['averageY']* 0.8, s=player['pointsCount'] * 10, alpha=0.7,color=random_color)
        ax.text(player['averageX']* 1.2, player['averageY']* 0.8, player['player']['jerseyNumber'], ha='center', va='center', color='white', fontsize=12, fontweight='bold')
        movement=most_frequent_positions(player['player']['id'],12744977)
        j=10
        for i in movement:
          j+=1
          pitch.arrows(player['averageX']* 1.2, player['averageY']* 0.8, i[0][0]* 1.2, i[0][1]* 0.8, ax=ax,color=random_color,linewidth=i[1]*0.02,capstyle='butt',  # capstyle round so the glow extends past the line
                    alpha=i[1]*0.02)


    # Invert the y-axis
    plt.gca().invert_yaxis()

    ax.set_title('Home Team')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    #plt.show()
    st.pyplot(fig)
def away(away_players,mid):
    # Create a figure for the home team
    fig, ax = plt.subplots(figsize=(10, 8))
    # Draw the pitch
    pitch = Pitch(pitch_type='statsbomb', line_color='black', pitch_color='#d9ead3')#,label=True)
    pitch.pitch_length=100
    pitch.pitch_width=100
    pitch.draw(ax=ax)

    # Ensure player positions are within pitch boundaries
    #for player in away_players:
        #player['averageX'] = player['averageX'] * 1.2
        #player['averageY'] = player['averageY'] * 0.8

    # Plot player positions with varying marker sizes
    for player in away_players:
        ax.scatter(player['averageX']* 1, player['averageY']* 1, s=player['pointsCount'] * 10, alpha=0.7,label=player['player']['shortName'])
        ax.text(player['averageX']* 1, player['averageY']* 1, player['player']['jerseyNumber'], ha='center', va='center', color='white', fontsize=12, fontweight='bold')
        movement=most_frequent_positions(player['player']['id'],mid)
        #j=10
        for i in movement:
        #j+=1
            pitch.arrows(player['averageX']* 1, player['averageY']* 1, i[0][0]* 1, i[0][1]* 1, ax=ax,color='red',linewidth=i[1]*0.02,capstyle='butt',  # capstyle round so the glow extends past the line
                    alpha=i[1]*0.02)

    # Invert the y-axis
    plt.gca().invert_yaxis()

    ax.set_title('Away Team')
    # Adjust legend to be outside the plot 
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    #plt.show()
    st.pyplot(fig)
def init():
    # Get today's date 
    today = datetime.date.today() # Format the date as YYYY-MM-DD 
    formatted_date = today.strftime("%Y-%m-%d") 

    response = requests.get(
    f'https://www.sofascore.com/api/v1/sport/football/scheduled-events/{formatted_date}'
    )
    data=response.json()['events']
    diction={}
    for i in data:
        if i['tournament']['uniqueTournament']['hasEventPlayerStatistics']==False:
            continue
        print(i)
        print(i.keys())
        print(i['homeTeam']['name'])
        print(i['awayTeam']['name'])
        print(i['id'])
        #break
        try:
            diction.update({f"{i['homeTeam']['name']} {i['homeScore']['display']} vs {i['awayTeam']['name']} {i['awayScore']['display']}":i['id']})
        except KeyError:
            continue
            diction.update({f"{i['homeTeam']['name']} vs {i['awayTeam']['name']}":i['id']})
    return diction
def match_pos(id=12057899):
    response = requests.get(f'https://www.sofascore.com/api/v1/event/{id}/average-positions')
    try:
        data=response.json()
    except requests.exceptions.JSONDecodeError:
        print(response.text)
    # Extract players who are not substituted in
    substituted_in_players = {sub['playerIn']['name'] for sub in data['substitutions']}

# Filter home and away players
    home_players = [player for player in data['home'] if player['player']['name'] not in substituted_in_players]
    away_players = [player for player in data['away'] if player['player']['name'] not in substituted_in_players]
    home(home_players,mid=id)
    away(away_players,mid=id)



#match_pos()
#init()
