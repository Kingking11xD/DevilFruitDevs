import { useEffect, useState, FormEvent } from "react";
import { Restaurant, RestaurantCreate, RestaurantUpdate } from "./types/restaurant";
import { fetchRestaurants, createRestaurant, updateRestaurant } from "./api/restaurants";

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [refresh, setRefresh] = useState(0);

  const [newRestaurant, setNewRestaurant] = useState<RestaurantCreate>({
    name: "",
    cuisine: "",
    address: "",
  });

  // New state variables for editing
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editFormData, setEditFormData] = useState<RestaurantUpdate>({});

  useEffect(() => {
    let isCurrent = true; 

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRestaurants({
          search: search || undefined,
          cuisine: cuisineFilter || undefined,
        });
        
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
      isCurrent = false; 
    };
  }, [search, cuisineFilter, refresh]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newRestaurant.name || !newRestaurant.cuisine || !newRestaurant.address) {
      return;
    }

    try {
      await createRestaurant(newRestaurant);
      setNewRestaurant({ name: "", cuisine: "", address: "" });
      setRefresh((prev) => prev + 1); 
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create restaurant");
    }
  };

  // New function to handle saving updates
  const handleUpdate = async (id: number) => {
    try {
      await updateRestaurant(id, editFormData);
      setEditingId(null);
      setRefresh((prev) => prev + 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update restaurant");
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
                alignItems: "center"
              }}
            >
              {editingId === item.id ? (
                // Edit Mode UI
                <div style={{ display: "flex", gap: "0.5rem", flex: 1, marginRight: "1rem" }}>
                  <input
                    value={editFormData.name || ""}
                    onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                    style={{ flex: 1 }}
                  />
                  <input
                    value={editFormData.cuisine || ""}
                    onChange={(e) => setEditFormData({ ...editFormData, cuisine: e.target.value })}
                    style={{ width: "100px" }}
                  />
                  <input
                    value={editFormData.address || ""}
                    onChange={(e) => setEditFormData({ ...editFormData, address: e.target.value })}
                    style={{ flex: 1 }}
                  />
                </div>
              ) : (
                // Display Mode UI
                <div style={{ flex: 1 }}>
                  <strong>{item.name}</strong> — <em>{item.cuisine}</em>
                  <div style={{ color: "#666", fontSize: "0.9rem" }}>{item.address}</div>
                </div>
              )}
              
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <span style={{ color: "#aaa", fontSize: "0.85rem", marginRight: "1rem" }}>ID: {item.id}</span>
                
                {editingId === item.id ? (
                  <>
                    <button onClick={() => handleUpdate(item.id)}>Save</button>
                    <button onClick={() => setEditingId(null)}>Cancel</button>
                  </>
                ) : (
                  <button 
                    onClick={() => {
                      setEditingId(item.id);
                      setEditFormData({ name: item.name, cuisine: item.cuisine, address: item.address });
                    }}
                  >
                    Edit
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}