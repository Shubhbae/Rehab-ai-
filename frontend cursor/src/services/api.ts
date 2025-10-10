import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

let accessToken: string | null = null;

export const setAccessToken = (token: string) => {
	accessToken = token;
};

export const clearAccessToken = () => {
	accessToken = null;
};

const api = axios.create({
	baseURL: API_BASE,
	withCredentials: false
});

api.interceptors.request.use((config) => {
	if (accessToken) {
		config.headers = config.headers ?? {};
		config.headers.Authorization = `Bearer ${accessToken}`;
	}
	return config;
});

api.interceptors.response.use(
	(resp) => resp,
	(error) => {
		if (error?.response?.status === 401) {
			clearAccessToken();
			localStorage.removeItem('access_token');
		}
		return Promise.reject(error);
	}
);

export default api;


