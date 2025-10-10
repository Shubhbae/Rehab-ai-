import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import Login from './pages/Login';
import PatientDashboard from './pages/PatientDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
	return (
		<AuthProvider>
			<ToastProvider>
			<Routes>
				<Route path="/login" element={<Login />} />
				<Route
					path="/patient"
					element={
						<ProtectedRoute allowedRoles={["patient"]}>
							<PatientDashboard />
						</ProtectedRoute>
					}
				/>
				<Route
					path="/doctor"
					element={
						<ProtectedRoute allowedRoles={["doctor"]}>
							<DoctorDashboard />
						</ProtectedRoute>
					}
				/>
				<Route path="*" element={<Navigate to="/login" replace />} />
			</Routes>
			</ToastProvider>
		</AuthProvider>
	);
};

export default App;


