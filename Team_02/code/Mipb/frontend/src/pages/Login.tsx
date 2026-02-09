
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface User {
    id: number;
    username: str;
    full_name: string;
    role_name: string;
}

export default function Login({ setUser }: { setUser: (u: User) => void }) {
    const [users, setUsers] = useState<User[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        axios.get(`${API_URL}/api/auth/users`)
            .then(res => setUsers(res.data))
            .catch(err => console.error(err));
    }, []);

    const handleLogin = (user: User) => {
        setUser(user);
        navigate('/worklist');
    };

    return (
        <div className="card" style={{ maxWidth: '800px', margin: '40px auto' }}>
            <h2>Wybierz użytkownika testowego (Rola)</h2>
            <p>Wybierz postać, aby zalogować się do systemu i wykonywać zadania przypisane do jej roli. <br />
                (Rygorystycznie wg pliku <em>Process to Roles Mapping.docx</em>)</p>

            <table>
                <thead>
                    <tr>
                        <th>Użytkownik</th>
                        <th>Rola</th>
                        <th>Akcja</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(u => (
                        <tr key={u.id}>
                            <td><strong>{u.full_name}</strong> <br /> <small style={{ color: '#666' }}>{u.username}</small></td>
                            <td>{u.role_name}</td>
                            <td>
                                <button onClick={() => handleLogin(u)}>Zaloguj</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px', textAlign: 'center' }}>
                <button onClick={() => navigate('/archive')} className="btn-secondary" style={{ width: '100%', background: '#7f8c8d' }}>
                    📂 Przeglądaj Zakończone Procesy (Dostęp Globalny)
                </button>
            </div>
        </div>
    );
}
