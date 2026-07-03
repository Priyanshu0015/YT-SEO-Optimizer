import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os
# --- CONFIGURATION ---
# REPLACE THIS WITH YOUR ACTUAL API KEY FROM GOOGLE CLOUD
API_KEY = os.getenv("API_KEY")
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

st.set_page_config(page_title="YouTube Views Analyzer", layout="wide")
st.title(" YouTube Topic View Analyzer")
st.write("Analyze the top videos for any topic and graph their real view counts.")

topic = st.text_input("Enter a topic to analyze views (e.g., Python Tutorial, Minecraft):")

if st.button("Analyze Views") and topic:
    if API_KEY == "YOUR_API_KEY_HERE":
        st.error(" Please add your YouTube API Key to the Python script!")
    else:
        with st.spinner(f'Fetching live view data for "{topic}"...'):
            try:
                # 1. Connect to the YouTube API
                youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
                
                # 2. Search for the top 15 videos matching the topic
                search_response = youtube.search().list(
                    q=topic,
                    part='id,snippet',
                    maxResults=15, # You can change this up to 50
                    type='video',
                    order='relevance' # Get the most relevant videos
                ).execute()

                video_ids = []
                video_titles = []
                
                # Extract Video IDs and Titles
                for search_result in search_response.get('items', []):
                    video_ids.append(search_result['id']['videoId'])
                    video_titles.append(search_result['snippet']['title'])

                # 3. Get the exact statistics (view counts) for those specific videos
                if video_ids:
                    stats_response = youtube.videos().list(
                        part='statistics',
                        id=','.join(video_ids) # Send all IDs at once to save API quota
                    ).execute()
                    
                    view_counts = []
                    
                    # Extract the view counts
                    for stat_result in stats_response.get('items', []):
                        # Some videos might have stats hidden, so we use .get() with a default of 0
                        views = int(stat_result['statistics'].get('viewCount', 0))
                        view_counts.append(views)
                        
                    # 4. Create a DataFrame
                    df = pd.DataFrame({
                        'Video Title': video_titles,
                        'Views': view_counts
                    })
                    
                    # Clean up titles if they are too long for the graph
                    df['Short Title'] = df['Video Title'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x)
                    
                    # Sort by views so the highest is at the top
                    df = df.sort_values('Views', ascending=False).reset_index(drop=True)
                    
                    # --- DISPLAY THE RESULTS ---
                    st.write(f"### Top Videos for '{topic}'")
                    
                    # Total views calculation
                    total_views = df['Views'].sum()
                    st.metric(label="Total Views (Top 15 Videos)", value=f"{total_views:,}")
                    
                    # 5. Draw the Graph
                    st.write("### View Count Comparison")
                    
                    # We use matplotlib to create a horizontal bar chart
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Create a horizontal bar chart
                    bars = ax.barh(df['Short Title'], df['Views'], color='skyblue')
                    
                    # Format the axes
                    ax.set_xlabel('Number of Views')
                    ax.set_ylabel('Video Title')
                    ax.set_title(f"Top 15 Videos for '{topic}'")
                    
                    # Format x-axis labels to avoid scientific notation (e.g., 1e6)
                    ax.ticklabel_format(style='plain', axis='x')
                    
                    # Invert y-axis so the highest views are at the top of the chart
                    ax.invert_yaxis()
                    
                    # Add commas to the x-axis numbers for readability
                    ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
                    
                    # Display the plot in Streamlit
                    st.pyplot(fig)
                    
                    # Display the raw data table
                    st.write("###  Raw Data")
                    # Format the views column with commas in the dataframe display
                    st.dataframe(df[['Video Title', 'Views']].style.format({'Views': '{:,}'}), use_container_width=True)
                    
                else:
                    st.warning("No videos found for this topic.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")