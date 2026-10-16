// src/types/restaurant.ts
export interface Restaurant {
  id: number;
  name: string;
  cuisine: string;
  address: string;
}

export interface RestaurantCreate {
  name: string;
  cuisine: string;
  address: string;
}

export interface RestaurantUpdate {
  name?: string;
  cuisine?: string;
  address?: string;
}

export interface RestaurantQueryParams {
  search?: string;
  cuisine?: string;
}