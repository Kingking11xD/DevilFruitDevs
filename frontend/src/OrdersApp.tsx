import { useState, useEffect } from 'react';

export interface OrderItem {
  menu_item_id: number;
  name: string;
  price: number;
  quantity: number;
  line_total: number;
}

export interface Order {
  id: number;
  customer_id: string;
  restaurant_id: number;
  status: string;
  items: Record<string, OrderItem> | OrderItem[];
  subtotal: number;
  total: number;
  delivery_address: string;
  created_at: string;
}

interface OrdersAppProps {
  token: string | null;
}

export default function OrdersApp({ token }: OrdersAppProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Status mapping for Pirate theme
  const getStatusDisplay = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return { label: 'Awaiting Snail', color: '#f57c00' };
      case 'preparing': return { label: 'Cooking in Galley', color: '#1976d2' };
      case 'delivering': return { label: 'Snail on Route', color: '#9c27b0' };
      case 'completed': return { label: 'Booty Delivered', color: '#2e7d32' };
      case 'cancelled': return { label: 'Scuttled', color: '#c62828' };
      default: return { label: status, color: '#555' };
    }
  };

  useEffect(() => {
    if (token) {
      fetchOrders();
    }
  }, [token]);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/orders', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setOrders(data);
      } else {
        const errData = await res.json();
        setError(errData.detail || 'Failed to fetch the ship logs.');
      }
    } catch (err) {
      setError('Network error checking the logs.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#3e2723' }}>
        <h3>You must sign the Articles (Log In) to view your past plunders!</h3>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      
      {error && (
        <div style={{ backgroundColor: '#ffebee', color: '#c62828', padding: '1rem', border: '2px solid #c62828', borderRadius: '6px', marginBottom: '1.5rem', fontWeight: 'bold', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {loading && <p style={{ textAlign: 'center', fontWeight: 'bold' }}>⏳ Reading the ship's log...</p>}

      {!loading && orders.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', border: '3px solid #3e2723', backgroundColor: '#fdf6e3', borderRadius: '8px' }}>
          <h2 style={{ color: '#8b0000', margin: 0, letterSpacing: '2px' }}>NO PAST PLUNDERS</h2>
          <p style={{ color: '#555', fontStyle: 'italic', marginTop: '0.5rem' }}>You haven't ordered any grub yet!</p>
        </div>
      )}

      {!loading && orders.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {orders.map(order => {
            const statusInfo = getStatusDisplay(order.status);
            const itemsList = Array.isArray(order.items) ? order.items : Object.values(order.items);
            
            return (
              <div key={order.id} style={{ 
                backgroundColor: '#fdf6e3', 
                border: '4px solid #3e2723', 
                borderRadius: '8px', 
                boxShadow: '6px 6px 0px rgba(62,39,35,0.8)',
                overflow: 'hidden'
              }}>
                {/* Header */}
                <div style={{ backgroundColor: '#eaddcf', padding: '1rem 1.5rem', borderBottom: '2px dashed #a67b5b', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <h3 style={{ margin: 0, color: '#8b0000', textTransform: 'uppercase' }}>Log #{order.id}</h3>
                    <div style={{ fontSize: '0.9rem', color: '#555', marginTop: '0.25rem' }}>
                      {new Date(order.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ backgroundColor: statusInfo.color, color: '#fff', padding: '0.4rem 1rem', borderRadius: '20px', fontWeight: 'bold', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    {statusInfo.label}
                  </div>
                </div>

                {/* Items */}
                <div style={{ padding: '1.5rem' }}>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                    {itemsList.map(item => (
                      <li key={item.menu_item_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid rgba(166, 123, 91, 0.3)' }}>
                        <div>
                          <span style={{ fontWeight: 'bold', color: '#3e2723', marginRight: '0.5rem' }}>{item.quantity}x</span>
                          <span style={{ color: '#8b0000' }}>{item.name}</span>
                        </div>
                        <div style={{ color: '#555' }}>${(item.line_total || (item.price * item.quantity)).toFixed(2)}</div>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Footer Totals */}
                <div style={{ backgroundColor: 'rgba(255,255,255,0.4)', padding: '1rem 1.5rem', borderTop: '2px solid #a67b5b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ color: '#555', fontStyle: 'italic', fontSize: '0.95rem' }}>
                    📍 Delivered to: {order.delivery_address}
                  </div>
                  <div style={{ fontSize: '1.4rem', color: '#8b0000', fontWeight: 'bold' }}>
                    Total: ${order.total.toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}