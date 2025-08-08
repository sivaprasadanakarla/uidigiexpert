
import base64

def get_image_base64(path):
	with open(path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode()
