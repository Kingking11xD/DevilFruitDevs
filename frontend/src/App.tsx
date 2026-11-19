import { useEffect, useState, FormEvent } from "react";
import { Restaurant, RestaurantCreate, RestaurantUpdate } from "./types/restaurant";
import { fetchRestaurants, createRestaurant, updateRestaurant } from "./api/restaurants";
import CustomerApp, { Account } from "./CustomerApp";
import CartApp from "./CartApp";
import MenuApp from "./MenuApp";
import OrdersApp from "./OrdersApp";

export default function App() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [search, setSearch] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [refresh, setRefresh] = useState(0);
  const [isAdmin, setIsAdmin] = useState(false);
  
  type TabName = 'restaurants' | 'profile' | 'cart' | 'orders';
  const [activeTab, setActiveTab] = useState<TabName>('restaurants');
  const [token, setToken] = useState<string | null>(null);
  const [account, setAccount] = useState<Account | null>(null);
  const isStaff = account?.role === 'admin' || account?.role === 'restaurant_user';

  const canManageRestaurant = (id: number) => Boolean(token && (
    account?.role === 'admin' ||
    (account?.role === 'restaurant_user' && account.managed_restaurant_ids.includes(id))
  ));
  
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<number | null>(null);

  const [newRestaurant, setNewRestaurant] = useState<RestaurantCreate>({
    name: "",
    cuisine: "",
    address: "",
  });

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editFormData, setEditFormData] = useState<RestaurantUpdate>({});

  const updateToken = (newToken: string | null) => {
    setToken(newToken);
    setAccount(null);
    setIsAdmin(false);
    setEditingId(null);
    setEditFormData({});
    setNewRestaurant({ name: "", cuisine: "", address: "" });
    setSelectedRestaurantId(null);
  };

  useEffect(() => {
    let isCurrent = true; 
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRestaurants({ search: search || undefined, cuisine: cuisineFilter || undefined });
        if (isCurrent) setRestaurants(data);
      } catch (err) {
        if (isCurrent) setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        if (isCurrent) setLoading(false);
      }
    };
    const debounceTimer = setTimeout(() => loadData(), 250);
    return () => { clearTimeout(debounceTimer); isCurrent = false; };
  }, [search, cuisineFilter, refresh]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || account?.role !== 'admin') return;
    if (!newRestaurant.name || !newRestaurant.cuisine || !newRestaurant.address) return;
    try {
      await createRestaurant(newRestaurant, token);
      setNewRestaurant({ name: "", cuisine: "", address: "" });
      setRefresh(prev => prev + 1); 
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create restaurant");
    }
  };

  const handleUpdate = async (id: number) => {
    if (!token || !canManageRestaurant(id)) return;
    try {
      await updateRestaurant(id, editFormData, token);
      setEditingId(null);
      setRefresh(prev => prev + 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update restaurant");
    }
  };

  const handleAddToCart = async (menuItemId: number, quantity: number) => {
    if (!token || account?.role !== 'customer') {
        alert("You must sign in as a customer via the Captain's Log to order!");
        return;
    }
    try {
        await fetch('/customers/me/cart', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
        const res = await fetch('/customers/me/cart/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ menu_item_id: menuItemId, quantity })
        });
        if (res.ok) {
            alert("Booty added to your hold!");
        } else {
            const errData = await res.json();
            alert(errData.detail || "Failed to add to hold.");
        }
    } catch (err) {
        alert("Network error checking the hold.");
    }
  };

  const tabStyle = (tabName: TabName) => ({
    padding: '0.75rem 1.5rem',
    backgroundColor: activeTab === tabName && !selectedRestaurantId ? '#8b0000' : '#3e2723',
    color: '#ffd700',
    border: '3px solid #ffd700',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '1.1rem',
    fontFamily: 'inherit',
    boxShadow: activeTab === tabName && !selectedRestaurantId ? 'inset 0 0 10px rgba(0,0,0,0.5)' : '3px 3px 0px rgba(0,0,0,0.5)',
    transform: activeTab === tabName && !selectedRestaurantId ? 'translateY(2px)' : 'none',
    transition: 'all 0.1s ease-in-out'
  });

  return (
    <>
      <style>{`
        :root { max-width: 100% !important; margin: 0 !important; padding: 0 !important; text-align: left !important; }
        html, body, #root { width: 100%; min-height: 100vh; margin: 0; padding: 0; background-color: #1e272e; }
        input:focus { outline: 2px solid #ffd700; }
        input::placeholder { color: rgba(62, 39, 35, 0.65); font-style: italic; font-weight: 500; }
        input { color: #3e2723; font-weight: 600; }
      `}</style>
      
      <div style={{ backgroundColor: "#1e272e", minHeight: "100vh", width: "100%", padding: "2rem 1rem", boxSizing: "border-box", backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.9))", display: "flex", justifyContent: "center" }}>
        <main style={{ width: "100%", maxWidth: 900, backgroundColor: "#f4e4bc", border: "10px solid #3e2723", borderRadius: "8px", padding: "2.5rem", boxShadow: "0 15px 40px rgba(0,0,0,0.9)", fontFamily: "'Palatino Linotype', 'Book Antiqua', Palatino, serif", position: "relative" }}>
          
          <header style={{ textAlign: "center", borderBottom: "4px dashed #8b0000", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
            <h1 style={{ fontSize: "3.5rem", color: "#8b0000", margin: 0, textTransform: "uppercase", letterSpacing: "4px", textShadow: "3px 3px 0px #ffd700" }}>
              ☠️ Grand Line Eats 🍖
            </h1>
            <p style={{ fontSize: "1.3rem", color: "#3e2723", fontWeight: "bold", margin: "0.5rem 0 0 0", letterSpacing: "1px" }}>The Fastest Transponder Snail Delivery!</p>
          </header>

          <nav style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2.5rem', borderBottom: '2px solid #a67b5b', paddingBottom: '1.5rem' }}>
            <button onClick={() => { setActiveTab('restaurants'); setSelectedRestaurantId(null); }} style={tabStyle('restaurants')}>🍖 Find Grub</button>
            {!isStaff && <>
            <button onClick={() => { setActiveTab('cart'); setSelectedRestaurantId(null); }} style={tabStyle('cart')}>🛒 Ship's Cargo</button>
            <button onClick={() => { setActiveTab('orders'); setSelectedRestaurantId(null); }} style={tabStyle('orders')}>📜 Log Book (Orders)</button>
            </>}
            <button onClick={() => { setActiveTab('profile'); setSelectedRestaurantId(null); }} style={tabStyle('profile')}>⚓ Captain's Log (Auth)</button>
          </nav>

          {activeTab === 'profile' && (
            <section style={{ backgroundColor: "rgba(255, 255, 255, 0.5)", padding: "1.5rem", borderRadius: "12px", border: "2px solid #a67b5b", marginBottom: "2.5rem" }}>
               <h2 style={{ color: "#3e2723", borderBottom: "2px solid #a67b5b", paddingBottom: "0.75rem", marginTop: 0, textAlign: 'center' }}>⚓ Captain's Log (Profile)</h2>
               <CustomerApp token={token} setToken={updateToken} setAccount={setAccount} />
            </section>
          )}

          {activeTab === 'cart' && !isStaff && (
            <section style={{ marginBottom: "2.5rem" }}>
               <CartApp 
                  token={token} 
                  onCheckoutSuccess={() => {
                      alert('Order dispatched successfully! The snails are on their way.');
                      setActiveTab('orders');
                  }} 
               />
            </section>
          )}
          
          {activeTab === 'orders' && !isStaff && (
            <section style={{ marginBottom: "2.5rem" }}><OrdersApp token={token} /></section>
          )}

          {activeTab === 'restaurants' && selectedRestaurantId && (
            <section style={{ marginBottom: "2.5rem" }}>
              <MenuApp 
                token={token} 
                restaurantId={selectedRestaurantId} 
                isAdmin={isAdmin && canManageRestaurant(selectedRestaurantId)}
                onAddToCart={handleAddToCart}
                onBack={() => setSelectedRestaurantId(null)}
              />
            </section>
          )}

          {activeTab === 'restaurants' && !selectedRestaurantId && (
            <>
              {token && isStaff && <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '2rem' }}>
                <button 
                  onClick={() => { setIsAdmin(!isAdmin); setEditingId(null); }}
                  style={{ backgroundColor: isAdmin ? '#8b0000' : '#3e2723', color: '#ffd700', padding: '0.75rem 1.25rem', border: '3px solid #ffd700', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontFamily: "inherit", boxShadow: "3px 3px 0px rgba(0,0,0,0.5)", transition: "all 0.2s" }}
                >
                  {isAdmin ? '❌ Exit Fleet Admiral Mode' : '🏴‍☠️ Fleet Admiral Mode'}
                </button>
              </div>}

              {isAdmin && token && account?.role === 'admin' && (
                <section style={{ border: "3px dashed #8b0000", padding: "1.5rem", backgroundColor: "#fff8dc", marginBottom: "2.5rem", borderRadius: "8px" }}>
                  <h2 style={{ marginTop: 0, color: "#8b0000" }}>🗺️ Chart a New Tavern</h2>
                  <form onSubmit={handleCreate} style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
                    <label style={{ display: 'flex', flexDirection: 'column', flex: 1, fontWeight: 'bold', color: '#3e2723' }}>
                      Tavern Name
                      <input placeholder="Ex: Baratie" value={newRestaurant.name} onChange={(e) => setNewRestaurant({ ...newRestaurant, name: e.target.value })} required style={{ padding: "0.75rem", border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", color: "#3e2723", marginTop: "0.25rem" }} />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', flex: 1, fontWeight: 'bold', color: '#3e2723' }}>
                      Grub Type (Cuisine)
                      <input placeholder="Ex: Seafood" value={newRestaurant.cuisine} onChange={(e) => setNewRestaurant({ ...newRestaurant, cuisine: e.target.value })} required style={{ padding: "0.75rem", border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", color: "#3e2723", marginTop: "0.25rem" }} />
                    </label>
                    <label style={{ display: 'flex', flexDirection: 'column', flex: 2, fontWeight: 'bold', color: '#3e2723' }}>
                      Island Coordinates (Address)
                      <input placeholder="Ex: Sambas Region, East Blue" value={newRestaurant.address} onChange={(e) => setNewRestaurant({ ...newRestaurant, address: e.target.value })} required style={{ padding: "0.75rem", border: "2px solid #8b0000", borderRadius: "4px", backgroundColor: "#fff", color: "#3e2723", marginTop: "0.25rem" }} />
                    </label>
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                      <button type="submit" style={{ backgroundColor: "#3e2723", color: "#ffd700", border: "2px solid #8b0000", borderRadius: "4px", padding: "0.75rem 1.5rem", cursor: "pointer", fontWeight: "bold" }}>Drop Anchor</button>
                    </div>
                  </form>
                </section>
              )}

              <section style={{ display: "flex", gap: "1.5rem", marginBottom: "2.5rem", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: "200px", position: "relative" }}>
                  <span style={{ position: "absolute", left: "12px", top: "14px", fontSize: "1.2rem" }}>🔭</span>
                  <input placeholder="Search islands for food..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: "100%", boxSizing: "border-box", padding: "0.85rem 0.85rem 0.85rem 2.8rem", border: "2px solid #8b0000", borderRadius: "6px", backgroundColor: "#fff8dc", color: "#3e2723", fontSize: "1.1rem", fontFamily: "inherit" }} />
                </div>
                <div style={{ width: "280px", position: "relative" }}>
                  <span style={{ position: "absolute", left: "12px", top: "14px", fontSize: "1.2rem" }}>🍖</span>
                  <input placeholder="Filter by Grub..." value={cuisineFilter} onChange={(e) => setCuisineFilter(e.target.value)} style={{ width: "100%", boxSizing: "border-box", padding: "0.85rem 0.85rem 0.85rem 2.8rem", border: "2px solid #8b0000", borderRadius: "6px", backgroundColor: "#fff8dc", color: "#3e2723", fontSize: "1.1rem", fontFamily: "inherit" }} />
                </div>
              </section>

              {loading && <p style={{ textAlign: "center", fontWeight: "bold", fontSize: "1.3rem", color: "#3e2723" }}>⏳ Consulting the Log Pose...</p>}
              {error && <p style={{ color: "#c62828", textAlign: "center", fontWeight: "bold", backgroundColor: "#ffebee", padding: "1rem", borderRadius: "4px", border: "2px solid #c62828" }}>🚨 {error}</p>}

              {!loading && restaurants.length === 0 ? (
                <p style={{ textAlign: "center", fontSize: "1.3rem", fontStyle: "italic", color: "#3e2723" }}>No taverns found in these waters.</p>
              ) : (
                <div style={{ display: isAdmin ? "block" : "grid", gridTemplateColumns: isAdmin ? "1fr" : "repeat(auto-fill, minmax(260px, 1fr))", gap: "2rem" }}>
                  {restaurants.map((item) => (
                    <div key={item.id} style={isAdmin ? { borderBottom: "2px solid #a67b5b", padding: "1rem 0", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" } : { backgroundColor: "#fdf6e3", border: "3px solid #3e2723", boxShadow: "6px 6px 0px rgba(62,39,35,0.9)", padding: "1.5rem", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", position: "relative" }}>
                      {!isAdmin && <div style={{ position: "absolute", top: "-12px", left: "50%", transform: "translateX(-50%)", width: "24px", height: "24px", backgroundColor: "#8b0000", borderRadius: "50%", border: "3px solid #3e2723", boxShadow: "2px 3px 4px rgba(0,0,0,0.6)" }}></div>}

                      {isAdmin && canManageRestaurant(item.id) && editingId === item.id ? (
                        <div style={{ display: "flex", gap: "1rem", flex: 1, marginRight: "1rem", flexWrap: "wrap", backgroundColor: "rgba(255,255,255,0.9)", padding: "1.2rem", borderRadius: "8px", border: "2px dashed #a67b5b", boxShadow: "inset 0 0 10px rgba(0,0,0,0.05)" }}>
                          <label style={{ display: "flex", flexDirection: "column", flex: 1, color: "#3e2723", fontWeight: "bold", fontSize: "0.95rem" }}>
                            Tavern Name:
                            <input value={editFormData.name || ""} onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })} style={{ padding: "0.6rem", border: "2px solid #8b0000", borderRadius: "4px", marginTop: "0.4rem", fontFamily: "inherit", backgroundColor: "#fff", color: "#3e2723" }} />
                          </label>
                          <label style={{ display: "flex", flexDirection: "column", width: "140px", color: "#3e2723", fontWeight: "bold", fontSize: "0.95rem" }}>
                            Grub (Cuisine):
                            <input value={editFormData.cuisine || ""} onChange={(e) => setEditFormData({ ...editFormData, cuisine: e.target.value })} style={{ padding: "0.6rem", border: "2px solid #8b0000", borderRadius: "4px", marginTop: "0.4rem", fontFamily: "inherit", backgroundColor: "#fff", color: "#3e2723" }} />
                          </label>
                          <label style={{ display: "flex", flexDirection: "column", flex: 2, color: "#3e2723", fontWeight: "bold", fontSize: "0.95rem" }}>
                            Coordinates (Address):
                            <input value={editFormData.address || ""} onChange={(e) => setEditFormData({ ...editFormData, address: e.target.value })} style={{ padding: "0.6rem", border: "2px solid #8b0000", borderRadius: "4px", marginTop: "0.4rem", fontFamily: "inherit", backgroundColor: "#fff", color: "#3e2723" }} />
                          </label>
                        </div>
                      ) : (
                        <div style={isAdmin ? { flex: 1 } : { width: "100%", flex: 1, marginTop: "0.5rem" }}>
                          {isAdmin ? (
                             <>
                               <strong style={{ fontSize: "1.3rem", color: "#3e2723" }}>{item.name}</strong> <span style={{color: '#8b0000', margin: '0 0.5rem'}}>—</span> <em>{item.cuisine}</em>
                               <div style={{ color: "#444", fontSize: "1rem", marginTop: "0.4rem", fontWeight: "500" }}>{item.address}</div>
                             </>
                          ) : (
                             <>
                               <div style={{ fontSize: "0.9rem", color: "#8b0000", letterSpacing: "3px", fontWeight: "bold", marginBottom: "0.75rem", textShadow: "1px 1px 0px rgba(0,0,0,0.1)" }}>★ BOUNTY ★</div>
                               <h3 style={{ margin: "0 0 0.75rem 0", color: "#3e2723", fontSize: "1.8rem", textTransform: "uppercase", lineHeight: "1.1", wordWrap: "break-word" }}>{item.name}</h3>
                               <div style={{ backgroundColor: "#3e2723", color: "#ffd700", padding: "0.3rem 0.75rem", borderRadius: "4px", fontSize: "0.95rem", marginBottom: "1.2rem", display: "inline-block", fontWeight: "bold", border: "1px solid #ffd700" }}>{item.cuisine}</div>
                               <p style={{ margin: "0 0 1.5rem 0", color: "#444", fontSize: "1rem", fontStyle: "italic", borderTop: "1px dashed #a67b5b", paddingTop: "1rem", fontWeight: "500" }}>📍 {item.address}</p>
                             </>
                          )}
                        </div>
                      )}
                      
                      {isAdmin && canManageRestaurant(item.id) ? (
                        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                          <span style={{ color: "#3e2723", fontSize: "1.1rem", fontWeight: "bold" }}>ID: {item.id}</span>
                          {editingId === item.id ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                              <button onClick={() => handleUpdate(item.id)} style={{ backgroundColor: "#2e7d32", color: "#fff", border: "2px solid #1b5e20", padding: "0.5rem 1rem", cursor: "pointer", borderRadius: "4px", fontWeight: "bold" }}>Save Changes</button>
                              <button onClick={() => setEditingId(null)} style={{ backgroundColor: "#f5f5f5", color: "#333", border: "2px solid #ccc", padding: "0.5rem 1rem", cursor: "pointer", borderRadius: "4px", fontWeight: "bold" }}>Cancel</button>
                            </div>
                          ) : (
                            <div style={{ display: "flex", gap: "0.5rem" }}>
                              <button onClick={() => { setEditingId(item.id); setEditFormData({ name: item.name, cuisine: item.cuisine, address: item.address }); }} style={{ border: "2px solid #3e2723", padding: "0.6rem 1rem", cursor: "pointer", backgroundColor: "#fff8dc", borderRadius: "4px", fontWeight: "bold", color: "#3e2723" }}>Edit Tavern</button>
                              <button onClick={() => setSelectedRestaurantId(item.id)} style={{ border: "2px solid #3e2723", padding: "0.6rem 1rem", cursor: "pointer", backgroundColor: "#8b0000", color: "#fff", borderRadius: "4px", fontWeight: "bold" }}>Manage Menu 📜</button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <button 
                          onClick={() => setSelectedRestaurantId(item.id)} 
                          style={{ backgroundColor: "#8b0000", color: "#fff", border: "2px solid #3e2723", padding: "0.85rem", width: "100%", fontWeight: "bold", cursor: "pointer", fontSize: "1.1rem", textTransform: "uppercase", letterSpacing: "1px", fontFamily: "inherit", boxShadow: "0 4px 0px #3e2723" }} 
                          onMouseDown={(e) => e.currentTarget.style.transform = "translateY(4px)"} 
                          onMouseUp={(e) => e.currentTarget.style.transform = "translateY(0)"} 
                          onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
                        >
                          View Menu 📜
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
