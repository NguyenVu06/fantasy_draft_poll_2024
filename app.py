import streamlit as st
import pandas as pd
import datetime
import altair as alt

# Constants
VOTES_FILE = "votes_with_time.csv"
OPTIONS_FILE = "sidebar_options.csv"
TIME_SPAN_HOURS = 3

# I/O functions
def load_votes():
    try:
        df = pd.read_csv(VOTES_FILE, parse_dates=['start_time'])
    except FileNotFoundError:
        df = pd.DataFrame(columns=['start_time', 'votes'])
    return df

def load_options():
    try:
        df = pd.read_csv(OPTIONS_FILE, parse_dates=['Voted At'])
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Voted At', 'Player'])
    return df

# Utility: tally expanded hours
def tally_time_windows(votes_df):
    if votes_df.empty:
        return pd.DataFrame(columns=['Time', 'Votes'])
    df = votes_df.copy()
    df['hours'] = df['start_time'].apply(
        lambda t: pd.date_range(t, periods=TIME_SPAN_HOURS, freq='H')
    )
    exploded = df.explode('hours')
    grouped = exploded.groupby('hours')['votes'].sum().reset_index()
    grouped.columns = ['Time', 'Votes']
    return grouped

# Main app
def main():
    st.title("2025 Fantasy Football Draft Scheduler")
    st.header("LEAGUE: Vaccines Massages Baby Mamas")
    st.write("Select your preferred time window; each vote spans 3 hours. The most common time window will be selected.")

    # Load data
    votes_df = load_votes()
    options_df = load_options()

    # Sidebar: player multiselect
    players = [
        "Nick (commish)🏅", "Nguyen🏅", "MyLinh", "Tuan", "David🏅",
        "Andrew🏅", "Joel", "Minh🏅", "Dima", "Dan🏅", "Anthony", "Cliffton"
    ]
    selected_players = st.sidebar.multiselect(
        "Choose one or more players to vote for:", players
    )

    # Valid date range setup
    valid_ranges = [
        (pd.to_datetime("today").date(), pd.to_datetime("2025-09-03").date())
    ]
    min_date = min(r[0] for r in valid_ranges)
    max_date = max(r[1] for r in valid_ranges)
    start_dt = datetime.datetime.combine(min_date, datetime.time(9))
    end_dt = datetime.datetime.combine(max_date, datetime.time(18))  # latest start to allow a 3-hour window

    # Datetime input for start time
    # Split datetime picker: use date + time input separately
    selected_date = st.date_input("Select draft date:", min_value=min_date, max_value=max_date, value=min_date)
    selected_time = st.time_input("Select start time (between 09:00 and 18:00):", value=datetime.time(9))

    # Combine into datetime
    selected_start = datetime.datetime.combine(selected_date, selected_time)

    # Clamp end time range: 3-hour slot must stay within 9:00 to 21:00
    if selected_time > datetime.time(18):
        st.error("Start time must be between 09:00 and 18:00 to allow a 3-hour voting window.")
        st.stop()

    selected_end = selected_start + datetime.timedelta(hours=TIME_SPAN_HOURS)


    selected_end = selected_start + datetime.timedelta(hours=TIME_SPAN_HOURS)

    # Show selected window with styled end time
    st.markdown(
        f"**Selected Window:** {selected_start.strftime('%m/%d %H:%M')} — "
        f"<span style='color:blue;font-weight:bold'>{selected_end.strftime('%H:%M')}</span>",
        unsafe_allow_html=True
    )

    # Submit vote
    if st.button("Submit Vote"):
        if not selected_players:
            st.error("Please select at least one player.")
        else:
            # Record options
            now = datetime.datetime.now()
            new_opts = pd.DataFrame([
                {'Voted At': now, 'Player': p} for p in selected_players
            ])
            options_df = pd.concat([options_df, new_opts], ignore_index=True)
            options_df.to_csv(OPTIONS_FILE, index=False)

            # Record votes per hour slot
            hours = pd.date_range(
                start=selected_start,
                end=selected_end - datetime.timedelta(hours=1),
                freq='H'
            )
            for slot in hours:
                mask = votes_df['start_time'] == slot
                if mask.any():
                    votes_df.loc[mask, 'votes'] += len(selected_players)
                else:
                    votes_df = pd.concat(
                        [votes_df, pd.DataFrame([{'start_time': slot, 'votes': len(selected_players)}])],
                        ignore_index=True
                    )
            votes_df.to_csv(VOTES_FILE, index=False)
            st.success("Your votes have been recorded!")

    # Display recorded options
    st.sidebar.write("Recorded Options:")
    st.sidebar.write(options_df)

    # Display vote results
    st.write("### Vote Frequency by Time")
    if votes_df.empty:
        st.write("No votes recorded yet.")
    else:
        tally_df = tally_time_windows(votes_df)
        chart = alt.Chart(tally_df).mark_bar().encode(
            x=alt.X('Time:T', title='Date & Time', axis=alt.Axis(format='%m-%d %H:%M', labelAngle=45)),
            y=alt.Y('Votes:Q', title='Number of Votes')
        ).properties(width=700, height=400)
        st.altair_chart(chart)
        st.write(tally_df.sort_values('Time'))

        # Show most common window
        idx = tally_df['Votes'].idxmax()
        if pd.notna(idx):
            common_start = tally_df.at[idx, 'Time']
            common_end = common_start + datetime.timedelta(hours=TIME_SPAN_HOURS)
            st.write(f"Most common 3-hour window: {common_start} to {common_end}")

if __name__ == "__main__":
    main()
