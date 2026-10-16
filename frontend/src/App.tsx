import { useEffect, useState, FormEvent } from "react";
import { Restaurant, RestaurantCreate } from "./types/restaurant";
import { fetchRestaurants, createRestaurant } from "./api/restaurants";

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newRestaurant, setNewRestaurant] = useState<RestaurantCreate>({
    name: "",
    cuisine: "",
    address: "",
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRestaurants({
        search: search || undefined,
        cuisine: cuisineFilter || undefined,
      });
      setRestaurants(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      loadData();
    }, 250);
    return () => clearTimeout(debounceTimer);
  }, [search, cuisineFilter]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newRestaurant.name || !newRestaurant.cuisine || !newRestaurant.address) {
      return;
    }

    try {
      const created = await createRestaurant(newRestaurant);
      setRestaurants((prev) => [...prev, created]);
      setNewRestaurant({ name: "", cuisine: "", address: "" });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create restaurant");
    }
  };

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <h1>Restaurant Management</h1>

      <section style={{ border: "1px solid #ccc", padding: "1rem", borderRadius: 8, marginBottom: "2rem" }}>
        <h2>Add Restaurant</h2>
        <form onSubmit={handleCreate} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input
            placeholder="Name"
            value={newRestaurant.name}
            onChange={(e) => setNewRestaurant({ ...newRestaurant, name: e.target.value })}
            required
          />
          <input
            placeholder="Cuisine"
            value={newRestaurant.cuisine}
            onChange={(e) => setNewRestaurant({ ...newRestaurant, cuisine: e.target.value })}
            required
          />
          <input
            placeholder="Address"
            value={newRestaurant.address}
            onChange={(e) => setNewRestaurant({ ...newRestaurant, address: e.target.value })}
            required
          />
          <button type="submit">Save</button>
        </form>
      </section>

      <section style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
        <input
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, padding: "0.5rem" }}
        />
        <input
          placeholder="Filter by cuisine..."
          value={cuisineFilter}
          onChange={(e) => setCuisineFilter(e.target.value)}
          style={{ width: 180, padding: "0.5rem" }}
        />
      </section>

      {loading && <p>Loading restaurants...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && restaurants.length === 0 ? (
        <p>No restaurants found.</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {restaurants.map((item) => (
            <li
              key={item.id}
              style={{
                borderBottom: "1px solid #eee",
                padding: "0.75rem 0",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <div>
                <strong>{item.name}</strong> — <em>{item.cuisine}</em>
                <div style={{ color: "#666", fontSize: "0.9rem" }}>{item.address}</div>
              </div>
              <span style={{ color: "#aaa", fontSize: "0.85rem" }}>ID: {item.id}</span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}