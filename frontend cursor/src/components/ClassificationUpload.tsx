import React, { useState } from 'react';
import api from '@/services/api';

const ClassificationUpload: React.FC = () => {
	const [file, setFile] = useState<File | null>(null);
	const [exercise, setExercise] = useState('squat');
	const [result, setResult] = useState<any | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const onUpload = async () => {
		if (!file) return;
		setLoading(true);
		setError(null);
		try {
			const form = new FormData();
			form.append('file', file);
			form.append('exercise_name', exercise);
			const { data } = await api.post('/classify/video', form, { headers: { 'Content-Type': 'multipart/form-data' } });
			setResult(data);
		} catch (e: any) {
			setError(e?.response?.data?.detail ?? 'Upload failed');
		} finally {
			setLoading(false);
		}
	};

	return (
		<div style={{ display: 'grid', gap: 8 }}>
			<h4>Upload Video for AI Classification</h4>
			<select value={exercise} onChange={(e) => setExercise(e.target.value)}>
				<option value="squat">Squat</option>
				<option value="step_jack">Step Jack</option>
				<option value="half_wheel">Half Wheel</option>
			</select>
			<input type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
			<button disabled={!file || loading} onClick={onUpload}>{loading ? 'Uploading…' : 'Upload'}</button>
			{error && <div style={{ color: 'red' }}>{error}</div>}
			{result && (
				<pre style={{ background: '#f5f5f5', padding: 8, overflow: 'auto' }}>{JSON.stringify(result, null, 2)}</pre>
			)}
		</div>
	);
};

export default ClassificationUpload;


