import { useEffect, useState, FormEvent } from "react";
import { Restaurant, RestaurantCreate, RestaurantUpdate } from "./types/restaurant";
import { fetchRestaurants, createRestaurant, updateRestaurant } from "./api/restaurants";
import CustomerApp from "./CustomerApp";

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [refresh, setRefresh] = useState(0);
  const [isAdmin, setIsAdmin] = useState(false);
  const [activeTab, setActiveTab] = useState<'restaurants' | 'profile'>('restaurants');

  const [newRestaurant, setNewRestaurant] = useState<RestaurantCreate>({
    name: "",
    cuisine: "",
    address: "",
  });

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
    <>
      <style>{`
        :root { max-width: 100% !important; margin: 0 !important; padding: 0 !important; text-align: left !important; }
        html, body, #root { width: 100%; min-height: 100vh; margin: 0; padding: 0; background-color: #1e272e; }
        input:focus { outline: 2px solid #ffd700; }
        input::placeholder { color: rgba(139, 0, 0, 0.5); font-style: italic; }
      `}</style>
      
      <div style={{ backgroundColor: "#1e272e", minHeight: "100vh", width: "100%", padding: "2rem 1rem", boxSizing: "border-box", backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.9))", display: "flex", justifyContent: "center" }}>
        <main style={{ width: "100%", maxWidth: 900, backgroundColor: "#f4e4bc", border: "10px solid #3e2723", borderRadius: "8px", padding: "2.5rem", boxShadow: "0 15px 40px rgba(0,0,0,0.9)", fontFamily: "'Palatino Linotype', 'Book Antiqua', Palatino, serif", position: "relative" }}>
          
          <header style={{ textAlign: "center", borderBottom: "4px dashed #8b0000", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
            <h1 style={{ fontSize: "3.5rem", color: "#8b0000", margin: 0, textTransform: "uppercase", letterSpacing: "4px", textShadow: "3px 3px 0px #ffd700" }}>
              ☠️ Grand Line Eats 🍖
            </h1>
            <p style={{ fontSize: "1.3rem", color: "#3e2723", fontWeight: "bold", margin: "0.5rem 0 0 0", letterSpacing: "1px" }}>The Fastest Transponder Snail Delivery!</p>
          </header>

          {/* Navigation Tabs */}
          <nav style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2.5rem', borderBottom: '2px solid #a67b5b', paddingBottom: '1.5rem' }}>
            <button
              onClick={() => setActiveTab('restaurants')}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: activeTab === 'restaurants' ? '#8b0000' : '#3e2723',
                color: '#ffd700',
                border: '3px solid #ffd700',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                fontFamily: 'inherit',
                boxShadow: activeTab === 'restaurants' ? 'inset 0 0 10px rgba(0,0,0,0.5)' : '3px 3px 0px rgba(0,0,0,0.5)',
                transform: activeTab === 'restaurants' ? 'translateY(2px)' : 'none',
                transition: 'all 0.1s ease-in-out'
              }}
            >
              🍖 Find Grub
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: activeTab === 'profile' ? '#8b0000' : '#3e2723',
                color: '#ffd700',
                border: '3px solid #ffd700',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '1.1rem',
                fontFamily: 'inherit',
                boxShadow: activeTab === 'profile' ? 'inset 0 0 10px rgba(0,0,0,0.5)' : '3px 3px 0px rgba(0,0,0,0.5)',
                transform: activeTab === 'profile' ? 'translateY(2px)' : 'none',
                transition: 'all 0.1s ease-in-out'
              }}
            >
              ⚓ Captain's Log
            </button>
          </nav>

          {/* Tab Content: Profile / Auth */}
          {activeTab === 'profile' && (
            <section style={{ backgroundColor: "rgba(255, 255, 255, 0.5)", padding: "1.5rem", borderRadius: "12px", border: "2px solid #a67b5b", marginBottom: "2.5rem", boxShadow: "inset 0 0 15px rgba(139,0,0,0.05)" }}>
               <h2 style={{ color: "#3e2723", borderBottom: "2px solid #a67b5b", paddingBottom: "0.75rem", marginTop: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}>
                 ⚓ Captain's Log (Profile)
               </h2>
               <CustomerApp />
            </section>
          )}

          {/* Tab Content: Restaurants */}
          {activeTab === 'restaurants' && (
            <>
              {/* Admin Toggle */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '2rem' }}>
                <button 
                  onClick={() => setIsAdmin(!isAdmin)} 
                  style={{ backgroundColor: isAdmin ? '#8b0000' : '#3e2723', color: '#ffd700', padding: '0.75rem 1.25rem', border: '3px solid #ffd700', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontFamily: "inherit", boxShadow: "3px 3px 0px rgba(0,0,0,0.5)", transition: "all 0.2s" }}
                >
                  {isAdmin ? '❌ Exit Fleet Admiral Mode' : '🏴‍☠️ Fleet Admiral Mode'}
                </button>
              </div>

              {isAdmin && (
                <section style={{ border: "3px dashed #8b0000", padding: "1.5rem", backgroundColor: "#fff8dc", marginBottom: "2.5rem", borderRadius: "8px" }}>
                  <h2 style={{ marginTop: 0, color: "#8b0000" }}>🗺️ Chart a New Tavern</h2>
                  <form onSubmit={handleCreate} style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                    <input placeholder="Tavern Name" value={newRestaurant.name} onChange={(e) => setNewRestaurant({ ...newRestaurant, name: e.target.value })} required style={{ padding: "0.75rem", flex: 1, border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", fontFamily: "inherit" }} />
                    <input placeholder="Grub Type (Cuisine)" value={newRestaurant.cuisine} onChange={(e) => setNewRestaurant({ ...newRestaurant, cuisine: e.target.value })} required style={{ padding: "0.75rem", flex: 1, border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", fontFamily: "inherit" }} />
                    <input placeholder="Island Coordinates (Address)" value={newRestaurant.address} onChange={(e) => setNewRestaurant({ ...newRestaurant, address: e.target.value })} required style={{ padding: "0.75rem", flex: 2, border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", fontFamily: "inherit" }} />
                    <button type="submit" style={{ backgroundColor: "#3e2723", color: "#ffd700", border: "2px solid #8b0000", borderRadius: "4px", padding: "0.75rem 1.5rem", cursor: "pointer", fontWeight: "bold", fontFamily: "inherit", boxShadow: "2px 2px 0px rgba(0,0,0,0.3)" }}>Drop Anchor</button>
                  </form>
                </section>
              )}

              <section style={{ display: "flex", gap: "1.5rem", marginBottom: "2.5rem", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: "200px", position: "relative" }}>
                  <span style={{ position: "absolute", left: "12px", top: "14px", fontSize: "1.2rem" }}>🔭</span>
                  <input
                    placeholder="Search islands for food..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{ width: "100%", boxSizing: "border-box", padding: "0.85rem 0.85rem 0.85rem 2.8rem", border: "2px solid #8b0000", borderRadius: "6px", backgroundColor: "#fff8dc", fontSize: "1.1rem", fontFamily: "inherit" }}
                  />
                </div>
                <div style={{ width: "280px", position: "relative" }}>
                  <span style={{ position: "absolute", left: "12px", top: "14px", fontSize: "1.2rem" }}>🍖</span>
                  <input
                    placeholder="Filter by Grub..."
                    value={cuisineFilter}
                    onChange={(e) => setCuisineFilter(e.target.value)}
                    style={{ width: "100%", boxSizing: "border-box", padding: "0.85rem 0.85rem 0.85rem 2.8rem", border: "2px solid #8b0000", borderRadius: "6px", backgroundColor: "#fff8dc", fontSize: "1.1rem", fontFamily: "inherit" }}
                  />
                </div>
              </section>

              {loading && <p style={{ textAlign: "center", fontWeight: "bold", fontSize: "1.3rem", color: "#3e2723" }}>⏳ Consulting the Log Pose...</p>}
              {error && <p style={{ color: "#c62828", textAlign: "center", fontWeight: "bold", backgroundColor: "#ffebee", padding: "1rem", borderRadius: "4px", border: "2px solid #c62828" }}>🚨 {error}</p>}

              {!loading && restaurants.length === 0 ? (
                <p style={{ textAlign: "center", fontSize: "1.3rem", fontStyle: "italic", color: "#555" }}>No taverns found in these waters.</p>
              ) : (
                <div style={{ 
                  display: isAdmin ? "block" : "grid", 
                  gridTemplateColumns: isAdmin ? "1fr" : "repeat(auto-fill, minmax(260px, 1fr))", 
                  gap: "2rem" 
                }}>
                  {restaurants.map((item) => (
                    <div
                      key={item.id}
                      style={isAdmin ? {
                        borderBottom: "2px solid #a67b5b",
                        padding: "1rem 0",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center"
                      } : { 
                         backgroundColor: "#fdf6e3", 
                         border: "3px solid #3e2723", 
                         boxShadow: "6px 6px 0px rgba(62,39,35,0.9)",
                         padding: "1.5rem",
                         display: "flex",
                         flexDirection: "column",
                         alignItems: "center",
                         textAlign: "center",
                         position: "relative"
                      }}
                    >
                      {!isAdmin && (
                        <div style={{ position: "absolute", top: "-12px", left: "50%", transform: "translateX(-50%)", width: "24px", height: "24px", backgroundColor: "#8b0000", borderRadius: "50%", border: "3px solid #3e2723", boxShadow: "2px 3px 4px rgba(0,0,0,0.6)" }}></div>
                      )}

                      {editingId === item.id ? (
                        <div style={{ display: "flex", gap: "1rem", flex: 1, marginRight: "1rem", flexWrap: "wrap" }}>
                          <input
                            value={editFormData.name || ""}
                            onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                            style={{ padding: "0.5rem", flex: 1, border: "1px solid #8b0000" }}
                          />
                          <input
                            value={editFormData.cuisine || ""}
                            onChange={(e) => setEditFormData({ ...editFormData, cuisine: e.target.value })}
                            style={{ padding: "0.5rem", width: "120px", border: "1px solid #8b0000" }}
                          />
                          <input
                            value={editFormData.address || ""}
                            onChange={(e) => setEditFormData({ ...editFormData, address: e.target.value })}
                            style={{ padding: "0.5rem", flex: 2, border: "1px solid #8b0000" }}
                          />
                        </div>
                      ) : (
                        <div style={isAdmin ? { flex: 1 } : { width: "100%", flex: 1, marginTop: "0.5rem" }}>
                          {isAdmin ? (
                             <>
                               <strong style={{ fontSize: "1.2rem", color: "#3e2723" }}>{item.name}</strong> — <em>{item.cuisine}</em>
                               <div style={{ color: "#666", fontSize: "0.95rem", marginTop: "0.25rem" }}>{item.address}</div>
                             </>
                          ) : (
                             <>
                               <div style={{ fontSize: "0.9rem", color: "#8b0000", letterSpacing: "3px", fontWeight: "bold", marginBottom: "0.75rem", textShadow: "1px 1px 0px rgba(0,0,0,0.1)" }}>★ BOUNTY ★</div>
                               <h3 style={{ margin: "0 0 0.75rem 0", color: "#3e2723", fontSize: "1.8rem", textTransform: "uppercase", lineHeight: "1.1", wordWrap: "break-word" }}>{item.name}</h3>
                               <div style={{ backgroundColor: "#3e2723", color: "#ffd700", padding: "0.3rem 0.75rem", borderRadius: "4px", fontSize: "0.95rem", marginBottom: "1.2rem", display: "inline-block", fontWeight: "bold", border: "1px solid #ffd700" }}>{item.cuisine}</div>
                               <p style={{ margin: "0 0 1.5rem 0", color: "#444", fontSize: "1rem", fontStyle: "italic", borderTop: "1px dashed #a67b5b", paddingTop: "1rem" }}>📍 {item.address}</p>
                             </>
                          )}
                        </div>
                      )}
                      
                      {isAdmin ? (
                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <span style={{ color: "#888", fontSize: "0.9rem", marginRight: "1rem" }}>ID: {item.id}</span>
                          {editingId === item.id ? (
                            <>
                              <button onClick={() => handleUpdate(item.id)} style={{ backgroundColor: "#3e2723", color: "#fff", border: "none", padding: "0.4rem 1rem", cursor: "pointer", borderRadius: "4px" }}>Save</button>
                              <button onClick={() => setEditingId(null)} style={{ border: "1px solid #ccc", padding: "0.4rem 1rem", cursor: "pointer", borderRadius: "4px" }}>Cancel</button>
                            </>
                          ) : (
                            <button 
                              style={{ border: "2px solid #3e2723", padding: "0.4rem 1rem", cursor: "pointer", backgroundColor: "#fff8dc", borderRadius: "4px", fontWeight: "bold" }}
                              onClick={() => {
                                setEditingId(item.id);
                                setEditFormData({ name: item.name, cuisine: item.cuisine, address: item.address });
                              }}
                            >
                              Edit
                            </button>
                          )}
                        </div>
                      ) : (
                        <button 
                          style={{ backgroundColor: "#8b0000", color: "#fff", border: "2px solid #3e2723", padding: "0.85rem", width: "100%", fontWeight: "bold", cursor: "pointer", fontSize: "1.1rem", textTransform: "uppercase", letterSpacing: "1px", fontFamily: "inherit", boxShadow: "0 4px 0px #3e2723" }} 
                          onMouseDown={(e) => e.currentTarget.style.transform = "translateY(4px)"}
                          onMouseUp={(e) => e.currentTarget.style.transform = "translateY(0)"}
                          onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                          onClick={() => alert(`Summoning a delivery snail to ${item.name}!`)}
                        >
                          Send Snail 🐌
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}