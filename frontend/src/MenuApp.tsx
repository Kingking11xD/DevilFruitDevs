import { useState, useEffect, FormEvent } from 'react';

export interface MenuItem {
  id: number;
  restaurant_id: number;
  name: string;
  price: number;
  available: boolean;
  active: boolean;
}

interface MenuAppProps {
  token: string | null;
  restaurantId: number;
  isAdmin: boolean;
  onAddToCart: (menuItemId: number, quantity: number) => void;
  onBack: () => void;
}

// Reusing error formatter from CartApp to handle FastAPI validation arrays
function formatErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = Array.isArray((item as { loc?: unknown[] }).loc)
            ? (item as { loc: unknown[] }).loc.filter((part) => part !== 'body').join('.')
            : '';
          const msg = String((item as { msg: unknown }).msg);
          return loc ? `${loc}: ${msg}` : msg;
        }
        return JSON.stringify(item);
      })
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join('; ');
    }
  }
  return fallback;
}

async function parseErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    return formatErrorDetail(data?.detail, fallback);
  } catch {
    return fallback;
  }
}

export default function MenuApp({ token, restaurantId, isAdmin, onAddToCart, onBack }: MenuAppProps) {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    price: 0,
    available: true,
    active: true
  });

  useEffect(() => {
    fetchMenu();
  }, [restaurantId]);

  const fetchMenu = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/restaurants/${restaurantId}/menu-items`);
      if (res.ok) {
        const data = await res.json();
        setMenuItems(data);
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to fetch the tavern menu.');
      }
    } catch (err) {
      setError('Network error checking the menu.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveItem = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    
    try {
      const url = editingId 
        ? `/restaurants/${restaurantId}/menu-items/${editingId}`
        : `/restaurants/${restaurantId}/menu-items`;
        
      // Ensure we only send the fields the backend expects
      const payload = editingId 
        ? { 
            name: formData.name, 
            price: formData.price, 
            available: formData.available, 
            active: formData.active 
          }
        : { 
            name: formData.name, 
            price: formData.price, 
            available: formData.available 
          };
          
      const res = await fetch(url, {
        method: editingId ? 'PATCH' : 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        fetchMenu();
        setEditingId(null);
        setFormData({ name: '', price: 0, available: true, active: true });
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to save menu item.');
        alert(errMsg);
      }
    } catch (err) {
      alert('Network error saving menu item.');
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <button 
          onClick={onBack}
          style={{ backgroundColor: '#eaddcf', border: '2px solid #a67b5b', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontFamily: 'inherit' }}
        >
          ⬅ Back to Sea
        </button>
        <h2 style={{ color: '#8b0000', margin: 0, textTransform: 'uppercase' }}>📜 Tavern Menu</h2>
      </div>

      {error && (
        <div style={{ backgroundColor: '#ffebee', color: '#c62828', padding: '1rem', border: '2px solid #c62828', borderRadius: '6px', marginBottom: '1.5rem', fontWeight: 'bold', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* Admin Panel: Add/Edit Menu Item */}
      {isAdmin && (
        <div style={{ backgroundColor: '#fff8dc', padding: '1.5rem', borderRadius: '8px', border: '3px dashed #8b0000', marginBottom: '2rem' }}>
          <h3 style={{ marginTop: 0, color: '#8b0000' }}>{editingId ? 'Edit Grub' : 'Add New Grub'}</h3>
          <form onSubmit={handleSaveItem} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <input 
                placeholder="Item Name" 
                value={formData.name} 
                onChange={e => setFormData({...formData, name: e.target.value})} 
                required 
                style={{ padding: '0.75rem', flex: 2, border: '2px solid #8b0000', borderRadius: '4px', fontFamily: 'inherit', color: '#3e2723' }} 
              />
              <input 
                type="number" 
                step="1" 
                min="0"
                placeholder="Price (Berries)" 
                value={formData.price === 0 ? '' : formData.price} 
                onChange={e => setFormData({...formData, price: parseInt(e.target.value, 10) || 0})} 
                required 
                style={{ padding: '0.75rem', flex: 1, border: '2px solid #8b0000', borderRadius: '4px', fontFamily: 'inherit', color: '#3e2723' }} 
              />
            </div>
            
            {editingId && (
              <div style={{ display: 'flex', gap: '2rem', margin: '0.5rem 0' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 'bold', color: '#3e2723' }}>
                  <input type="checkbox" checked={formData.available} onChange={e => setFormData({...formData, available: e.target.checked})} />
                  Available to Order
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontWeight: 'bold', color: '#3e2723' }}>
                  <input type="checkbox" checked={formData.active} onChange={e => setFormData({...formData, active: e.target.checked})} />
                  Active Item
                </label>
              </div>
            )}
            
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="submit" style={{ backgroundColor: '#3e2723', color: '#ffd700', padding: '0.75rem 1.5rem', border: '2px solid #8b0000', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
                {editingId ? 'Save Changes' : 'Add to Menu'}
              </button>
              {editingId && (
                <button type="button" onClick={() => { setEditingId(null); setFormData({ name: '', price: 0, available: true, active: true }); }} style={{ padding: '0.75rem 1.5rem', border: '2px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {loading && <p style={{ textAlign: 'center', fontWeight: 'bold', color: '#3e2723' }}>⏳ Reading the scroll...</p>}

      {!loading && menuItems.length === 0 && (
        <p style={{ textAlign: 'center', fontStyle: 'italic', fontSize: '1.2rem', color: '#3e2723' }}>This tavern has no grub available.</p>
      )}

      {/* Menu List */}
      {!loading && menuItems.length > 0 && (
        <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {menuItems.map(item => (
            <div key={item.id} style={{ 
              backgroundColor: '#fdf6e3', 
              border: '3px solid #3e2723', 
              padding: '1.5rem', 
              boxShadow: '4px 4px 0px rgba(62,39,35,0.8)',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              opacity: (!item.available || !item.active) && !isAdmin ? 0.6 : 1
            }}>
              
              {/* Status Badges for Admin */}
              {isAdmin && (
                <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', gap: '0.5rem' }}>
                  {!item.available && <span style={{ backgroundColor: '#f57c00', color: '#fff', padding: '0.2rem 0.5rem', fontSize: '0.7rem', borderRadius: '4px', fontWeight: 'bold' }}>SOLD OUT</span>}
                  {!item.active && <span style={{ backgroundColor: '#c62828', color: '#fff', padding: '0.2rem 0.5rem', fontSize: '0.7rem', borderRadius: '4px', fontWeight: 'bold' }}>INACTIVE</span>}
                </div>
              )}

              <h3 style={{ margin: '0 0 0.5rem 0', color: '#8b0000', fontSize: '1.4rem' }}>{item.name}</h3>
              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#3e2723', marginBottom: '1.5rem' }}>{item.price} Berries</div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
                {isAdmin ? (
                  <button 
                    onClick={() => {
                      setEditingId(item.id);
                      setFormData({ name: item.name, price: item.price, available: item.available, active: item.active });
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                    style={{ flex: 1, padding: '0.5rem', backgroundColor: '#eaddcf', border: '2px solid #3e2723', fontWeight: 'bold', color: '#3e2723', cursor: 'pointer' }}
                  >
                    Edit Grub
                  </button>
                ) : (
                  <button 
                    disabled={!item.available || !item.active || !token}
                    onClick={() => onAddToCart(item.id, 1)}
                    style={{ 
                      flex: 1, 
                      padding: '0.75rem', 
                      backgroundColor: (!item.available || !item.active || !token) ? '#ccc' : '#8b0000', 
                      color: (!item.available || !item.active || !token) ? '#666' : '#fff', 
                      border: '2px solid #3e2723', 
                      fontWeight: 'bold', 
                      cursor: (!item.available || !item.active || !token) ? 'not-allowed' : 'pointer',
                      fontFamily: 'inherit',
                      textTransform: 'uppercase'
                    }}
                  >
                    {!token ? 'Sign In to Order' : (!item.available || !item.active) ? 'Unavailable' : '+ Add to Haul'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}