
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function StartProcess({ user }: { user: any }) {
    const { processKey } = useParams();
    const navigate = useNavigate();
    const [formData, setFormData] = useState<any>({});

    // Pre-fill some data based on user
    useEffect(() => {
        if (user) {
            setFormData((prev: any) => ({
                ...prev,
                employee_name: user.full_name,
                // Logic for 'is_academic' is crucial for Leave Request routing
                is_academic: user.role_name === 'Academic Teacher'
            }));
        }
    }, [user]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        axios.post(`${API_URL}/api/process/start`, {
            process_key: processKey,
            user_id: user.id,
            initial_data: formData
        })
            .then(res => {
                alert(`Rozpoczęto proces (ID: ${res.data.id}). Przejdź do listy zadań.`);
                navigate('/worklist');
            })
            .catch(err => alert("Błąd startu: " + err));
    };

    const getTitle = () => {
        if (processKey === 'leave_request') return "Nowy Wniosek Urlopowy";
        if (processKey === 'change_employment') return "Wniosek o Zmianę Warunków Pracy";
        if (processKey === 'decorations') return "Wniosek o Odznaczenie";
        return "Rozpocznij Proces";
    };

    return (
        <div className="card" style={{ maxWidth: '800px', margin: '20px auto' }}>
            <h3>{getTitle()}</h3>
            <form onSubmit={handleSubmit}>

                {/* --- LEAVE REQUEST FORM --- */}
                {processKey === 'leave_request' && (
                    <>
                        <div className="form-group">
                            <label>Imię i Nazwisko Pracownika:</label>
                            <input value={formData.employee_name || ''} onChange={e => setFormData({ ...formData, employee_name: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Stanowisko:</label>
                            <input value={formData.employee_position || ''} onChange={e => setFormData({ ...formData, employee_position: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Rodzaj Urlopu:</label>
                            <select value={formData.leave_type || ''} onChange={e => setFormData({ ...formData, leave_type: e.target.value })} required>
                                <option value="">Wybierz...</option>
                                <option value="Recreational">Wypoczynkowy</option>
                                <option value="Sick">Chorobowy</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Data Startu:</label>
                            <input type="date" value={formData.leave_start_date || ''} onChange={e => setFormData({ ...formData, leave_start_date: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Czas trwania (dni):</label>
                            <input type="number" value={formData.leave_duration_days || ''} onChange={e => setFormData({ ...formData, leave_duration_days: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Data Wniosku:</label>
                            <input type="date" value={formData.request_date || new Date().toISOString().slice(0, 10)} onChange={e => setFormData({ ...formData, request_date: e.target.value })} />
                        </div>
                    </>
                )}

                {/* --- CHANGE EMPLOYMENT FORM --- */}
                {processKey === 'change_employment' && (
                    <>
                        <div className="form-group">
                            <label>Imię i Nazwisko Pracownika:</label>
                            <input value={formData.employee_name || ''} onChange={e => setFormData({ ...formData, employee_name: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Proponowane Warunki:</label>
                            <textarea rows={3} value={formData.proposed_conditions || ''} onChange={e => setFormData({ ...formData, proposed_conditions: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Uzasadnienie:</label>
                            <textarea rows={3} value={formData.change_justification || ''} onChange={e => setFormData({ ...formData, change_justification: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Data wejścia w życie:</label>
                            <input type="date" value={formData.change_effective_date || ''} onChange={e => setFormData({ ...formData, change_effective_date: e.target.value })} required />
                        </div>
                    </>
                )}

                {/* --- DECORATIONS FORM --- */}
                {processKey === 'decorations' && (
                    <>
                        <div className="form-group">
                            <label>Imię i Nazwisko Nominowanego:</label>
                            <input value={formData.employee_name || ''} onChange={e => setFormData({ ...formData, employee_name: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Jednostka Organizacyjna:</label>
                            <input value={formData.organizational_unit || ''} onChange={e => setFormData({ ...formData, organizational_unit: e.target.value })} required />
                        </div>
                        <div className="form-group">
                            <label>Typ Odznaczenia:</label>
                            <select value={formData.decoration_type || ''} onChange={e => setFormData({ ...formData, decoration_type: e.target.value })} required>
                                <option value="">Wybierz...</option>
                                <option value="Gold Medal for Long Service">Gold Medal for Long Service</option>
                                <option value="Silver Medal">Silver Medal</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Uzasadnienie:</label>
                            <textarea rows={4} value={formData.application_justification || ''} onChange={e => setFormData({ ...formData, application_justification: e.target.value })} required />
                        </div>
                    </>
                )}

                <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                    <button type="submit">Wyślij Wniosek</button>
                    <button type="button" className="btn-secondary" onClick={() => navigate('/worklist')}>Anuluj</button>
                </div>
            </form>
        </div>
    );
}
