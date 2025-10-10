import React, { useEffect, useState } from 'react';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

type Patient = { id: number; email: string; full_name: string };

const DoctorDashboard: React.FC = () => {
	const { user } = useAuth();
	const [patients, setPatients] = useState<Patient[]>([]);
	const [selectedId, setSelectedId] = useState<number | null>(null);
	const [analytics, setAnalytics] = useState<any | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		(async () => {
			try {
				const { data } = await api.get('/patients/');
				setPatients(data);
			} catch (e: any) {
				setError(e?.response?.data?.detail ?? 'Failed to load patients');
			} finally {
				setLoading(false);
			}
		})();
	}, []);

	useEffect(() => {
		(async () => {
			if (!selectedId) return;
			try {
				const { data } = await api.get(`/analytics/patient/${selectedId}`);
				setAnalytics(data);
			} catch {}
		})();
	}, [selectedId]);

	if (loading) return <div style={{ padding: 24 }}>Loading…</div>;
	if (error) return <div style={{ padding: 24, color: 'red' }}>{error}</div>;

	const chartData = analytics ? Object.entries(analytics.label_distribution).map(([label, count]) => ({ label, count })) : [];

	return (
		<div style={{ padding: 24, display: 'grid', gap: 24 }}>
			<h2>Doctor Dashboard — {user?.email}</h2>
			<section>
				<h3>Patients</h3>
				<select value={selectedId ?? ''} onChange={(e) => setSelectedId(Number(e.target.value))}>
					<option value="" disabled>Select patient</option>
					{patients.map((p) => (
						<option key={p.id} value={p.id}>{p.full_name ?? p.email}</option>
					))}
				</select>
			</section>
			{analytics && (
				<section>
					<h3>Progress analytics</h3>
					<div style={{ width: '100%', height: 300 }}>
						<ResponsiveContainer>
							<BarChart data={chartData}>
								<CartesianGrid strokeDasharray="3 3" />
								<XAxis dataKey="label" />
								<YAxis allowDecimals={false} />
								<Tooltip />
								<Bar dataKey="count" fill="#8884d8" />
							</BarChart>
						</ResponsiveContainer>
					</div>
				</section>
			)}
		</div>
	);
};

export default DoctorDashboard;


