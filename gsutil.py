import csv
import io
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
from google.cloud import storage


def read_schedule_from_gcs(bucket_name, source_blob_name):
    """Reads a CSV file from a Google Cloud Storage bucket and returns the data as a list of dictionaries.

    Args:
        bucket_name (str): The name of the GCS bucket.
        source_blob_name (str): The full path to the file in the bucket (e.g., 'data/schedule.csv').

    Returns:
        list: A list of dictionaries, where each dictionary represents a row in the CSV.
    """
    try:
        # Initialize a client
        storage_client = storage.Client()

        # Get the bucket and the blob (file)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)

        # Download the contents of the blob as a string
        csv_string = blob.download_as_string().decode('utf-8')

        # Use StringIO to treat the string as a file-like object
        csv_file = StringIO(csv_string)

        # Use csv.DictReader to read the data into a list of dictionaries
        reader = csv.DictReader(csv_file)
        schedule = [row for row in reader]

        # Convert 'age' from string to integer
        for item in schedule:
            if 'age' in item:
                item['age'] = int(item['age'])

        return schedule

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def read_notification_history_from_gcs(bucket_name: str, days_to_read: int = 7) -> pd.DataFrame:
    """
    Reads notification history from GCS for the last specified number of days.
    It looks for files named 'notification_sent_ddmmyyyy.csv'.

    Args:
        bucket_name (str): The name of the GCS bucket where notification files are stored.
        days_to_read (int): The number of past days (including today) to read data for.

    Returns:
        pd.DataFrame: A DataFrame containing combined notification history.
                      Returns an empty DataFrame if no files are found or an error occurs.
    """
    all_notifications_df = pd.DataFrame()
    today = datetime.now().date()


    for i in range(days_to_read):
        current_date = today - timedelta(days=i)
        file_date_str = current_date.strftime("%d%m%Y")
        file_name = f"notification_sent_{file_date_str}.csv"
        blob_path = file_name  # Assuming files are directly in the bucket root
        storage_client = storage.Client()

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        if blob.exists():
            try:
                # Download blob content to an in-memory BytesIO object
                # This is efficient for pandas to read directly
                blob_content = blob.download_as_bytes()
                df_day = pd.read_csv(io.BytesIO(blob_content))
                all_notifications_df = pd.concat([all_notifications_df, df_day], ignore_index=True)
                print(f"✅ Loaded: `{file_name}`")
            except Exception as e:
                print(f"⚠️ Error reading `{file_name}`: {e}")
        else:
            print(f"ℹ️ File not found: `{file_name}`")

    # Sort the DataFrame by date (assuming 'notification_sent_date' is in 'MMM DD' format,
    # we'll need to convert it to a sortable format if not already sorted by file name)
    # For robust sorting, it's best to use the original datetime objects or a sortable string.
    # Since we're concatenating, the order might be mixed. Let's re-sort by parsing the date.
    try:
        # Create a temporary sortable date column (e.g., 'YYYY-MM-DD')
        # Assuming 'notification_sent_date' is like "Jul 22" and we need to infer the year.
        # For simplicity, we'll assume the year is the current year.
        # A more robust solution might pass the year or use a full date in the CSV.
        all_notifications_df['sort_date'] = all_notifications_df['notification_sent_date'].apply(
            lambda x: datetime.strptime(f"{x} {today.year}", "%b %d %Y").date()
        )
        all_notifications_df = all_notifications_df.sort_values(by='sort_date', ascending=False).drop(
            columns=['sort_date'])
    except KeyError:
        print("Column 'notification_sent_date' not found for sorting. Displaying as-is.")
    except Exception as e:
        print(f"Error sorting notifications: {e}. Displaying as-is.")

    return all_notifications_df


if __name__ == "__main__":
    """This block is executed only when the script is run directly."""
    # --- Example Usage ---
    # Replace with your bucket and file path
    bucket_name = "digexpbucket"
    source_blob_name = "meetings.csv"

    # Call the function to get the schedule
    schedule = read_schedule_from_gcs(bucket_name, source_blob_name)

    # Print the resulting schedule to verify
    if schedule:
        print("Schedule read from GCS:")
        for appointment in schedule:
            print(appointment)
    else:
        print("Failed to read schedule from GCS.")
