import { useState, useEffect, FormEvent } from 'react';

interface Account {
  id: string;
  name: string;
  email: string;
  delivery_address?: string | null;
  is_active: boolean;
}

export interface CustomerAppProps {
  token?: string | null;
  setToken?: (token: string | null) => void;
}

// Module-level fallback so the token survives tab navigation without using localStorage
let inMemoryToken: string | null = null;

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

export default function CustomerApp(props: CustomerAppProps) {
  const { token: propToken, setToken: propSetToken } = props;
  const [localToken, setLocalToken] = useState<string | null>(inMemoryToken);

  const token = propToken !== undefined ? propToken : localToken;
  const updateToken = (newToken: string | null) => {
    inMemoryToken = newToken;
    if (propSetToken) {
      propSetToken(newToken);
    } else {
      setLocalToken(newToken);
    }
  };

  const [profile, setProfile] = useState<Account | null>(null);
  const [view, setView] = useState<'login' | 'register'>('login');
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setProfile(null);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const res = await fetch('/customers/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data: Account = await res.json();
        setProfile(data);
        setName(data.name);
        setDeliveryAddress(data.delivery_address || '');
      } else {
        const errMsg = await parseErrorMessage(res, 'Session expired. Please sign in again.');
        updateToken(null);
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error loading profile. Please check if the server is running.' });
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (res.ok) {
        const data = await res.json();
        updateToken(data.access_token);
      } else {
        const errMsg = await parseErrorMessage(res, 'Login failed');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error during login. Please try again.' });
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch('/customers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });

      if (res.ok) {
        setMessage({ type: 'success', text: 'Account created! Please log in.' });
        setView('login');
      } else {
        const errMsg = await parseErrorMessage(res, 'Registration failed');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error during registration. Please try again.' });
    }
  };

  const handleUpdateName = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch('/customers/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name })
      });
      if (res.ok) {
        const updatedAccount = await res.json();
        setProfile(updatedAccount);
        setMessage({ type: 'success', text: 'Name updated successfully.' });
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to update name.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error while updating name.' });
    }
  };

  const handleUpdateAddress = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      const res = await fetch('/customers/me/address', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ delivery_address: deliveryAddress })
      });
      if (res.ok) {
        const updatedAccount = await res.json();
        setProfile(updatedAccount);
        setMessage({ type: 'success', text: 'Address updated successfully.' });
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to update address.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error while updating address.' });
    }
  };

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate your account? This cannot be undone.')) return;
    setMessage(null);
    try {
      const res = await fetch('/customers/me/deactivate', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        updateToken(null);
        setMessage({ type: 'success', text: 'Account successfully deactivated.' });
      } else {
        const errMsg = await parseErrorMessage(res, 'Failed to deactivate account.');
        setMessage({ type: 'error', text: errMsg });
      }
    } catch {
      setMessage({ type: 'error', text: 'Network error while deactivating account.' });
    }
  };

  const inputStyle = {
    padding: '0.85rem',
    border: '2px solid #8b0000',
    borderRadius: '4px',
    backgroundColor: '#fff8dc',
    color: '#3e2723',
    fontFamily: 'inherit',
    fontSize: '1.05rem',
    width: '100%',
    boxSizing: 'border-box' as const,
    boxShadow: 'inset 2px 2px 5px rgba(0,0,0,0.05)',
  };

  const btnStyle = {
    padding: '0.85rem',
    backgroundColor: '#3e2723',
    color: '#ffd700',
    border: '2px solid #8b0000',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '1.15rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '2px',
    fontFamily: 'inherit',
    width: '100%',
    boxShadow: '3px 3px 0px rgba(0,0,0,0.2)',
  };

  const linkBtnStyle = {
    background: 'none',
    border: 'none',
    color: '#8b0000',
    textDecoration: 'underline',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '1.05rem',
    fontFamily: 'inherit',
    padding: 0,
  };

  const renderMessage = () => {
    if (!message) return null;
    const isError = message.type === 'error';
    return (
      <div style={{ 
        backgroundColor: isError ? '#ffebee' : '#e8f5e9', 
        color: isError ? '#c62828' : '#2e7d32', 
        padding: '0.85rem', 
        border: `2px solid ${isError ? '#c62828' : '#2e7d32'}`,
        borderRadius: '4px',
        marginBottom: '1.5rem',
        fontWeight: 'bold',
        textAlign: 'center'
      }}>
        {message.text}
      </div>
    );
  };

  if (profile) {
    return (
      <div style={{ maxWidth: '650px', margin: '0 auto', textAlign: 'center' }}>
        {renderMessage()}
        
        {/* WANTED POSTER PROFILE VIEW */}
        <div style={{ 
          backgroundColor: '#eaddcf', 
          border: '10px solid #3e2723', 
          padding: '2.5rem', 
          boxShadow: '8px 8px 15px rgba(0,0,0,0.3)', 
          position: 'relative',
          marginBottom: '2rem'
        }}>
          {/* Decorative Corner Pins */}
          <div style={{ position: 'absolute', top: '10px', left: '10px', width: '12px', height: '12px', backgroundColor: '#8b0000', borderRadius: '50%', border: '2px solid #3e2723' }}></div>
          <div style={{ position: 'absolute', top: '10px', right: '10px', width: '12px', height: '12px', backgroundColor: '#8b0000', borderRadius: '50%', border: '2px solid #3e2723' }}></div>
          <div style={{ position: 'absolute', bottom: '10px', left: '10px', width: '12px', height: '12px', backgroundColor: '#8b0000', borderRadius: '50%', border: '2px solid #3e2723' }}></div>
          <div style={{ position: 'absolute', bottom: '10px', right: '10px', width: '12px', height: '12px', backgroundColor: '#8b0000', borderRadius: '50%', border: '2px solid #3e2723' }}></div>

          <h2 style={{ fontSize: '3.5rem', margin: 0, color: '#3e2723', textTransform: 'uppercase', letterSpacing: '6px', borderBottom: '4px solid #3e2723', paddingBottom: '0.5rem', lineHeight: '1' }}>WANTED</h2>
          <h3 style={{ fontSize: '1.8rem', color: '#8b0000', margin: '0.75rem 0 1.5rem 0', letterSpacing: '3px' }}>DEAD OR ALIVE</h3>
          
          <div style={{ 
            backgroundColor: '#fdf6e3', 
            border: '4px solid #3e2723', 
            padding: '2rem 1rem', 
            margin: '0 auto 1.5rem auto',
            width: '80%',
            boxShadow: 'inset 0 0 20px rgba(0,0,0,0.1)' 
          }}>
            <h1 style={{ fontSize: '2.5rem', color: '#3e2723', margin: '0', textTransform: 'uppercase', wordWrap: 'break-word' }}>
              {profile.name}
            </h1>
          </div>

          <p style={{ fontSize: '1.3rem', color: '#555', fontWeight: 'bold', marginBottom: '2rem', borderBottom: '2px dashed #a67b5b', paddingBottom: '1.5rem' }}>
            📍 Known Hideout: <br/>
            <span style={{ color: '#8b0000', fontSize: '1.5rem' }}>{profile.delivery_address || 'Unknown Waters'}</span>
          </p>

          <div style={{ backgroundColor: 'rgba(255,255,255,0.5)', padding: '1.5rem', border: '2px dashed #a67b5b', borderRadius: '8px' }}>
            <h4 style={{ color: '#3e2723', marginTop: 0, marginBottom: '1rem', fontSize: '1.2rem', textTransform: 'uppercase' }}>✍️ Update Bounty Info</h4>
            
            <form onSubmit={handleUpdateName} style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="New Pirate Name" required style={{...inputStyle, flex: 1, minWidth: '200px'}} />
              <button type="submit" style={{...btnStyle, width: 'auto', whiteSpace: 'nowrap', padding: '0.85rem 1.5rem'}}>Change Name</button>
            </form>

            <form onSubmit={handleUpdateAddress} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <input value={deliveryAddress} onChange={e => setDeliveryAddress(e.target.value)} placeholder="New Delivery Coordinates" style={{...inputStyle, flex: 1, minWidth: '200px'}} />
              <button type="submit" style={{...btnStyle, width: 'auto', whiteSpace: 'nowrap', padding: '0.85rem 1.5rem'}}>Change Hideout</button>
            </form>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center' }}>
          <button onClick={() => updateToken(null)} style={{...btnStyle, backgroundColor: '#8b0000', color: '#fff', width: 'auto', padding: '0.85rem 2rem'}}>Drop Anchor (Log Out)</button>
          <button onClick={handleDeactivate} style={{...linkBtnStyle, color: '#c62828'}}>Scuttle Ship (Deactivate)</button>
        </div>
      </div>
    );
  }

  // LOGIN / REGISTER VIEW
  return (
    <div style={{ maxWidth: '420px', margin: '0 auto', textAlign: 'center', padding: '1rem 0' }}>
      <h3 style={{ color: '#8b0000', borderBottom: '2px dashed #a67b5b', paddingBottom: '0.75rem', marginBottom: '2rem', fontSize: '1.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
        {view === 'login' ? '🏴‍☠️ Sign In' : '📜 Register Crew'}
      </h3>
      
      {renderMessage()}

      {view === 'login' ? (
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} />
          <input type="password" placeholder="Secret Passcode" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} />
          <button type="submit" style={btnStyle}>Log In</button>
          
          <p style={{ color: '#3e2723', fontWeight: 'bold', marginTop: '1rem', fontSize: '1.1rem' }}>
            New to the waters? <br/><button type="button" onClick={() => setView('register')} style={{...linkBtnStyle, marginTop: '0.75rem', fontSize: '1.1rem'}}>Join the Fleet</button>
          </p>
        </form>
      ) : (
        <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <input type="text" placeholder="Pirate Name" value={name} onChange={e => setName(e.target.value)} required style={inputStyle} />
          <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} required style={inputStyle} />
          <input type="password" placeholder="Secret Passcode" value={password} onChange={e => setPassword(e.target.value)} required style={inputStyle} />
          <button type="submit" style={btnStyle}>Sign Articles</button>
          
          <p style={{ color: '#3e2723', fontWeight: 'bold', marginTop: '1rem', fontSize: '1.1rem' }}>
            Already in the crew? <br/><button type="button" onClick={() => setView('login')} style={{...linkBtnStyle, marginTop: '0.75rem', fontSize: '1.1rem'}}>Log In</button>
          </p>
        </form>
      )}
    </div>
  );
}