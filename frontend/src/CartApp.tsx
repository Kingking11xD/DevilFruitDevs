import { useState, useEffect, FormEvent } from 'react';

export interface CartItemDetail {
  menu_item_id: number;
  name?: string; 
  price?: number;
  quantity: number;
  line_total?: number;
  problems?: string[];
}

export interface CartDetail {
  id: string;
  customer_id: string;
  restaurant_id: number | null;
  items: Record<string, CartItemDetail> | CartItemDetail[]; // Handling both array or dict formats depending on backend schema
  subtotal: number;
  total: number;
}

interface CartAppProps {
  token: string | null;
}

export default function CartApp({ token }: CartAppProps) {
  const [cart, setCart] = useState<CartDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success', text: string } | null>(null);

  // Quick Add State (For testing until the Menu page is built)
  const [addMenuId, setAddMenuId] = useState('');
  const [addQty, setAddQty] = useState('1');

  useEffect(() => {
    if (token) {
      fetchCart();
    }
  }, [token]);

  const fetchCart = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch('/customers/me/cart', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCart(data);
      } else if (res.status === 404) {
        // Active cart not found [cite: 25]
        setCart(null);
      } else {
        const errData = await res.json();
        setMessage({ type: 'error', text: errData.detail || 'Failed to load cargo.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error checking the hold.' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (menuItemId: number, newQuantity: number) => {
    if (newQuantity < 1) return;
    try {
      const res = await fetch(`/customers/me/cart/items/${menuItemId}`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ quantity: newQuantity })
      });
      
      if (res.ok) {
        const data = await res.json();
        setCart(data);
      } else {
        const errData = await res.json();
        setMessage({ type: 'error', text: errData.detail || 'Failed to adjust rations.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error adjusting rations.' });
    }
  };

  const handleRemoveItem = async (menuItemId: number) => {
    if (!window.confirm('Throw these rations overboard?')) return;
    try {
      const res = await fetch(`/customers/me/cart/items/${menuItemId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        fetchCart(); // Refetch to get updated totals [cite: 25]
      } else {
        const errData = await res.json();
        setMessage({ type: 'error', text: errData.detail || 'Failed to throw overboard.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error removing item.' });
    }
  };

  const handleQuickAdd = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch('/customers/me/cart/items', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ 
          menu_item_id: parseInt(addMenuId), 
          quantity: parseInt(addQty) 
        })
      });
      
      if (res.ok) {
        setMessage({ type: 'success', text: 'Booty added to hold!' });
        fetchCart(); // Refresh cart to show new totals
      } else {
        const errData = await res.json();
        setMessage({ type: 'error', text: errData.detail || 'Failed to add booty.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error adding to cart.' });
    }
  };

  if (!token) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#3e2723' }}>
        <h3>You must sign the Articles (Log In) to view your cargo!</h3>
      </div>
    );
  }

  // Normalize items array (Backend might return a dict or an array)
  const cartItems: CartItemDetail[] = cart?.items 
    ? (Array.isArray(cart.items) ? cart.items : Object.values(cart.items))
    : [];

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
      
      {message && (
        <div style={{ 
          backgroundColor: message.type === 'error' ? '#ffebee' : '#e8f5e9', 
          color: message.type === 'error' ? '#c62828' : '#2e7d32', 
          padding: '1rem', 
          border: `2px solid ${message.type === 'error' ? '#c62828' : '#2e7d32'}`,
          borderRadius: '6px',
          marginBottom: '1.5rem',
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          {message.text}
        </div>
      )}

      {/* QUICK ADD TOOL (Temporary until Menu UI is built) */}
      <div style={{ backgroundColor: 'rgba(255,255,255,0.4)', padding: '1rem', borderRadius: '8px', border: '2px dashed #a67b5b', marginBottom: '2rem' }}>
        <h4 style={{ margin: '0 0 1rem 0', color: '#3e2723', textTransform: 'uppercase' }}>🔭 Quick Plunder (Add by ID)</h4>
        <form onSubmit={handleQuickAdd} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input 
            type="number" 
            placeholder="Menu Item ID" 
            value={addMenuId} 
            onChange={(e) => setAddMenuId(e.target.value)} 
            required 
            style={{ padding: '0.5rem', border: '2px solid #8b0000', borderRadius: '4px', flex: 1, minWidth: '120px' }}
          />
          <input 
            type="number" 
            min="1" 
            value={addQty} 
            onChange={(e) => setAddQty(e.target.value)} 
            required 
            style={{ padding: '0.5rem', border: '2px solid #8b0000', borderRadius: '4px', width: '80px' }}
          />
          <button type="submit" style={{ backgroundColor: '#3e2723', color: '#ffd700', padding: '0.5rem 1rem', border: '2px solid #8b0000', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer' }}>
            Haul Aboard
          </button>
        </form>
      </div>

      {loading && <p style={{ textAlign: 'center', fontWeight: 'bold' }}>⏳ Inspecting the hold...</p>}

      {!loading && cartItems.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', border: '3px solid #3e2723', backgroundColor: '#fdf6e3', borderRadius: '8px' }}>
          <h2 style={{ color: '#8b0000', margin: 0, letterSpacing: '2px' }}>YOUR HOLD IS EMPTY</h2>
          <p style={{ color: '#555', fontStyle: 'italic', marginTop: '0.5rem' }}>Chart a course to a tavern and start plundering!</p>
        </div>
      )}

      {!loading && cartItems.length > 0 && (
        <div style={{ border: '4px solid #3e2723', backgroundColor: '#fdf6e3', padding: '1.5rem', borderRadius: '8px', boxShadow: '5px 5px 0px rgba(0,0,0,0.3)' }}>
          <h2 style={{ margin: '0 0 1.5rem 0', color: '#3e2723', borderBottom: '2px dashed #a67b5b', paddingBottom: '0.5rem', textTransform: 'uppercase' }}>
            📦 Ship's Cargo
          </h2>
          
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {cartItems.map((item) => (
              <li key={item.menu_item_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 0', borderBottom: '1px solid #eaddcf' }}>
                <div style={{ flex: 1 }}>
                  <h4 style={{ margin: '0 0 0.25rem 0', color: '#8b0000', fontSize: '1.2rem' }}>
                    {item.name || `Mysterious Ration #${item.menu_item_id}`}
                  </h4>
                  <div style={{ fontSize: '0.9rem', color: '#555' }}>
                    Unit Price: ${(item.price || 0).toFixed(2)}
                  </div>
                  {item.problems && item.problems.length > 0 && (
                    <div style={{ color: '#c62828', fontSize: '0.85rem', marginTop: '0.25rem', fontWeight: 'bold' }}>
                      ⚠️ {item.problems.join(', ')}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', border: '2px solid #3e2723', borderRadius: '4px', backgroundColor: '#fff', overflow: 'hidden' }}>
                    <button 
                      onClick={() => handleUpdateQuantity(item.menu_item_id, item.quantity - 1)}
                      style={{ border: 'none', backgroundColor: '#eaddcf', padding: '0.5rem 0.75rem', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem' }}
                    >-</button>
                    <span style={{ padding: '0 1rem', fontWeight: 'bold' }}>{item.quantity}</span>
                    <button 
                      onClick={() => handleUpdateQuantity(item.menu_item_id, item.quantity + 1)}
                      style={{ border: 'none', backgroundColor: '#eaddcf', padding: '0.5rem 0.75rem', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem' }}
                    >+</button>
                  </div>
                  
                  <div style={{ fontWeight: 'bold', color: '#3e2723', minWidth: '80px', textAlign: 'right' }}>
                    ${(item.line_total || 0).toFixed(2)}
                  </div>

                  <button 
                    onClick={() => handleRemoveItem(item.menu_item_id)}
                    style={{ backgroundColor: '#c62828', color: '#fff', border: '2px solid #8b0000', borderRadius: '4px', padding: '0.5rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                    title="Throw Overboard"
                  >
                    🗑️
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#eaddcf', border: '2px solid #a67b5b', borderRadius: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#555', fontWeight: 'bold' }}>
              <span>Subtotal:</span>
              <span>${(cart?.subtotal || 0).toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.5rem', color: '#8b0000', fontWeight: 'bold', borderTop: '2px dashed #a67b5b', paddingTop: '1rem', marginTop: '0.5rem' }}>
              <span>Total Booty:</span>
              <span>${(cart?.total || 0).toFixed(2)}</span>
            </div>
            <button style={{ width: '100%', padding: '1rem', backgroundColor: '#8b0000', color: '#ffd700', border: '3px solid #3e2723', borderRadius: '6px', fontWeight: 'bold', fontSize: '1.2rem', textTransform: 'uppercase', letterSpacing: '2px', cursor: 'pointer', marginTop: '1.5rem', boxShadow: '0 4px 0px #3e2723' }}>
              Set Sail to Checkout ⚓
            </button>
          </div>
        </div>
      )}
    </div>
  );
}