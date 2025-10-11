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
	const [realtime, setRealtime] = useState<{ label?: string; confidence?: number; keypoints?: any[] }>({});
	const [cameraActive, setCameraActive] = useState(false);
	const [aiAnalysisActive, setAiAnalysisActive] = useState(false);
	const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
	const lastKpsRef = useRef<any[]>([]);

	const wsUrl = useMemo(() => {
		const base = (import.meta.env.VITE_API_WS_URL as string) ?? 'ws://127.0.0.1:8000';
		return `${base}/realtime/ws`;
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
			console.log('Requesting camera access...');
			const stream = await navigator.mediaDevices.getUserMedia({ 
				video: { width: 640, height: 480 }, 
				audio: false 
			});
			console.log('Camera stream obtained:', stream);
			if (videoRef.current) {
				videoRef.current.srcObject = stream;
				await videoRef.current.play();
				console.log('Video element playing, camera active');
				setCameraActive(true);
			} else {
				console.error('Video ref is null');
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

	const startExercise = async (exercise: AssignedExercise) => {
		console.log('Starting exercise:', exercise.exercise.name);
		setExerciseSession({
			isActive: true,
			currentExercise: exercise.exercise.name,
			repsCompleted: 0,
			setsCompleted: 0,
			aiFeedback: 'Starting exercise...',
			confidence: 0
		});
		
		// Start camera first
		await startCamera();
		
		// Wait a moment for camera to initialize, then start AI analysis
		setTimeout(() => {
			console.log('Starting AI analysis for exercise...');
			startRealtime();
		}, 1000);
	};

	const stopExercise = () => {
		console.log('Stopping exercise...');
		setExerciseSession({
			isActive: false,
			currentExercise: null,
			repsCompleted: 0,
			setsCompleted: 0,
			aiFeedback: '',
			confidence: 0
		});
		
		// Stop AI analysis first
		if (ws) {
			ws.close();
			setWs(null);
		}
		setAiAnalysisActive(false);
		setConnectionStatus('disconnected');
		setRealtime({});
		
		// Then stop camera
		stopCamera();
	};

	const startRealtime = () => {
		if (!videoRef.current || !canvasRef.current) {
			console.error('Video or canvas ref not available');
			return;
		}
		
		console.log('Starting AI Analysis...');
		console.log('WebSocket URL:', wsUrl);
		setAiAnalysisActive(true);
		setConnectionStatus('connecting');
		
		const socket = new WebSocket(wsUrl);
		setWs(socket);
		
		socket.onopen = () => {
			console.log('WebSocket connected - AI Analysis started!');
			setConnectionStatus('connected');
		};
		
		socket.onmessage = (ev) => {
			try {
				const data = JSON.parse(ev.data);
				console.log('WebSocket message received:', data);
				
				// Store keypoints for skeleton drawing
				if (data.keypoints) {
					console.log(`Received ${data.keypoints.length} keypoints for skeleton drawing`);
					lastKpsRef.current = data.keypoints;
					setRealtime(prev => ({ ...prev, keypoints: data.keypoints }));
				}
				
				// Handle prediction results
				if (data.label) {
					console.log(`AI Prediction: ${data.label} (${data.confidence})`);
					setRealtime(prev => ({ 
						...prev, 
						label: data.label, 
						confidence: data.confidence 
					}));
					
					// Update exercise session with AI feedback
					if (exerciseSession.isActive) {
						const exerciseName = data.label.replace('_', ' ').toUpperCase();
						const confidencePercent = data.confidence ? (data.confidence * 100).toFixed(1) : '0';
						
						let feedback = `Detected: ${exerciseName} (${confidencePercent}% confidence)`;
						
						// Add specific feedback based on confidence
						if (data.confidence && data.confidence > 0.8) {
							feedback += ' - Excellent form!';
						} else if (data.confidence && data.confidence > 0.6) {
							feedback += ' - Good form!';
						} else if (data.confidence && data.confidence > 0.4) {
							feedback += ' - Keep practicing!';
						} else {
							feedback += ' - Try to get in position';
						}
						
						setExerciseSession(prev => ({
							...prev,
							aiFeedback: feedback,
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
			setConnectionStatus('error');
		};
		
		socket.onclose = () => {
			console.log('WebSocket disconnected');
			setConnectionStatus('disconnected');
			setAiAnalysisActive(false);
		};
		
		const ctx = canvasRef.current.getContext('2d')!;
		const tick = () => {
			if (!videoRef.current || socket.readyState !== 1) {
				console.log('Tick skipped - video or socket not ready');
				return;
			}
			console.log('Tick running - processing frame');
			
			const w = videoRef.current.videoWidth;
			const h = videoRef.current.videoHeight;
			canvasRef.current!.width = w;
			canvasRef.current!.height = h;
			ctx.drawImage(videoRef.current, 0, 0, w, h);
			
			// Draw skeleton overlay if keypoints are available
			const kps = lastKpsRef.current;
			if (kps && Array.isArray(kps) && kps.length === 17) {
				console.log('Drawing skeleton with', kps.length, 'keypoints');
				// Define skeleton connections (bone structure)
				const edges: Array<[number, number]> = [
					[0,1],[0,2],[1,3],[2,4], // Head
					[5,6],[5,7],[7,9],[6,8],[8,10], // Torso & Arms
					[11,12],[5,11],[6,12],[11,13],[13,15],[12,14],[14,16] // Legs
				];
				
				ctx.save();
				ctx.lineWidth = 4;
				ctx.strokeStyle = '#2563eb'; // Blue for bones
				ctx.fillStyle = '#22c55e'; // Green for joints
				ctx.shadowColor = 'rgba(0,0,0,0.5)';
				ctx.shadowBlur = 2;
				
				// Draw bones (connections)
				for (const [a,b] of edges) {
					const ka = kps[a];
					const kb = kps[b];
					if (ka && kb && ka.score > 0.2 && kb.score > 0.2) { // Only draw if confidence is high enough
						ctx.beginPath();
						ctx.moveTo(ka.x * w, ka.y * h);
						ctx.lineTo(kb.x * w, kb.y * h);
						ctx.stroke();
					}
				}
				
				// Draw joints (keypoints)
				for (const kp of kps) {
					if (kp.score > 0.2) { // Only draw if confidence is high enough
						ctx.beginPath();
						ctx.arc(kp.x * w, kp.y * h, 6, 0, Math.PI * 2);
						ctx.fill();
					}
				}
				ctx.restore();
			}
			
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
						{realtime.label && (
							<div style={{ marginBottom: '15px', padding: '10px', backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: '8px' }}>
								<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
									<div>
										<strong>Detected Exercise:</strong> {realtime.label.replace('_', ' ').toUpperCase()}
									</div>
									<div>
										<strong>Accuracy:</strong> {realtime.confidence ? (realtime.confidence * 100).toFixed(1) + '%' : 'N/A'}
									</div>
								</div>
								{realtime.keypoints && (
									<div style={{ marginTop: '5px', fontSize: '14px' }}>
										<strong>Keypoints Detected:</strong> {realtime.keypoints.length}/17
									</div>
								)}
							</div>
						)}
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
                        <div className="h2" style={{ marginBottom: 20 }}>
							Exercise Analysis
							{aiAnalysisActive && (
								<span style={{ 
									marginLeft: '10px', 
									fontSize: '16px', 
									color: '#22c55e',
									animation: 'pulse 2s infinite'
								}}>
									🟢 LIVE
								</span>
							)}
						</div>
						
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
							<canvas 
								ref={canvasRef} 
								style={{ 
									position: 'absolute',
									top: 0,
									left: 0,
									width: '100%',
									height: '100%',
									pointerEvents: 'none',
									zIndex: 1
								}} 
							/>
							{!cameraActive && (
								<div style={{
									position: 'absolute',
									top: '50%',
									left: '50%',
									transform: 'translate(-50%, -50%)',
									color: 'white',
									textAlign: 'center',
									zIndex: 2
								}}>
									<div style={{ fontSize: '48px', marginBottom: '10px' }}>📹</div>
									<div>Camera not active</div>
								</div>
							)}
						</div>
						
						{/* Controls */}
                        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
							{!cameraActive ? (
                                <button className="btn btn-primary" onClick={startCamera}>
									📹 Start Camera
								</button>
							) : (
                                <button className="btn btn-danger" onClick={stopCamera}>
									📹 Stop Camera
								</button>
							)}
							
							{cameraActive && !aiAnalysisActive && (
                                <button className="btn btn-secondary" onClick={startRealtime}>
									🤖 Start AI Analysis
								</button>
							)}
							
							{aiAnalysisActive && (
                                <button className="btn btn-danger" onClick={() => {
									if (ws) {
										ws.close();
										setWs(null);
									}
									setAiAnalysisActive(false);
									setConnectionStatus('disconnected');
								}}>
									🤖 Stop AI Analysis
								</button>
							)}
						</div>
						
						{/* Connection Status */}
						{aiAnalysisActive && (
							<div style={{ 
								padding: '10px', 
								borderRadius: '8px', 
								marginBottom: '20px',
								backgroundColor: connectionStatus === 'connected' ? '#d5f4e6' : 
												connectionStatus === 'connecting' ? '#fff3cd' : '#f8d7da',
								color: connectionStatus === 'connected' ? '#155724' : 
									   connectionStatus === 'connecting' ? '#856404' : '#721c24'
							}}>
								<strong>AI Analysis Status:</strong> {
									connectionStatus === 'connected' ? '🟢 Connected - Tracking Active' :
									connectionStatus === 'connecting' ? '🟡 Connecting...' :
									connectionStatus === 'error' ? '🔴 Connection Error' :
									'⚪ Disconnected'
								}
							</div>
						)}

						{/* AI Feedback */}
                        <div className="card" style={{ background: 'var(--sky)' }}>
                            <h3 style={{ margin: '0 0 10px 0' }}>🤖 AI Analysis</h3>
							<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
								<div>
									<strong>Detected Exercise:</strong><br/>
									<span style={{ 
										fontSize: '18px', 
										fontWeight: 'bold',
										color: realtime.label ? '#2563eb' : '#6b7280'
									}}>
										{realtime.label ? realtime.label.replace('_', ' ').toUpperCase() : 'None'}
									</span>
								</div>
								<div>
									<strong>Confidence:</strong><br/>
									<span style={{ 
										fontSize: '18px', 
										fontWeight: 'bold',
										color: realtime.confidence && realtime.confidence > 0.7 ? '#22c55e' : 
											   realtime.confidence && realtime.confidence > 0.4 ? '#f59e0b' : '#6b7280'
									}}>
										{realtime.confidence ? (realtime.confidence * 100).toFixed(1) + '%' : 'N/A'}
									</span>
								</div>
							</div>
							<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
								<div>
									<strong>Keypoints:</strong> {realtime.keypoints ? realtime.keypoints.length : 0} / 17
								</div>
								<div>
									<strong>Status:</strong> {realtime.keypoints && realtime.keypoints.length > 10 ? '🟢 Tracking Active' : '🔴 No Detection'}
								</div>
							</div>
							{aiAnalysisActive && (
								<div style={{ 
									marginTop: '10px', 
									padding: '8px', 
									backgroundColor: 'rgba(37, 99, 235, 0.1)',
									borderRadius: '6px',
									fontSize: '14px'
								}}>
									💡 <strong>Tip:</strong> Make sure you're visible in the camera frame for best tracking results!
								</div>
							)}
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


