import json


class RestaurantRepo:

    def __init__(self, file_path):
        self.file_path = file_path

    def get_all(self):
        with open(self.file_path, "r") as file:
            return json.load(file)