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
		<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
			<form onSubmit={onSubmit} style={{ width: 360, display: 'grid', gap: 12 }}>
				<h2>{authType === 'signup' ? 'Create your account' : 'Rehab AI Login'}</h2>
				<label>
					Role
					<select value={role} onChange={(e) => setRole(e.target.value as any)}>
						<option value="patient">Patient</option>
						<option value="doctor">Doctor</option>
					</select>
				</label>
				<div>
					<button type="button" onClick={() => setAuthType('login')} disabled={authType === 'login'}>Login</button>
					<button type="button" onClick={() => setAuthType('signup')} disabled={authType === 'signup'} style={{ marginLeft: 8 }}>Sign Up</button>
				</div>
				<div>
					<label>
						<input type="radio" checked={mode === 'password'} onChange={() => setMode('password')} /> Password
					</label>
					<label style={{ marginLeft: 12 }}>
						<input type="radio" checked={mode === 'otp'} onChange={() => setMode('otp')} /> OTP
					</label>
				</div>
				{authType === 'signup' ? (
					<>
						<input placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
						<input placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
						<input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
						<input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
					</>
				) : mode === 'password' ? (
					<>
						<input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
						<input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
					</>
				) : (
					<>
						<input placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
						<input placeholder="OTP" value={otp} onChange={(e) => setOtp(e.target.value)} />
					</>
				)}
				<button disabled={loading} type="submit">{loading ? 'Please wait…' : authType === 'signup' ? 'Create account' : 'Continue'}</button>
				{error && <div style={{ color: 'red' }}>{error}</div>}
			</form>
		</div>
	);
}

export default Login;


