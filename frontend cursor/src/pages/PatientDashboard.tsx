import React, { useEffect, useMemo, useRef, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

type AssignedExercise = {
	id: string;
	exerciseId: string;
	exercise: { id: string; name: string; description: string; reps: number; sets: number };
	patientId: string;
	reps: number;
	sets: number;
	instructions: string;
	status: string;
};

type ExerciseSession = {
	isActive: boolean;
	currentExercise: string | null;
	repsCompleted: number;
	setsCompleted: number;
	aiFeedback: string;
	confidence: number;
};

const PatientDashboard: React.FC = () => {
	const { user, logout } = useAuth();
	const [exercises, setExercises] = useState<AssignedExercise[]>([]);
	const [aiScore, setAiScore] = useState<{ score: number; message: string } | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [exerciseSession, setExerciseSession] = useState<ExerciseSession>({
		isActive: false,
		currentExercise: null,
		repsCompleted: 0,
		setsCompleted: 0,
		aiFeedback: '',
		confidence: 0
	});

	const videoRef = useRef<HTMLVideoElement | null>(null);
	const canvasRef = useRef<HTMLCanvasElement | null>(null);
	const [ws, setWs] = useState<WebSocket | null>(null);
	const [realtime, setRealtime] = useState<{ label?: string; confidence?: number }>({});
	const [cameraActive, setCameraActive] = useState(false);

	const wsUrl = useMemo(() => {
		const base = (import.meta.env.VITE_API_WS_URL as string) ?? 'ws://127.0.0.1:8000/realtime/ws';
		return base;
	}, []);

	useEffect(() => {
		(async () => {
			try {
				const [exRes, scoreRes] = await Promise.all([
					api.get('/patients/exercises'),
					api.get('/patients/ai-score')
				]);
			setExercises(exRes.data);
			setAiScore(scoreRes.data);
		} catch (e: any) {
			setError(e?.response?.data?.detail ?? 'Failed to load data');
		} finally {
			setLoading(false);
		}
		})();
	}, []);

	const startCamera = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ 
				video: { width: 640, height: 480 }, 
				audio: false 
			});
		if (videoRef.current) {
			videoRef.current.srcObject = stream;
			await videoRef.current.play();
				setCameraActive(true);
			}
		} catch (err) {
			console.error('Error accessing camera:', err);
			alert('Could not access camera. Please check permissions.');
		}
	};

	const stopCamera = () => {
		if (videoRef.current && videoRef.current.srcObject) {
			const stream = videoRef.current.srcObject as MediaStream;
			stream.getTracks().forEach(track => track.stop());
			videoRef.current.srcObject = null;
			setCameraActive(false);
		}
		if (ws) {
			ws.close();
			setWs(null);
		}
		setRealtime({});
	};

	const startExercise = (exercise: AssignedExercise) => {
		setExerciseSession({
			isActive: true,
			currentExercise: exercise.exercise.name,
			repsCompleted: 0,
			setsCompleted: 0,
			aiFeedback: 'Starting exercise...',
			confidence: 0
		});
		startCamera();
	};

	const stopExercise = () => {
		setExerciseSession({
			isActive: false,
			currentExercise: null,
			repsCompleted: 0,
			setsCompleted: 0,
			aiFeedback: '',
			confidence: 0
		});
		stopCamera();
	};

	const startRealtime = () => {
		if (!videoRef.current || !canvasRef.current) return;
		
		const socket = new WebSocket(wsUrl);
		setWs(socket);
		
		socket.onopen = () => {
			console.log('WebSocket connected');
		};
		
		socket.onmessage = (ev) => {
			try {
				const data = JSON.parse(ev.data);
				if (data.label) {
					setRealtime({ label: data.label, confidence: data.confidence });
					
					// Update exercise session with AI feedback
					if (exerciseSession.isActive) {
						setExerciseSession(prev => ({
							...prev,
							aiFeedback: `Detected: ${data.label}`,
							confidence: data.confidence || 0
						}));
					}
				}
			} catch (e) {
				console.error('Error parsing WebSocket message:', e);
			}
		};
		
		socket.onerror = (error) => {
			console.error('WebSocket error:', error);
		};
		
		socket.onclose = () => {
			console.log('WebSocket disconnected');
		};
		
		const ctx = canvasRef.current.getContext('2d')!;
		const tick = () => {
			if (!videoRef.current || socket.readyState !== 1) return;
			
			const w = videoRef.current.videoWidth;
			const h = videoRef.current.videoHeight;
			canvasRef.current!.width = w;
			canvasRef.current!.height = h;
			ctx.drawImage(videoRef.current, 0, 0, w, h);
			
			const dataUrl = canvasRef.current!.toDataURL('image/jpeg', 0.5);
			socket.send(JSON.stringify({ image_b64: dataUrl }));
			
			requestAnimationFrame(tick);
		};
		requestAnimationFrame(tick);
	};

	const completeRep = () => {
		if (exerciseSession.isActive) {
			setExerciseSession(prev => ({
				...prev,
				repsCompleted: prev.repsCompleted + 1
			}));
		}
	};

	const completeSet = () => {
		if (exerciseSession.isActive) {
			setExerciseSession(prev => ({
				...prev,
				setsCompleted: prev.setsCompleted + 1,
				repsCompleted: 0
			}));
		}
	};

    if (loading) return (
        <div className="container" style={{ padding: '48px 0', textAlign: 'center' }}>
            <div className="card">Loading your dashboard…</div>
        </div>
    );

    if (error) return (
        <div className="container" style={{ padding: '48px 0' }}>
            <div className="card" style={{ borderLeft: '6px solid var(--red)' }}>Error: {error}</div>
        </div>
    );

	return (
        <div>
            <header style={{ background: 'var(--color-card)', boxShadow: 'var(--shadow-1)' }}>
                <div className="container" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div className="h1" style={{ margin: 0 }}>Good day, {user?.full_name || user?.email}</div>
                        <div className="muted">We’re here with you. Every step counts.</div>
                    </div>
                    <button className="btn btn-danger" onClick={logout}>Logout</button>
                </div>
            </header>

            <div className="container" style={{ padding: '24px 0' }}>
				{/* Exercise Session */}
				{exerciseSession.isActive && (
                    <div className="card" style={{ background: 'var(--green)', color: 'white', textAlign: 'center' }}>
						<h2 style={{ margin: '0 0 10px 0' }}>Exercise in Progress: {exerciseSession.currentExercise}</h2>
						<div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '15px' }}>
							<div>
								<strong>Reps Completed:</strong> {exerciseSession.repsCompleted}
							</div>
							<div>
								<strong>Sets Completed:</strong> {exerciseSession.setsCompleted}
							</div>
							<div>
								<strong>AI Confidence:</strong> {(exerciseSession.confidence * 100).toFixed(1)}%
							</div>
						</div>
						<div style={{ marginBottom: '15px' }}>
							<strong>AI Feedback:</strong> {exerciseSession.aiFeedback}
						</div>
						<div>
                            <button className="btn btn-primary" onClick={completeRep}>
								Complete Rep
							</button>
                            <button className="btn btn-secondary" onClick={completeSet}>
								Complete Set
							</button>
                            <button className="btn btn-danger" onClick={stopExercise}>
								Stop Exercise
							</button>
						</div>
					</div>
				)}

				{/* Main Content Grid */}
                <div className="grid-2">
					{/* Assigned Exercises */}
                    <div className="card">
                        <div className="h2">Your Exercises</div>
						{exercises.length === 0 ? (
                            <p className="muted" style={{ textAlign: 'center' }}>No exercises assigned yet</p>
						) : (
                            <div className="grid">
								{exercises.map((exercise) => (
                                    <div key={exercise.id} className="card">
                                        <h3 style={{ margin: '0 0 10px 0' }}>
											{exercise.exercise.name}
										</h3>
                                        <p className="muted" style={{ margin: '0 0 10px 0' }}>
											{exercise.exercise.description}
										</p>
										<div style={{ marginBottom: '10px' }}>
                                            <span className="badge badge-green">{exercise.reps} reps × {exercise.sets} sets</span>
										</div>
										<div style={{ marginBottom: '15px' }}>
											<strong>Instructions:</strong> {exercise.instructions}
										</div>
										<div style={{ marginBottom: '15px' }}>
											<strong>Status:</strong> 
                                            <span className={exercise.status === 'completed' ? 'badge badge-green' : exercise.status === 'in_progress' ? 'badge badge-amber' : 'badge badge-blue'} style={{ marginLeft: 6 }}>{exercise.status}</span>
										</div>
										{!exerciseSession.isActive && (
                                            <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => startExercise(exercise)}>
												Start Exercise
											</button>
										)}
									</div>
								))}
							</div>
						)}
					</div>

					{/* Camera and AI Analysis */}
                    <div className="card">
                        <div className="h2" style={{ marginBottom: 20 }}>Exercise Analysis</div>
						
						{/* Camera Feed */}
						<div style={{ 
							backgroundColor: '#000', 
							borderRadius: '8px', 
							overflow: 'hidden',
							marginBottom: '20px',
							position: 'relative'
						}}>
							<video 
								ref={videoRef} 
								style={{ 
									width: '100%', 
									height: '300px',
									objectFit: 'cover'
								}} 
								muted 
								playsInline 
							/>
							{!cameraActive && (
								<div style={{
									position: 'absolute',
									top: '50%',
									left: '50%',
									transform: 'translate(-50%, -50%)',
									color: 'white',
									textAlign: 'center'
								}}>
									<div style={{ fontSize: '48px', marginBottom: '10px' }}>📹</div>
									<div>Camera not active</div>
								</div>
							)}
						</div>
						
						<canvas ref={canvasRef} style={{ display: 'none' }} />
						
						{/* Controls */}
                        <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
							{!cameraActive ? (
                                <button className="btn btn-primary" onClick={startCamera}>
									Start Camera
								</button>
							) : (
                                <button className="btn btn-danger" onClick={stopCamera}>
									Stop Camera
								</button>
							)}
							
							{cameraActive && !ws && (
                                <button className="btn btn-secondary" onClick={startRealtime}>
									Start AI Analysis
								</button>
							)}
						</div>

						{/* AI Feedback */}
                        <div className="card" style={{ background: 'var(--sky)' }}>
                            <h3 style={{ margin: '0 0 10px 0' }}>AI Analysis</h3>
							<div>
								<strong>Detected Exercise:</strong> {realtime.label || 'None'}
							</div>
							<div>
								<strong>Confidence:</strong> {realtime.confidence ? (realtime.confidence * 100).toFixed(1) + '%' : 'N/A'}
							</div>
						</div>

						{/* AI Score */}
						<div style={{
							backgroundColor: '#d5f4e6',
							padding: '15px',
							borderRadius: '8px'
						}}>
							<h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>Your Progress</h3>
							{aiScore ? (
								<div>
									<div style={{ fontSize: '24px', fontWeight: 'bold', color: '#27ae60' }}>
										Score: {aiScore.score}%
									</div>
									<div style={{ color: '#2c3e50' }}>{aiScore.message}</div>
								</div>
							) : (
								<div style={{ color: '#7f8c8d' }}>No score available yet</div>
							)}
						</div>
                    </div>
                </div>
            </div>
		</div>
	);
};

export default PatientDashboard;


