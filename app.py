import streamlit as st
import pandas as pd
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt


VOTES_FILE = "votes_with_time.csv"
OPTIONS_FILE = "sidebar_options.csv"
TIME_SPAN_HOURS = 3 

def load_votes():
    try:
        votes_df = pd.read_csv(VOTES_FILE, parse_dates=['start_time'])
    except FileNotFoundError:
        votes_df = pd.DataFrame(columns=['start_time', 'votes'])
    return votes_df

def save_votes(votes_df):
    votes_df.to_csv(VOTES_FILE, index=False)

def load_options():
    try:
        options_df = pd.read_csv(OPTIONS_FILE)
    except FileNotFoundError:
        options_df = pd.DataFrame(columns=['Voted At', 'Player'])
    return options_df

def save_option(selected_option):
    if selected_option != "None":  # Don't save if the selected option is "None"
        options_df = load_options()
        new_option = pd.DataFrame({'Voted At': [datetime.datetime.now()], 'Player': [selected_option]})
        options_df = pd.concat([options_df, new_option], ignore_index=True)
        options_df.to_csv(OPTIONS_FILE, index=False)

def find_common_time_window(votes_df):
    time_windows = defaultdict(int)
    
    for _, row in votes_df.iterrows():
        start_time = row['start_time']
        end_time = start_time + pd.Timedelta(hours=TIME_SPAN_HOURS)
        
        for time in pd.date_range(start=start_time, end=end_time, freq='H'):
            time_windows[time] += row['votes']
    
    # Find the most common time window
    if time_windows:
        common_start_time = max(time_windows, key=time_windows.get)
        common_end_time = common_start_time + pd.Timedelta(hours=TIME_SPAN_HOURS)
        return common_start_time, common_end_time
    return None, None

def plot_histogram(votes_df):
    if not votes_df.empty:
        all_times = []
        for _, row in votes_df.iterrows():
            start_time = row['start_time']
            end_time = start_time + pd.Timedelta(hours=TIME_SPAN_HOURS)
            all_times.extend(pd.date_range(start=start_time, end=end_time, freq='H'))
        
        # Create histogram
        plt.figure(figsize=(10, 6))
        plt.hist(all_times, bins=len(all_times)//TIME_SPAN_HOURS, rwidth=0.8)
        plt.title("Vote Frequency by Time")
        plt.xlabel("Time")
        plt.ylabel("Number of Votes")
        plt.xticks(rotation=45)
        st.pyplot(plt.gcf())

def main():
    st.title("2024 Fantasy Football Draft Scheduler")
    st.header("LEAGUE: Vaccines Massages Baby Mamas")
    st.write("Select your preferred date and time for the our draft. The most common time window will be selected.")
    st.write("Note: Each vote has an automatic 3-hour span. for example if you vote for 9:00 AM, you are also voting for 10:00 AM and 11:00 AM.")

    options = ["None","Nick (commish)", "Nguyen (2x champ)", "MyLinh", "Tuan", "David", "Andrew", "Joel", "Minh", "Dima", "Dan", "Anthony", "Nick's +1"]

    selected_option = st.sidebar.radio("Choose an option:", options)
    # Save the selected option
    



    # Load votes
    votes_df = load_votes()

    # Calendar and time widget for selecting a date and time
    selected_date = st.date_input("Choose a date", value=datetime.date.today())
    selected_time = st.time_input("Choose a time", value=datetime.time(9, 0))  # Default to 9:00 AM

    selected_datetime = datetime.datetime.combine(selected_date, selected_time)
    if selected_date >= datetime.date(2024, 9, 5):
        st.error("NO DUMMY, THIS IS KICK OFF DAY!, VOTE AGAIN")

    else:
        if st.button("Vote"):
            save_option(selected_option)
            st.sidebar.write(f"{selected_option} Voting")
        # Check if the selected datetime is already in the votes
            if selected_datetime in votes_df['start_time'].values:
                # Increment the vote count for the selected datetime
                votes_df.loc[votes_df['start_time'] == selected_datetime, 'votes'] += 1
            else:
                # Add the selected datetime with a vote count of 1
                new_vote = pd.DataFrame({'start_time': [selected_datetime], 'votes': [1]})
                votes_df = pd.concat([votes_df, new_vote], ignore_index=True)

        # Save the updated votes
        if selected_option != "None":
            save_votes(votes_df)

        # Display the saved options
            st.sidebar.write("Recorded Options:")
            options_df = load_options()
            st.sidebar.write(options_df)
            st.success(f"Click 'Vote' to record your selection at {selected_datetime}!")

    # Display the vote results
    st.write("Vote Results:")
    if not votes_df.empty:
        votes_df_sorted = votes_df.sort_values(by='start_time')
        st.write(votes_df_sorted)
    else:
        st.write("No votes recorded yet.")

    # Calculate and display the most common time window
    common_start_time, common_end_time = find_common_time_window(votes_df)
    if common_start_time and common_end_time:
        st.write(f"The most common time window is from {common_start_time} to {common_end_time}.")
    else:
        st.write("No common time window determined yet.")

    # Display the histogram
    st.write("Vote Frequency Histogram:")
    plot_histogram(votes_df)

    

if __name__ == "__main__":
    main()
