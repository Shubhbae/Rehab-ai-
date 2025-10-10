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
		<div style={{ 
			display: 'flex', 
			justifyContent: 'center', 
			alignItems: 'center', 
			height: '100vh',
			fontSize: '18px'
		}}>
			Loading your dashboard...
		</div>
	);

	if (error) return (
		<div style={{ 
			padding: 24, 
			color: 'red', 
			textAlign: 'center',
			fontSize: '18px'
		}}>
			Error: {error}
		</div>
	);

	return (
		<div style={{ 
			minHeight: '100vh', 
			backgroundColor: '#f5f5f5',
			fontFamily: 'Arial, sans-serif'
		}}>
			{/* Header */}
			<header style={{
				backgroundColor: '#2c3e50',
				color: 'white',
				padding: '20px',
				display: 'flex',
				justifyContent: 'space-between',
				alignItems: 'center'
			}}>
				<div>
					<h1 style={{ margin: 0, fontSize: '24px' }}>Patient Dashboard</h1>
					<p style={{ margin: '5px 0 0 0', opacity: 0.8 }}>Welcome, {user?.full_name || user?.email}</p>
				</div>
				<button 
					onClick={logout}
					style={{
						backgroundColor: '#e74c3c',
						color: 'white',
						border: 'none',
						padding: '10px 20px',
						borderRadius: '5px',
						cursor: 'pointer'
					}}
				>
					Logout
				</button>
			</header>

			<div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
				{/* Exercise Session */}
				{exerciseSession.isActive && (
					<div style={{
						backgroundColor: '#27ae60',
						color: 'white',
						padding: '20px',
						borderRadius: '10px',
						marginBottom: '20px',
						textAlign: 'center'
					}}>
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
							<button 
								onClick={completeRep}
								style={{
									backgroundColor: '#3498db',
									color: 'white',
									border: 'none',
									padding: '10px 20px',
									borderRadius: '5px',
									marginRight: '10px',
									cursor: 'pointer'
								}}
							>
								Complete Rep
							</button>
							<button 
								onClick={completeSet}
								style={{
									backgroundColor: '#9b59b6',
									color: 'white',
									border: 'none',
									padding: '10px 20px',
									borderRadius: '5px',
									marginRight: '10px',
									cursor: 'pointer'
								}}
							>
								Complete Set
							</button>
							<button 
								onClick={stopExercise}
								style={{
									backgroundColor: '#e74c3c',
									color: 'white',
									border: 'none',
									padding: '10px 20px',
									borderRadius: '5px',
									cursor: 'pointer'
								}}
							>
								Stop Exercise
							</button>
						</div>
					</div>
				)}

				{/* Main Content Grid */}
				<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
					{/* Assigned Exercises */}
					<div style={{
						backgroundColor: 'white',
						padding: '20px',
						borderRadius: '10px',
						boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
					}}>
						<h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>Your Exercises</h2>
						{exercises.length === 0 ? (
							<p style={{ color: '#7f8c8d', textAlign: 'center' }}>No exercises assigned yet</p>
						) : (
							<div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
								{exercises.map((exercise) => (
									<div key={exercise.id} style={{
										border: '1px solid #ecf0f1',
										borderRadius: '8px',
										padding: '15px',
										backgroundColor: '#f8f9fa'
									}}>
										<h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>
											{exercise.exercise.name}
										</h3>
										<p style={{ margin: '0 0 10px 0', color: '#7f8c8d' }}>
											{exercise.exercise.description}
										</p>
										<div style={{ marginBottom: '10px' }}>
											<strong>Target:</strong> {exercise.reps} reps × {exercise.sets} sets
										</div>
										<div style={{ marginBottom: '15px' }}>
											<strong>Instructions:</strong> {exercise.instructions}
										</div>
										<div style={{ marginBottom: '15px' }}>
											<strong>Status:</strong> 
											<span style={{ 
												color: exercise.status === 'completed' ? '#27ae60' : 
													   exercise.status === 'in_progress' ? '#f39c12' : '#7f8c8d',
												marginLeft: '5px'
											}}>
												{exercise.status}
											</span>
										</div>
										{!exerciseSession.isActive && (
											<button 
												onClick={() => startExercise(exercise)}
												style={{
													backgroundColor: '#27ae60',
													color: 'white',
													border: 'none',
													padding: '10px 20px',
													borderRadius: '5px',
													cursor: 'pointer',
													width: '100%'
												}}
											>
												Start Exercise
											</button>
										)}
									</div>
								))}
							</div>
						)}
					</div>

					{/* Camera and AI Analysis */}
					<div style={{
						backgroundColor: 'white',
						padding: '20px',
						borderRadius: '10px',
						boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
					}}>
						<h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>Exercise Analysis</h2>
						
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
						<div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
							{!cameraActive ? (
								<button 
									onClick={startCamera}
									style={{
										backgroundColor: '#3498db',
										color: 'white',
										border: 'none',
										padding: '10px 20px',
										borderRadius: '5px',
										cursor: 'pointer'
									}}
								>
									Start Camera
								</button>
							) : (
								<button 
									onClick={stopCamera}
									style={{
										backgroundColor: '#e74c3c',
										color: 'white',
										border: 'none',
										padding: '10px 20px',
										borderRadius: '5px',
										cursor: 'pointer'
									}}
								>
									Stop Camera
								</button>
							)}
							
							{cameraActive && !ws && (
								<button 
									onClick={startRealtime}
									style={{
										backgroundColor: '#9b59b6',
										color: 'white',
										border: 'none',
										padding: '10px 20px',
										borderRadius: '5px',
										cursor: 'pointer'
									}}
								>
									Start AI Analysis
								</button>
							)}
						</div>

						{/* AI Feedback */}
						<div style={{
							backgroundColor: '#ecf0f1',
							padding: '15px',
							borderRadius: '8px',
							marginBottom: '20px'
						}}>
							<h3 style={{ margin: '0 0 10px 0', color: '#2c3e50' }}>AI Analysis</h3>
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


