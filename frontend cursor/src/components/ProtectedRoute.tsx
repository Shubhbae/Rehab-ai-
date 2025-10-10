import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles: Array<'patient' | 'doctor'> }> = ({ children, allowedRoles }) => {
	const { user, loading } = useAuth();
	if (loading) return <div style={{ padding: 24 }}>Loading...</div>;
	if (!user) return <Navigate to="/login" replace />;
	if (!allowedRoles.includes(user.role)) return <Navigate to="/login" replace />;
	return <>{children}</>;
};

export default ProtectedRoute;


