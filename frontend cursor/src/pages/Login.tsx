import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
	const { login, signup, verifyOtp } = useAuth();
	const navigate = useNavigate();
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [phone, setPhone] = useState('');
	const [otp, setOtp] = useState('');
	const [mode, setMode] = useState<'password' | 'otp'>('password');
	const [authType, setAuthType] = useState<'login' | 'signup'>('login');
	const [firstName, setFirstName] = useState('');
	const [lastName, setLastName] = useState('');
	const [role, setRole] = useState<'patient' | 'doctor'>('patient');
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const onSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setError(null);
		setLoading(true);
		try {
			if (authType === 'signup') {
				await signup(firstName, lastName, email, password, role);
			} else if (mode === 'password') {
				await login(email, password);
			} else {
				await verifyOtp(phone, otp, role);
			}
			navigate(role === 'doctor' ? '/doctor' : '/patient', { replace: true });
		} catch (err: any) {
			setError(err?.response?.data?.detail ?? 'Login failed');
		} finally {
			setLoading(false);
		}
	};

  return (
    <div style={{ minHeight: '100vh', background: '#0b0b0b', display: 'grid', placeItems: 'center', padding: 16 }}>
      <div style={{ width: 420, background: '#111', borderRadius: 16, boxShadow: '0 12px 32px rgba(0,0,0,0.35)', padding: 24, color: '#fff' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#1f1f1f', display: 'grid', placeItems: 'center', marginRight: 8 }}>
            <span style={{ fontSize: 28 }}>&#10084;</span>
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: 1 }}>REHAB AI</div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <button type="button" className="btn" style={{ flex: 1, background: authType === 'login' ? '#fff' : 'transparent', color: authType === 'login' ? '#000' : '#fff', border: '1px solid #2a2a2a' }} onClick={() => setAuthType('login')}>Login</button>
          <button type="button" className="btn" style={{ flex: 1, background: authType === 'signup' ? '#fff' : 'transparent', color: authType === 'signup' ? '#000' : '#fff', border: '1px solid #2a2a2a' }} onClick={() => setAuthType('signup')}>Sign Up</button>
        </div>
        <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12 }}>
          <label style={{ color: '#bbb' }}>Role
            <select className="input" value={role} onChange={(e) => setRole(e.target.value as any)}>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </label>
          <div style={{ display: 'flex', gap: 12 }}>
            <label style={{ color: '#bbb' }}>
              <input type="radio" checked={mode === 'password'} onChange={() => setMode('password')} /> Password
            </label>
            <label style={{ color: '#bbb' }}>
              <input type="radio" checked={mode === 'otp'} onChange={() => setMode('otp')} /> OTP
            </label>
          </div>
          {authType === 'signup' ? (
            <>
              <input className="input" placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              <input className="input" placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
              <input className="input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
              <input className="input" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </>
          ) : mode === 'password' ? (
            <>
              <input className="input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
              <input className="input" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </>
          ) : (
            <>
              <input className="input" placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
              <input className="input" placeholder="OTP" value={otp} onChange={(e) => setOtp(e.target.value)} />
            </>
          )}
          <button disabled={loading} type="submit" className="btn btn-primary" style={{ background: '#fff', color: '#000' }}>{loading ? 'Please wait…' : authType === 'signup' ? 'Create account' : 'Continue'}</button>
          {error && <div style={{ color: '#ff6b6b' }}>{error}</div>}
        </form>
      </div>
    </div>
  );
}

export default Login;


