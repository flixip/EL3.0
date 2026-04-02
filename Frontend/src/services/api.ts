// Auto-Generated API | 请勿手动修改
import axios from 'axios';

export interface StandardOutParams {
    status?: number;
    msg?: string;
}

// GET /data
export async function data(): Promise<StandardOutParams> {
    return axios.get('/data');
}

// GET /
export async function index(): Promise<StandardOutParams> {
    return axios.get('/');
}

