import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

type Toast = { id: number; type: 'success' | 'error' | 'info'; message: string };

type ToastContextValue = {
	toasts: Toast[];
	push: (t: Omit<Toast, 'id'>) => void;
	dismiss: (id: number) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const [toasts, setToasts] = useState<Toast[]>([]);

	const push = useCallback((t: Omit<Toast, 'id'>) => {
		const id = Date.now() + Math.random();
		setToasts((prev) => [...prev, { ...t, id }]);
		setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== id)), 4000);
	}, []);

	const dismiss = useCallback((id: number) => setToasts((prev) => prev.filter((x) => x.id !== id)), []);

	const value = useMemo(() => ({ toasts, push, dismiss }), [toasts, push, dismiss]);

	return (
		<ToastContext.Provider value={value}>
			{children}
			<div style={{ position: 'fixed', right: 16, bottom: 16, display: 'grid', gap: 8 }}>
				{toasts.map((t) => (
					<div key={t.id} style={{ padding: 12, background: t.type === 'success' ? '#D1FADF' : t.type === 'error' ? '#FFE4E6' : '#E0F2FE', borderRadius: 8 }}>
						{t.message}
					</div>
				))}
			</div>
		</ToastContext.Provider>
	);
};

export const useToast = (): ToastContextValue => {
	const ctx = useContext(ToastContext);
	if (!ctx) throw new Error('useToast must be used within ToastProvider');
	return ctx;
};







