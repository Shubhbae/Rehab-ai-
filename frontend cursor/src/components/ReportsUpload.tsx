import React, { useState } from 'react';
import api from '@/services/api';
import { useToast } from '@/contexts/ToastContext';

const ReportsUpload: React.FC = () => {
	const [file, setFile] = useState<File | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const { push } = useToast();

	const onUpload = async () => {
		if (!file) return;
		setLoading(true);
		setError(null);
		try {
			const form = new FormData();
			form.append('file', file);
			await api.post('/patients/reports', form, { headers: { 'Content-Type': 'multipart/form-data' } });
			push({ type: 'success', message: 'Report uploaded successfully' });
			setFile(null);
		} catch (e: any) {
			setError(e?.response?.data?.detail ?? 'Upload failed');
			push({ type: 'error', message: 'Upload failed' });
		} finally {
			setLoading(false);
		}
	};

	return (
		<div style={{ display: 'grid', gap: 8 }}>
			<h4>Upload Medical Report</h4>
			<input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
			<button disabled={!file || loading} onClick={onUpload}>{loading ? 'Uploading…' : 'Upload'}</button>
			{error && <div style={{ color: 'red' }}>{error}</div>}
		</div>
	);
};

export default ReportsUpload;



