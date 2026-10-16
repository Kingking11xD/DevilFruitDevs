import { useEffect, useState, FormEvent } from "react";
import { Restaurant, RestaurantCreate } from "./types/restaurant";
import { fetchRestaurants, createRestaurant } from "./api/restaurants";

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // New state to trigger a clean re-fetch after creation
  const [refresh, setRefresh] = useState(0);

  const [newRestaurant, setNewRestaurant] = useState<RestaurantCreate>({
    name: "",
    cuisine: "",
    address: "",
  });

  useEffect(() => {
    let isCurrent = true; // Tracks if this specific effect run is still active

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRestaurants({
          search: search || undefined,
          cuisine: cuisineFilter || undefined,
        });
        
        // Only update state if a newer search hasn't already started
        if (isCurrent) {
          setRestaurants(data);
        }
      } catch (err) {
        if (isCurrent) {
          setError(err instanceof Error ? err.message : "An error occurred");
        }
      } finally {
        if (isCurrent) {
          setLoading(false);
        }
      }
    };

    const debounceTimer = setTimeout(() => {
      loadData();
    }, 250);

    return () => {
      clearTimeout(debounceTimer);
      isCurrent = false; // Marks this network request's results as outdated
    };
  }, [search, cuisineFilter, refresh]); // Added 'refresh' as a dependency

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newRestaurant.name || !newRestaurant.cuisine || !newRestaurant.address) {
      return;
    }

    try {
      await createRestaurant(newRestaurant);
      setNewRestaurant({ name: "", cuisine: "", address: "" });
      
      // Trigger a re-fetch so the backend handles filtering the new item
      setRefresh((prev) => prev + 1); 
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
