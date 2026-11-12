import { useState, useEffect, FormEvent } from 'react';

interface Account {
  id: string;
  name: string;
  email: string;
  delivery_address?: string | null;
  is_active: boolean;
}

export default function CustomerApp() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('accessToken'));
  const [profile, setProfile] = useState<Account | null>(null);
  const [view, setView] = useState<'login' | 'register'>('login');
  const [message, setMessage] = useState<{ type: 'error' | 'success', text: string } | null>(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');

  useEffect(() => {
    if (token) {
      localStorage.setItem('accessToken', token);
      fetchProfile();
    } else {
      localStorage.removeItem('accessToken');
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
        setToken(null);
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error loading profile.' });
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await res.json();
    if (res.ok) {
      setToken(data.access_token);
    } else {
      setMessage({ type: 'error', text: data.detail || 'Login failed' });
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    const res = await fetch('/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });

    if (res.ok) {
      setMessage({ type: 'success', text: 'Account created! Please log in.' });
      setView('login');
    } else {
      const data = await res.json();
      setMessage({ type: 'error', text: data.detail || 'Registration failed' });
    }
  };

  const handleUpdateName = async (e: FormEvent) => {
    e.preventDefault();
    const res = await fetch('/customers/me', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ name })
    });
    if (res.ok) {
      const updatedAccount = await res.json();
      setProfile(updatedAccount);
      setMessage({ type: 'success', text: 'Name updated successfully.' });
    }
  };

  const handleUpdateAddress = async (e: FormEvent) => {
    e.preventDefault();
    const res = await fetch('/customers/me/address', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ delivery_address: deliveryAddress })
    });
    if (res.ok) {
      const updatedAccount = await res.json();
      setProfile(updatedAccount);
      setMessage({ type: 'success', text: 'Address updated successfully.' });
    }
  };

  const handleDeactivate = async () => {
    if (!window.confirm('Are you sure you want to deactivate your account? This cannot be undone.')) return;
    const res = await fetch('/customers/me/deactivate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      setToken(null);
      setMessage({ type: 'success', text: 'Account successfully deactivated.' });
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
      <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h3 style={{ color: '#8b0000', marginBottom: '0.5rem', fontSize: '2.2rem', textTransform: 'uppercase' }}>
          Ahoy, {profile.name}! 🏴‍☠️
        </h3>
        {renderMessage()}
        
        <div style={{ marginBottom: '2rem', padding: '2rem', border: '2px dashed #a67b5b', backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
          <h4 style={{ color: '#3e2723', marginTop: 0, borderBottom: '2px solid #a67b5b', paddingBottom: '0.75rem', fontSize: '1.2rem' }}>Update Crew Manifest</h4>
          
          <form onSubmit={handleUpdateName} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Your Pirate Name" required style={{...inputStyle, flex: 1, minWidth: '200px'}} />
            <button type="submit" style={{...btnStyle, width: 'auto', whiteSpace: 'nowrap', padding: '0.85rem 1.5rem'}}>Update Name</button>
          </form>

          <form onSubmit={handleUpdateAddress} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <input value={deliveryAddress} onChange={e => setDeliveryAddress(e.target.value)} placeholder="Island Delivery Coordinates" style={{...inputStyle, flex: 1, minWidth: '200px'}} />
            <button type="submit" style={{...btnStyle, width: 'auto', whiteSpace: 'nowrap', padding: '0.85rem 1.5rem'}}>Update Address</button>
          </form>
        </div>

        <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center' }}>
          <button onClick={() => setToken(null)} style={{...btnStyle, backgroundColor: '#8b0000', color: '#fff', width: 'auto', padding: '0.85rem 2rem'}}>Drop Anchor (Log Out)</button>
          <button onClick={handleDeactivate} style={{...linkBtnStyle, color: '#c62828'}}>Scuttle Ship (Deactivate)</button>
        </div>
      </div>
    );
  }

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