import { useState, useEffect, FormEvent } from 'react';

export interface CartItemDetail {
  menu_item_id: number;
  name?: string;
  unit_price?: number;
  quantity: number;
  line_total?: number;
  problems?: string[];
}

export interface CartDetail {
  id: string;
  customer_id: string;
  restaurant_id: number | null;
  items: Record<string, CartItemDetail> | CartItemDetail[];
  subtotal: number;
  total: number;
}

interface RestaurantOption {
  id: number;
  name: string;
  cuisine?: string;
}

interface MenuItemOption {
  id: number;
  restaurant_id: number;
  name: string;
  price: number;
  available: boolean;
  active: boolean;
}

interface CartAppProps {
  token: string | null;
  onCheckoutSuccess?: () => void;
}

// Helper to convert FastAPI string or array validation errors into readable text
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

export default function CartApp({ token, onCheckoutSuccess }: CartAppProps) {
  const [cart, setCart] = useState<CartDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  // Quick Plunder state (supports selecting by restaurant + menu item OR manual ID entry)
  const [quickMode, setQuickMode] = useState<'picker' | 'manual'>('picker');
  const [restaurants, setRestaurants] = useState<RestaurantOption[]>([]);
  const [loadingRestaurants, setLoadingRestaurants] = useState(false);
  const [selectedRestaurantId, setSelectedRestaurantId] = useState('');
  const [menuItems, setMenuItems] = useState<MenuItemOption[]>([]);
  const [loadingMenuItems, setLoadingMenuItems] = useState(false);

  const [manualRestaurantId, setManualRestaurantId] = useState('');
  const [addMenuId, setAddMenuId] = useState('');
  const [addQty, setAddQty] = useState('1');

  useEffect(() => {
    if (token) {
      fetchCart();
      fetchRestaurantsList();
    }
  }, [token]);

  // Pre-select the cart's current restaurant if one is active and nothing is chosen yet
  useEffect(() => {
    if (cart?.restaurant_id && !selectedRestaurantId) {
      setSelectedRestaurantId(String(cart.restaurant_id));
    }
  }, [cart?.restaurant_id, selectedRestaurantId]);

  // Load menu items whenever a restaurant is selected in picker mode
  useEffect(() => {
    if (!token || !selectedRestaurantId) {
      setMenuItems([]);
      return;
    }

    let isCurrent = true;
    const loadMenu = async () => {
      setLoadingMenuItems(true);
      try {
        const res = await fetch(`/restaurants/${selectedRestaurantId}/menu-items`);
        if (!isCurrent) return;
        if (res.ok) {
          const data: MenuItemOption[] = await res.json();
          setMenuItems(data);
        } else {
          setMenuItems([]);
        }
      } catch {
        if (isCurrent) setMenuItems([]);
      } finally {
        if (isCurrent) setLoadingMenuItems(false);
      }
    };

    loadMenu();
    return () => {
      isCurrent = false;
    };
  }, [token, selectedRestaurantId]);

  const fetchRestaurantsList = async () => {
    setLoadingRestaurants(true);
    try {
      const res = await fetch('/restaurants');
      if (res.ok) {
        const data: RestaurantOption[] = await res.json();
        setRestaurants(data);
      }
    } catch {
      // Keep list empty if restaurants fail to load; manual ID mode still works
    } finally {
      setLoadingRestaurants(false);
    }
  };

  const fetchCart = async (clearMessage = true) => {
    setLoading(true);
    if (clearMessage) setMessage(null);
    try {
      const res = await fetch('/customers/me/cart', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCart(data);
      } else if (res.status === 404) {
        setCart(null);
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to load cargo.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
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
        const errMsg = await parseErrorMessage(res, 'Failed to adjust rations.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
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
        fetchCart();
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to throw overboard.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error removing item.' });
    }
  };

  const handleClearCart = async () => {
    if (!window.confirm('Are you sure you want to empty the entire hold? This will dump all cargo overboard!')) return;
    try {
      const res = await fetch('/customers/me/cart/items', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        setCart(null);
        setMessage({ type: 'success', text: 'Hold emptied. Ready for new plunder!' });
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to empty the hold.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error emptying cart.' });
    }
  };

  const handleQuickAdd = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);

    const parsedMenuId = parseInt(addMenuId, 10);
    const parsedQty = parseInt(addQty, 10);

    if (Number.isNaN(parsedMenuId) || parsedMenuId <= 0) {
      setMessage({ type: 'error', text: 'Please pick or enter a valid Menu Item ID.' });
      return;
    }

    if (Number.isNaN(parsedQty) || parsedQty < 1) {
      setMessage({ type: 'error', text: 'Quantity must be at least 1.' });
      return;
    }

    // In manual mode, if a Restaurant ID was provided, verify the item belongs to that restaurant first
    if (quickMode === 'manual' && manualRestaurantId.trim() !== '') {
      const parsedRestaurantId = parseInt(manualRestaurantId, 10);
      if (Number.isNaN(parsedRestaurantId) || parsedRestaurantId <= 0) {
        setMessage({ type: 'error', text: 'Please enter a valid Restaurant ID.' });
        return;
      }

      try {
        const verifyRes = await fetch(`/restaurants/${parsedRestaurantId}/menu-items/${parsedMenuId}`);
        if (!verifyRes.ok) {
          const errMsg = await parseErrorMessage(
            verifyRes,
            `Menu item #${parsedMenuId} was not found at Restaurant #${parsedRestaurantId}.`
          );
          setMessage({ type: 'error', text: errMsg });
          return;
        }
      } catch {
        setMessage({ type: 'error', text: 'Network error verifying restaurant and menu item.' });
        return;
      }
    }

    if (!cart) {
      try {
        const createRes = await fetch('/customers/me/cart', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!createRes.ok) {
          const errMsg = await parseErrorMessage(createRes, 'Failed to create an active cart.');
          setMessage({ type: 'error', text: errMsg });
          return;
        }
      } catch {
        setMessage({ type: 'error', text: 'Failed to manifest a new cart.' });
        return;
      }
    }

    try {
      const res = await fetch('/customers/me/cart/items', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          menu_item_id: parsedMenuId,
          quantity: parsedQty
        })
      });

      if (res.ok) {
        setMessage({ type: 'success', text: 'Booty added to hold!' });
        fetchCart(false);
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to add booty.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error adding to cart.' });
    }
  };

  const handleCheckout = async () => {
    if (!cart) return;
    setMessage(null);
    try {
      const res = await fetch(`/carts/${cart.id}/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ expected_total: cart.total })
      });

      if (res.ok) {
        setCart(null);
        if (onCheckoutSuccess) {
          onCheckoutSuccess();
        } else {
          setMessage({ type: 'success', text: 'Order dispatched successfully! The snails are on their way.' });
        }
      } else {
        const errData = await res.json();
        let errMsg = formatErrorDetail(errData.detail, 'Failed to checkout.');

        // Handle specific 409 TotalChangedError dictionary object
        if (typeof errData.detail === 'object' && errData.detail?.message) {
          errMsg = `${errData.detail.message}. New total: ${errData.detail.total} Berries`;
          fetchCart(false); // Refresh cart to show the new prices
        } else if (res.status === 409) {
          fetchCart(false); // Refresh cart for unavailable items
        }

        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error during checkout.' });
    }
  };

  if (!token) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#3e2723' }}>
        <h3>You must sign the Articles (Log In) to view your cargo!</h3>
      </div>
    );
  }

  const cartItems: CartItemDetail[] = cart?.items
    ? Array.isArray(cart.items)
      ? cart.items
      : Object.values(cart.items)
    : [];

  const fieldStyle = {
    padding: '0.6rem 0.75rem',
    border: '2px solid #8b0000',
    borderRadius: '4px',
    backgroundColor: '#ffffff',
    color: '#3e2723',
    fontWeight: 600,
    fontFamily: 'inherit',
    fontSize: '0.95rem',
    width: '100%',
    boxSizing: 'border-box' as const,
  };

  const labelStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.35rem',
    color: '#3e2723',
    fontWeight: 'bold' as const,
    fontSize: '0.9rem',
  };

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto' }}>
      {message && (
        <div
          style={{
            backgroundColor: message.type === 'error' ? '#ffebee' : '#e8f5e9',
            color: message.type === 'error' ? '#c62828' : '#2e7d32',
            padding: '1rem',
            border: `2px solid ${message.type === 'error' ? '#c62828' : '#2e7d32'}`,
            borderRadius: '6px',
            marginBottom: '1.5rem',
            fontWeight: 'bold',
            textAlign: 'center'
          }}
        >
          {message.text}
        </div>
      )}

      {/* QUICK PLUNDER TOOL */}
      <div
        style={{
          backgroundColor: '#fdf6e3',
          padding: '1.25rem',
          borderRadius: '8px',
          border: '3px solid #3e2723',
          boxShadow: '4px 4px 0px rgba(62,39,35,0.6)',
          marginBottom: '2rem'
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '0.75rem',
            borderBottom: '2px dashed #a67b5b',
            paddingBottom: '0.75rem',
            marginBottom: '1rem'
          }}
        >
          <h4 style={{ margin: 0, color: '#8b0000', textTransform: 'uppercase', fontSize: '1.15rem' }}>
            🔭 Quick Plunder
          </h4>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => {
                setQuickMode('picker');
                setAddMenuId('');
              }}
              style={{
                padding: '0.4rem 0.75rem',
                borderRadius: '4px',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                cursor: 'pointer',
                fontFamily: 'inherit',
                backgroundColor: quickMode === 'picker' ? '#8b0000' : '#eaddcf',
                color: quickMode === 'picker' ? '#ffd700' : '#3e2723',
                border: quickMode === 'picker' ? '2px solid #3e2723' : '2px solid #a67b5b'
              }}
            >
              Pick Tavern &amp; Item
            </button>
            <button
              type="button"
              onClick={() => {
                setQuickMode('manual');
                if (selectedRestaurantId && !manualRestaurantId) {
                  setManualRestaurantId(selectedRestaurantId);
                }
              }}
              style={{
                padding: '0.4rem 0.75rem',
                borderRadius: '4px',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                cursor: 'pointer',
                fontFamily: 'inherit',
                backgroundColor: quickMode === 'manual' ? '#8b0000' : '#eaddcf',
                color: quickMode === 'manual' ? '#ffd700' : '#3e2723',
                border: quickMode === 'manual' ? '2px solid #3e2723' : '2px solid #a67b5b'
              }}
            >
              Enter IDs Manually
            </button>
          </div>
        </div>

        {cart?.restaurant_id && (
          <p style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: '#3e2723', fontWeight: 600 }}>
            ⚓ Active cargo belongs to <strong>Tavern #{cart.restaurant_id}</strong> (all items in one hold must come from the same tavern).
          </p>
        )}

        <form onSubmit={handleQuickAdd} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          {quickMode === 'picker' ? (
            <>
              <label style={{ ...labelStyle, flex: '1 1 200px' }}>
                Restaurant (ID)
                <select
                  value={selectedRestaurantId}
                  onChange={(e) => {
                    setSelectedRestaurantId(e.target.value);
                    setAddMenuId('');
                  }}
                  required
                  style={fieldStyle}
                >
                  <option value="">
                    {loadingRestaurants ? 'Loading taverns...' : '-- Select Restaurant --'}
                  </option>
                  {restaurants.map((r) => (
                    <option key={r.id} value={r.id}>
                      #{r.id} — {r.name}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ ...labelStyle, flex: '1 1 220px' }}>
                Menu Item (ID)
                <select
                  value={addMenuId}
                  onChange={(e) => setAddMenuId(e.target.value)}
                  required
                  disabled={!selectedRestaurantId || loadingMenuItems}
                  style={{
                    ...fieldStyle,
                    backgroundColor: !selectedRestaurantId || loadingMenuItems ? '#eaddcf' : '#ffffff',
                    cursor: !selectedRestaurantId || loadingMenuItems ? 'not-allowed' : 'pointer'
                  }}
                >
                  <option value="">
                    {!selectedRestaurantId
                      ? '-- Pick a Restaurant First --'
                      : loadingMenuItems
                        ? 'Loading menu...'
                        : menuItems.length === 0
                          ? 'No items on this menu'
                          : '-- Select Menu Item --'}
                  </option>
                  {menuItems.map((item) => {
                    const unavailable = !item.available || !item.active;
                    return (
                      <option key={item.id} value={item.id} disabled={unavailable}>
                        #{item.id} — {item.name} ({item.price} Berries){unavailable ? ' [Unavailable]' : ''}
                      </option>
                    );
                  })}
                </select>
              </label>
            </>
          ) : (
            <>
              <label style={{ ...labelStyle, flex: '1 1 150px' }}>
                Restaurant ID
                <input
                  type="number"
                  min="1"
                  placeholder="Ex: 1"
                  value={manualRestaurantId}
                  onChange={(e) => setManualRestaurantId(e.target.value)}
                  required
                  style={fieldStyle}
                />
              </label>

              <label style={{ ...labelStyle, flex: '1 1 150px' }}>
                Menu Item ID
                <input
                  type="number"
                  min="1"
                  placeholder="Ex: 1"
                  value={addMenuId}
                  onChange={(e) => setAddMenuId(e.target.value)}
                  required
                  style={fieldStyle}
                />
              </label>
            </>
          )}

          <label style={{ ...labelStyle, width: '90px' }}>
            Qty
            <input
              type="number"
              min="1"
              value={addQty}
              onChange={(e) => setAddQty(e.target.value)}
              required
              style={fieldStyle}
            />
          </label>

          <button
            type="submit"
            style={{
              backgroundColor: '#3e2723',
              color: '#ffd700',
              padding: '0.65rem 1.25rem',
              border: '2px solid #8b0000',
              borderRadius: '4px',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: '0.95rem',
              whiteSpace: 'nowrap'
            }}
          >
            Haul Aboard
          </button>
        </form>
      </div>

      {loading && <p style={{ textAlign: 'center', fontWeight: 'bold', color: '#3e2723' }}>⏳ Inspecting the hold...</p>}

      {!loading && cartItems.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', border: '3px solid #3e2723', backgroundColor: '#fdf6e3', borderRadius: '8px' }}>
          <h2 style={{ color: '#8b0000', margin: 0, letterSpacing: '2px' }}>YOUR HOLD IS EMPTY</h2>
          <p style={{ color: '#555', fontStyle: 'italic', marginTop: '0.5rem' }}>Chart a course to a tavern and start plundering!</p>
        </div>
      )}

      {!loading && cartItems.length > 0 && (
        <div style={{ border: '4px solid #3e2723', backgroundColor: '#fdf6e3', padding: '1.5rem', borderRadius: '8px', boxShadow: '5px 5px 0px rgba(0,0,0,0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px dashed #a67b5b', paddingBottom: '0.5rem', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0, color: '#3e2723', textTransform: 'uppercase' }}>
              📦 Ship's Cargo
            </h2>
            <button
              onClick={handleClearCart}
              style={{ backgroundColor: '#fff', color: '#c62828', border: '2px solid #c62828', padding: '0.4rem 0.75rem', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.9rem' }}
            >
              Dump All Cargo 🗑️
            </button>
          </div>

          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {cartItems.map((item) => (
              <li key={item.menu_item_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 0', borderBottom: '1px solid #eaddcf', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ flex: '1 1 200px' }}>
                  <h4 style={{ margin: '0 0 0.25rem 0', color: '#8b0000', fontSize: '1.2rem' }}>
                    {item.name || `Mysterious Ration #${item.menu_item_id}`}
                  </h4>
                  <div style={{ fontSize: '0.9rem', color: '#555' }}>
                    Unit Price: {item.unit_price || 0} Berries
                  </div>
                  {item.problems && item.problems.length > 0 && (
                    <div style={{ color: '#c62828', fontSize: '0.85rem', marginTop: '0.25rem', fontWeight: 'bold' }}>
                      ⚠️ {item.problems.join(', ')}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', border: '2px solid #3e2723', borderRadius: '4px', backgroundColor: '#d4a931', overflow: 'hidden' }}>
                    <button
                      onClick={() => handleUpdateQuantity(item.menu_item_id, item.quantity - 1)}
                      style={{ border: 'none', backgroundColor: '#eaddcf', color: '#3e2723', padding: '0.5rem 0.75rem', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem' }}
                    >
                      -
                    </button>
                    <span style={{ padding: '0 1rem', fontWeight: 'bold', color: '#3e2723' }}>{item.quantity}</span>
                    <button
                      onClick={() => handleUpdateQuantity(item.menu_item_id, item.quantity + 1)}
                      style={{ border: 'none', backgroundColor: '#eaddcf', color: '#3e2723', padding: '0.5rem 0.75rem', cursor: 'pointer', fontWeight: 'bold', fontSize: '1.1rem' }}
                    >
                      +
                    </button>
                  </div>

                  <div style={{ fontWeight: 'bold', color: '#3e2723', minWidth: '80px', textAlign: 'right', fontSize: '1.1rem' }}>
                    {item.line_total || 0} Berries
                  </div>

                  <button
                    onClick={() => handleRemoveItem(item.menu_item_id)}
                    style={{ backgroundColor: '#c62828', color: '#fff', border: '2px solid #8b0000', borderRadius: '4px', padding: '0.5rem 0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem' }}
                    title="Throw Overboard"
                  >
                    X
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#eaddcf', border: '2px solid #a67b5b', borderRadius: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', color: '#555', fontWeight: 'bold', fontSize: '1.1rem' }}>
              <span>Subtotal:</span>
              <span>{cart?.subtotal || 0} Berries</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.6rem', color: '#8b0000', fontWeight: 'bold', borderTop: '2px dashed #a67b5b', paddingTop: '1rem', marginTop: '0.5rem' }}>
              <span>Total Booty:</span>
              <span>{cart?.total || 0} Berries</span>
            </div>
            <button
              onClick={handleCheckout}
              style={{ width: '100%', padding: '1rem', backgroundColor: '#8b0000', color: '#ffd700', border: '3px solid #3e2723', borderRadius: '6px', fontWeight: 'bold', fontSize: '1.2rem', textTransform: 'uppercase', letterSpacing: '2px', cursor: 'pointer', marginTop: '1.5rem', boxShadow: '0 4px 0px #3e2723' }}
            >
              Set Sail to Checkout ⚓
            </button>
          </div>
        </div>
      )}
    </div>
  );
}