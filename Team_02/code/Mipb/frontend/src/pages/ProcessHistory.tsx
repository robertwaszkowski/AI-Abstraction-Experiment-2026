
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Page Component (Default Export)
export default function ProcessHistory() {
    const { processId } = useParams();
    if (!processId) return <div>Brak ID procesu w adresie URL.</div>;
    return <ProcessHistoryView processInstanceId={Number(processId)} defaultVisible={true} />;
}

// View Component (Named Export)
interface Props {
    processInstanceId?: number;
    defaultVisible?: boolean;
}

export function ProcessHistoryView({ processInstanceId, defaultVisible = false }: Props) {
    const [data, setData] = useState<any>(null);
    const [isVisible, setIsVisible] = useState(defaultVisible);

    useEffect(() => {
        if (processInstanceId) {
            axios.get(`${API_URL}/api/process/history/${processInstanceId}`)
                .then(res => setData(res.data))
                .catch(err => console.error(err));
        }
    }, [processInstanceId]);

    // If invisible, check if we should even show the button (only if COMPLETED)
    if (!isVisible) {
        // Validation for "End of Process Only":
        // If data is active (not completed), hide everything.
        if (data && data.status !== 'COMPLETED') {
            return null;
        }

        // If data not loaded yet, wait silently or return null
        if (!data) return null;

        // If completed, show the toggle button
        return (
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
                <button
                    onClick={() => setIsVisible(true)}
                    className="btn-secondary"
                    style={{ width: '100%', padding: '15px', background: '#27ae60', border: 'none', color: 'white' }}
                >
                    ⬇ Proces Zakończony - Pokaż Podsumowanie (Weryfikacja)
                </button>
            </div>
        );
    }

    // If visible (clicked or defaultVisible=true)
    if (!data) return <div className="card">Ładowanie historii...</div>;

    const { logs, final_variables, status } = data;

    return (
        <div className="card" style={{ marginTop: '20px' }}>
            <div style={{ textAlign: 'right', marginBottom: '10px' }}>
                <button onClick={() => setIsVisible(false)} style={{ background: 'transparent', color: '#7f8c8d', border: 'none', cursor: 'pointer' }}>
                    Ukryj ⬆
                </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3>Historia Procesu</h3>
                <span style={{
                    padding: '5px 10px',
                    borderRadius: '4px',
                    background: status === 'COMPLETED' ? '#27ae60' : '#f39c12',
                    color: 'white',
                    fontWeight: 'bold'
                }}>
                    {status}
                </span>
            </div>

            {/* --- PODSUMOWANIE ZMIENNYCH --- */}
            <div style={{ background: '#f8f9fa', padding: '10px', margin: '10px 0', borderLeft: '4px solid #3498db' }}>
                <h4>Podsumowanie (Zmienne Procesu)</h4>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {final_variables && Object.entries(final_variables).map(([key, val]: [string, any]) => (
                        <li key={key} style={{ marginBottom: '4px' }}>
                            <strong>{key}:</strong> {val ? val.toString() : 'null'}
                        </li>
                    ))}
                </ul>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Czas</th>
                        <th>Użytkownik</th>
                        <th>Akcja</th>
                        <th>Komentarz / Szczegóły</th>
                    </tr>
                </thead>
                <tbody>
                    {logs && logs.map((l: any, idx: number) => (
                        <tr key={idx}>
                            <td>{new Date(l.timestamp).toLocaleString()}</td>
                            <td>{l.user_name || 'System'}</td>
                            <td>{l.action}</td>
                            <td>{l.comment}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
