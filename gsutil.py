import csv
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
