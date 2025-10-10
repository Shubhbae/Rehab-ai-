import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api, { setAccessToken, clearAccessToken } from '@/services/api';

type Role = 'patient' | 'doctor';

type User = {
	id: number | string;
	email: string;
	role: Role;
};

type AuthContextValue = {
	user: User | null;
	loading: boolean;
	login: (email: string, password: string) => Promise<void>;
    signup: (firstName: string, lastName: string, email: string, password: string, role: Role) => Promise<void>;
	verifyOtp: (phone: string, otp: string, role: Role) => Promise<void>;
	logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);

	const fetchMe = useCallback(async () => {
		try {
			const { data } = await api.get('/auth/me');
			setUser(data);
		} catch {
			setUser(null);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		const stored = localStorage.getItem('access_token');
		if (stored) {
			setAccessToken(stored);
		}
		fetchMe();
	}, [fetchMe]);

    const login = useCallback(async (email: string, password: string) => {
		const body = new URLSearchParams();
		body.set('username', email);
		body.set('password', password);
		const { data } = await api.post('/auth/login', body, {
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
		});
		setAccessToken(data.access_token);
		localStorage.setItem('access_token', data.access_token);
		await fetchMe();
	}, [fetchMe]);

	const signup = useCallback(async (firstName: string, lastName: string, email: string, password: string, role: Role) => {
		const response = await api.post('/auth/signup', {
			first_name: firstName,
			last_name: lastName,
			email,
			password,
			role,
		});
		
		// Set the Supabase access token
		if (response.data.session?.access_token) {
			setAccessToken(response.data.session.access_token);
			localStorage.setItem('access_token', response.data.session.access_token);
			await fetchMe();
		}
	}, [fetchMe]);

	const verifyOtp = useCallback(async (phone: string, otp: string, role: Role) => {
		const { data } = await api.post('/auth/verify-otp', null, { params: { phone, otp, role } });
		setAccessToken(data.token);
		localStorage.setItem('access_token', data.token);
		await fetchMe();
	}, [fetchMe]);

	const logout = useCallback(() => {
		clearAccessToken();
		localStorage.removeItem('access_token');
		setUser(null);
	}, []);

    const value = useMemo<AuthContextValue>(() => ({ user, loading, login, signup, verifyOtp, logout }), [user, loading, login, signup, verifyOtp, logout]);

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
	const ctx = useContext(AuthContext);
	if (!ctx) throw new Error('useAuth must be used within AuthProvider');
	return ctx;
};


