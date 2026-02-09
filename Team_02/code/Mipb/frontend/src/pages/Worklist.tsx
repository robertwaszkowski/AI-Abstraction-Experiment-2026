
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Task {
    id: number;
    name: string;
    assignee_role: string;
    created_at: string;
    process_instance_id: number;
    task_definition_key: string;
    variables: any;
}

export default function Worklist({ user }: { user: any }) {
    const [tasks, setTasks] = useState<Task[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        if (!user) {
            navigate('/');
            return;
        }
        fetchTasks();
    }, [user]);

    const fetchTasks = () => {
        axios.get(`${API_URL}/api/process/tasks/${user.id}`)
            .then(res => setTasks(res.data))
            .catch(err => console.error(err));
    };

    const startProcess = (key: string) => {
        navigate(`/start/${key}`);
    };

    return (
        <div>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <button className="btn-secondary" onClick={() => startProcess('leave_request')}>+ Nowy Wniosek Urlopowy</button>
                <button className="btn-secondary" onClick={() => startProcess('change_employment')}>+ Zmiana Warunków Pracy</button>
                <button className="btn-secondary" onClick={() => startProcess('decorations')}>+ Wniosek o Odznaczenie</button>
                <button className="btn-secondary" onClick={() => fetchTasks()}>Odśwież</button>
            </div>

            <div className="card">
                <h3>Moje Zadania (Worklist)</h3>
                <p>Zalogowany jako: <strong>{user.full_name}</strong> ({user.role_name})</p>
                {tasks.length === 0 ? <p>Brak zadań w Twojej skrzynce.</p> : (
                    <table>
                        <thead>
                            <tr>
                                <th>ID Zadania</th>
                                <th>Nazwa Zadania</th>
                                <th>Przypisane do Roli</th>
                                <th>Data utworzenia</th>
                                <th>Akcja</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map(t => (
                                <tr key={t.id}>
                                    <td>{t.id}</td>
                                    <td>{t.name}</td>
                                    <td>{t.assignee_role || 'Personalnie'}</td>
                                    <td>{new Date(t.created_at).toLocaleString()}</td>
                                    <td>
                                        <button onClick={() => navigate(`/task/${t.id}`)}>Otwórz</button>
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
