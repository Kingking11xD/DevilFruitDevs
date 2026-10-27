// src/api/restaurants.ts
import {
  Restaurant,
  RestaurantCreate,
  RestaurantUpdate,
  RestaurantQueryParams,
} from "../types/restaurant";

const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchRestaurants(
  params?: RestaurantQueryParams
): Promise<Restaurant[]> {
  const query = new URLSearchParams();
  if (params?.search) query.append("search", params.search);
  if (params?.cuisine) query.append("cuisine", params.cuisine);

  const url = `${API_BASE_URL}/restaurants${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch restaurants: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchRestaurantById(id: number): Promise<Restaurant> {
  const response = await fetch(`${API_BASE_URL}/restaurants/${id}`);
  if (!response.ok) {
    throw new Error(`Restaurant with ID ${id} not found.`);
  }
  return response.json();
}

export async function createRestaurant(data: RestaurantCreate): Promise<Restaurant> {
  const response = await fetch(`${API_BASE_URL}/restaurants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let errorMessage = "Failed to create restaurant.";

    // Parse FastAPI's array of validation errors
    if (Array.isArray(errorData.detail)) {
      errorMessage = errorData.detail.map((err: any) => err.msg).join(", ");
    } else if (typeof errorData.detail === "string") {
      errorMessage = errorData.detail;
    }

    throw new Error(errorMessage);
  }
  return response.json();
}

export async function updateRestaurant(
  id: number,
  changes: RestaurantUpdate
): Promise<Restaurant> {
  const response = await fetch(`${API_BASE_URL}/restaurants/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to update restaurant.");
  }
  return response.json();
}
