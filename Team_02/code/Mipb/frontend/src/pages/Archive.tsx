
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProcessInstance {
    id: number;
    process_definition_key: string;
    status: string;
    created_at: string;
}

export default function Archive() {
    const [completedProcesses, setCompletedProcesses] = useState<ProcessInstance[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        axios.get(`${API_URL}/api/process/instances`)
            .then(res => {
                const finished = res.data.filter((p: any) => p.status === 'COMPLETED' || p.status === 'REJECTED');
                setCompletedProcesses(finished);
            })
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ maxWidth: '800px', margin: '40px auto' }}>
            <button
                onClick={() => navigate('/')}
                className="btn-secondary"
                style={{ marginBottom: '20px', background: '#95a5a6' }}
            >
                ⬅ Wróć do Logowania
            </button>

            <div className="card">
                <h3>Zakończone Procesy (Archiwum)</h3>
                <p>Lista wszystkich zakończonych procesów w systemie. (Weryfikacja Krok 9)</p>
                {completedProcesses.length === 0 ? <p>Brak zakończonych procesów.</p> : (
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Proces</th>
                                <th>Status</th>
                                <th>Utworzono</th>
                                <th>Podgląd</th>
                            </tr>
                        </thead>
                        <tbody>
                            {completedProcesses.map(p => (
                                <tr key={p.id}>
                                    <td>{p.id}</td>
                                    <td>{p.process_definition_key}</td>
                                    <td style={{ fontWeight: 'bold', color: p.status === 'COMPLETED' ? 'green' : 'red' }}>{p.status}</td>
                                    <td>{new Date(p.created_at).toLocaleString()}</td>
                                    <td>
                                        <button onClick={() => navigate(`/process/${p.id}/history`)}>Szczegóły</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
