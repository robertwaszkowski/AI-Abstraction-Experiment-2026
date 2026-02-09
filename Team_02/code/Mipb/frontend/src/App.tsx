
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Login from './pages/Login';
import Worklist from './pages/Worklist';
import StartProcess from './pages/StartProcess';
import TaskForm from './pages/TaskForm';
import ProcessHistory from './pages/ProcessHistory';
import Archive from './pages/Archive';
import { useState } from 'react';

function App() {
    const [user, setUser] = useState<any>(null);

    const handleLogout = () => {
        setUser(null);
        window.location.href = '/';
    };

    return (
        <Router>
            <div>
                <nav style={{ background: '#2c3e50', padding: '15px', color: 'white' }}>
                    <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Link to="/" style={{ color: 'white', textDecoration: 'none', fontSize: '1.2em', fontWeight: 'bold' }}>
                            Minimal Process Platform
                        </Link>
                        {user && (
                            <div style={{ display: 'flex', gap: '20px' }}>
                                <span>Zalogowano jako: <strong>{user.full_name}</strong> ({user.role_name})</span>
                                <Link to="/worklist" style={{ color: '#3498db', textDecoration: 'none' }}>Moje Zadania</Link>
                                <button onClick={handleLogout} style={{ background: 'transparent', border: '1px solid white', padding: '5px 10px' }}>Wyloguj</button>
                            </div>
                        )}
                    </div>
                </nav>

                <div className="container" style={{ marginTop: '20px' }}>
                    <Routes>
                        <Route path="/" element={<Login setUser={setUser} />} />
                        <Route path="/worklist" element={<Worklist user={user} />} />
                        <Route path="/start/:processKey" element={<StartProcess user={user} />} />
                        <Route path="/task/:taskId" element={<TaskForm user={user} />} />
                        <Route path="/process/:processId/history" element={<ProcessHistory />} />
                        <Route path="/archive" element={<Archive />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
}

export default App;
