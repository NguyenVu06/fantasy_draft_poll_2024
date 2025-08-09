import streamlit as st
import pandas as pd
import datetime
import altair as alt
import boto3
import streamlit as st
from io import StringIO

# Get AWS credentials from .streamlit/secrets.toml
aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
region_name = st.secrets.get("AWS_DEFAULT_REGION", "us-east-2")  # Default if not provided
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)
# Function to write DataFrame to S3
def write_df_to_s3(df, s3_path):
    bucket_name, key = s3_path.split("/", 1)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)



    s3.put_object(Bucket=bucket_name, Key=key, Body=csv_buffer.getvalue())



# Constants
S3_BUCKET_PATH = "nguyendaovu-bucket/Streamlit/"
VOTES_FILE = S3_BUCKET_PATH + "votes_with_time.csv"
OPTIONS_FILE = S3_BUCKET_PATH + "sidebar_options.csv"
RECORDED_VOTES = S3_BUCKET_PATH + "recorded_votes.csv"
TIME_SPAN_HOURS = 3


# I/O functions
def load_votes():
    bucket_name, key = VOTES_FILE.split("/", 1)
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=key)
        csv_bytes = obj["Body"].read()
        df = pd.read_csv(StringIO(csv_bytes.decode("utf-8")))
        df["start_time"] = pd.to_datetime(df["start_time"])
    except Exception:
        df = pd.DataFrame(columns=["start_time", "votes"])
    return df

def load_options():
    bucket_name, key = OPTIONS_FILE.split("/", 1)
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=key)
        csv_bytes = obj["Body"].read()
        df = pd.read_csv(StringIO(csv_bytes.decode("utf-8")))
        df["Voted At"]   = pd.to_datetime(df["Voted At"])
        df["start_time"] = pd.to_datetime(df["start_time"])
    except Exception:
        df = pd.DataFrame(columns=["Voted At", "Player", "start_time"])
    return df

def save_votes(df):
    write_df_to_s3(df, VOTES_FILE)

def save_options(df):
    write_df_to_s3(df, OPTIONS_FILE)

# Main app
def main():
    st.title("2025 Fantasy Football Draft Scheduler")
    st.header("LEAGUE: Vaccines Massages Baby Mamas")
    st.write("Select your preferred time window; each vote spans 3 hours. The most common time window will be selected.")

    # Load data
    votes_df = load_votes()
    options_df = load_options()

    # Sidebar: player select
    players = [
        "Nick (commish)🏅", "Nguyen🏅", "MyLinh", "Tuan", "David🏅",
        "Andrew🏅", "Joel", "Minh🏅", "Dima", "Dan🏅", "Anthony", "Cliffton"
    ]

    selected_players = st.selectbox("Choose a player to vote for:", players)

    # Valid date range setup
    valid_ranges = [
        (pd.to_datetime("today").date(), pd.to_datetime("2025-09-03").date())
    ]
    min_date = min(r[0] for r in valid_ranges)
    max_date = max(r[1] for r in valid_ranges)
    start_dt = datetime.datetime.combine(min_date, datetime.time(9))
    end_dt = datetime.datetime.combine(max_date, datetime.time(18))

    # Datetime input for start time
    selected_date = st.date_input("Select draft date:", min_value=min_date, max_value=max_date, value=min_date)
    selected_time = st.time_input("Select start time (between 09:00 and 18:00):", value=datetime.time(9), step=datetime.timedelta(minutes=60))
    selected_start = datetime.datetime.combine(selected_date, selected_time)

    if selected_time > datetime.time(22):
        st.error("Start time must be between 09:00 and 22:00 to allow a 3-hour voting window.")
        st.stop()

    selected_end = selected_start + datetime.timedelta(hours=TIME_SPAN_HOURS)
    selected_end_pst = selected_end - datetime.timedelta(hours=3)
    selected_start_pst = selected_start - datetime.timedelta(hours=3)

    st.markdown(
        f"**Selected Window:** {selected_start.strftime('%d %b %H:%M')} — "
        f"<span style='color:blue;font-weight:bold'>{selected_end.strftime('%H:%M')} EST</span>"
        f"  **OR**  {selected_start_pst.strftime('%d %b %H:%M')} — "
        f"<span style='color:blue;font-weight:bold'>{selected_end_pst.strftime('%H:%M')} PST</span>",
        unsafe_allow_html=True
    )

    if st.button("Submit Vote"):
        if not selected_players:
            st.error("Please select a player.")
        else:
            existing_votes = options_df[
                (options_df['start_time'] == selected_start) &
                (options_df['Player'] == selected_players)
            ]
            if not existing_votes.empty:
                st.warning("You have already voted for this player at this time slot.")
            else:
                hours = pd.date_range(
                    start=selected_start,
                    end=selected_end - datetime.timedelta(hours=1),
                    freq='H'
                )
                for slot in hours:
                    mask = votes_df['start_time'] == slot
                    if mask.any():
                        votes_df.loc[mask, 'votes'] += 1
                    else:
                        votes_df = pd.concat(
                            [votes_df, pd.DataFrame([{'start_time': slot, 'votes': 1}])],
                            ignore_index=True
                        )
                save_votes(votes_df)

                now = datetime.datetime.now()
                new_opts = pd.DataFrame([
                    {'Voted At': now, 'Player': selected_players, 'start_time': selected_start}
                ])
                options_df = pd.concat([options_df, new_opts], ignore_index=True)
                save_options(options_df)

                st.success("Your vote has been recorded!")

    # Sidebar vote display
    st.sidebar.write("Players Voted:")
    if options_df.empty:
        st.sidebar.write("No votes recorded yet.")
    else:
        options_df_display = options_df[['Voted At', 'Player']].copy()
        options_df_display['Voted At'] = options_df_display['Voted At'].dt.strftime('%Y-%m-%d')
        options_df_display = options_df_display.drop_duplicates(subset=['Voted At', 'Player'])
        st.sidebar.dataframe(options_df_display, use_container_width=True)

    # Vote chart
    st.write("### Vote Frequency by Time")
    if votes_df.empty:
        st.write("No votes recorded yet.")
    else:
        tally_df = votes_df.rename(columns={'start_time': 'Time', 'votes': 'Votes'})
        tally_df['Votes'] = pd.to_numeric(tally_df['Votes'], errors='coerce').fillna(0).astype(int)
        tally_df['Time'] = pd.to_datetime(tally_df['Time'])
        chart = alt.Chart(tally_df).mark_bar().encode(
            x=alt.X('Time:T', title='Date & Time', axis=alt.Axis(format='%d %b %H:%M', labelAngle=45)),
            y=alt.Y('Votes:Q', title='Number of Votes')
        ).properties(width=700, height=400)
        st.altair_chart(chart)
        st.write(tally_df.sort_values('Time'))

        idx = tally_df['Votes'].idxmax()
        if pd.notna(idx):
            common_start = tally_df.at[idx, 'Time']
            common_end = common_start + datetime.timedelta(hours=TIME_SPAN_HOURS)
            st.write(f"Most common 3-hour window: {common_start} to {common_end}")

if __name__ == "__main__":
    main()
