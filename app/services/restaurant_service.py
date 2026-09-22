from app.repositories.restaurant_repo import RestaurantRepo


class RestaurantService:

    def __init__(self, repository):
        self.repository = repository

    def get_all_restaurants(self):
        return self.repository.get_all()