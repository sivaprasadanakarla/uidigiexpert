
import base64

def get_image_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


if __name__ == "__main__":
    """This block is executed only when the script is run directly."""
    #bucket_name = "digexpbuckselfdata"
    # Call the function to get the schedule
    schedule = get_image_base64('Citi_1.png')
    print(schedule)

