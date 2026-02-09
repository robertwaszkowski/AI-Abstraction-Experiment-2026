
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { ProcessHistoryView } from './ProcessHistory';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function TaskForm({ user }: { user: any }) {
    const { taskId } = useParams();
    const navigate = useNavigate();
    const [task, setTask] = useState<any>(null);
    const [formData, setFormData] = useState<any>({});

    // Load Task
    useEffect(() => {
        // We need to fetch specific task details.
        // Re-using the list endpoint for now is not efficient but effective given constraints.
        // Ideally GET /api/process/tasks/{id} detail.
        // For now I'll use the user task list as I know the user has access.
        if (user && taskId) {
            axios.get(`${API_URL}/api/process/tasks/${user.id}`)
                .then(res => {
                    const found = res.data.find((t: any) => t.id === Number(taskId));
                    if (found) {
                        setTask(found);
                        // Initialize form with existing variables
                        setFormData(found.variables || {});
                    }
                });
        }
    }, [user, taskId]);

    const handleSubmit = (decision: string | null = null) => {
        const dataToSend = { ...formData };

        const processKey = task.process_definition_key;

        // Validation for Decorations Step 8 (Receive Decision) - User must input the decision
        if (processKey === 'decorations' && task.task_definition_key === 'Task_ReceiveDecision' && !formData.external_decision) {
            alert("Proszę wprowadzić otrzymaną decyzję (Przyznano/Odmowa)!");
            return;
        }

        // --- Leave Request Variables ---
        if (decision) {
            const processKey = task.process_definition_key;

            // --- Leave Request Variables ---
            if (processKey === 'leave_request') {
                if (task.name.includes("Head of O.U.")) dataToSend['head_ou_decision'] = formData.head_ou_decision || decision;
                if (task.name.includes("Review leave request")) dataToSend['pd_review_status'] = formData.pd_review_status || decision;
                if (task.name.includes("PRK")) dataToSend['prk_review_status'] = formData.prk_review_status || decision;
                if (task.name.includes("PRN")) dataToSend['prn_review_status'] = formData.prn_review_status || decision;
                if (task.name.includes("Rector") || task.name.includes("Chancellor")) {
                    dataToSend['final_decision'] = decision; // Buttons usually
                }
            }

            // --- Change of Employment Variables ---
            if (processKey === 'change_employment') {
                if (task.name.includes("Head of O.U.")) dataToSend['head_ou_review_status'] = formData.head_ou_review_status || decision;
                if (task.name.includes("PD")) dataToSend['pd_review_status'] = formData.pd_review_status || decision;
                if (task.name.includes("Quartermaster") || task.name.includes("KWE")) {
                    // KWE only has financial opinion, handled by form binding. If distinct status needed:
                    // dataToSend['kwe_review_status'] = decision; // Removed per user request
                }
                if (task.name.includes("PRK")) dataToSend['prk_opinion'] = formData.prk_opinion || decision;
                if (task.name.includes("PRN")) dataToSend['prn_opinion'] = formData.prn_opinion || decision;
                if (task.name.includes("Make decision") && (task.name.includes("Rector") || task.name.includes("RKR"))) {
                    dataToSend['final_decision'] = formData.final_decision || decision;
                    dataToSend['rkr_decision'] = formData.final_decision || decision;
                }
            }

            // --- Decorations Variables ---
            if (processKey === 'decorations') {
                if (task.task_definition_key === 'Task_SubmitApplication') dataToSend['head_ou_opinion'] = formData.head_ou_opinion || decision;
                if (task.name.includes("Present")) {
                    // PD tasks
                    if (formData.pd_opinion) dataToSend['pd_opinion'] = formData.pd_opinion;
                }
                if (task.name.includes("Review applications") && task.name.includes("PRK")) {
                    dataToSend['prk_opinion'] = formData.prk_opinion || decision;
                }
                if (task.name.includes("Make decision") && task.name.includes("Rector")) dataToSend['rkr_decision'] = decision;
                // Step 8: Receive Decision - The user enters the external decision here
                if (task.task_definition_key === 'Task_ReceiveDecision') dataToSend['external_decision'] = formData.external_decision;
                // Step 9: Enter to Register
                if (task.task_definition_key === 'Task_EnterToRegister') dataToSend['award_grant_date'] = formData.award_grant_date;
            }
        }

        axios.post(`${API_URL}/api/process/tasks/${task.id}/complete`, {
            user_id: user.id,
            data: dataToSend
        })
            .then(() => {
                alert("Zadanie wykonane!");
                navigate('/worklist');
            })
            .catch(err => alert("Błąd: " + err));
    };

    if (!task) return <div>Ładowanie...</div>;

    // Helpers for form rendering
    const processKey = task.process_definition_key; // Updated to use key directly
    // Ah, my task router response includes 'task_definition_key' but not 'process_definition_key' directly... 
    // Wait, I can deduce or add it to backend. 
    // Actually, let's just use variable heuristic or task naming.

    // OR better: The "ProcessHistory" component is embedded below.

    return (
        <div>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
                <div className="card" style={{ flex: 1 }}>
                    <h3>{task.name}</h3>
                    <p><em>{task.assignee_role}</em></p>

                    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>

                        {/* --- Common Read-Only Context --- */}
                        {(formData.employee_name) && (
                            <div className="form-group">
                                <label>Pracownik:</label>
                                <input value={formData.employee_name} disabled />
                            </div>
                        )}


                        {/* --- Leave Request Fields --- */}
                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_ReviewAndForward_HeadOU' || task.task_definition_key.includes('Start')) && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} onChange={e => setFormData({ ...formData, employee_name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Stanowisko:</label>
                                    <input value={formData.employee_position || ''} onChange={e => setFormData({ ...formData, employee_position: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Rodzaj Urlopu:</label>
                                    <select value={formData.leave_type || ''} onChange={e => setFormData({ ...formData, leave_type: e.target.value })}>
                                        <option value="">Wybierz...</option>
                                        <option value="Recreational">Wypoczynkowy</option>
                                        <option value="Sick">Chorobowy</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Data Startu:</label>
                                    <input type="date" value={formData.leave_start_date || ''} onChange={e => setFormData({ ...formData, leave_start_date: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Dni:</label>
                                    <input type="number" value={formData.leave_duration_days || ''} onChange={e => setFormData({ ...formData, leave_duration_days: e.target.value })} />
                                </div>
                                {/* Head OU Decision for Leave Request */}
                                {task.task_definition_key === 'Task_ReviewAndForward_HeadOU' && (
                                    <div className="form-group">
                                        <label>Decyzja Kierownika JO (Head of O.U. Decision):</label>
                                        <select
                                            value={formData.head_ou_decision || ''}
                                            onChange={e => setFormData({ ...formData, head_ou_decision: e.target.value })}
                                        >
                                            <option value="">Wybierz...</option>
                                            <option value="Approved">Zatwierdź / Approved</option>
                                            <option value="Rejected">Odrzuć / Rejected</option>
                                        </select>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Leave Request: PD Review */}
                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_ReviewApplication_PD') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Kierownika JO:</label>
                                    <input value={formData.head_ou_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Czy Nauczyciel Akademicki?</label>
                                    <select
                                        value={String(formData.is_academic)}
                                        onChange={e => setFormData({ ...formData, is_academic: e.target.value === 'true' })}
                                    >
                                        <option value="false">Nie</option>
                                        <option value="true">Tak</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PD (PD Review Status):</label>
                                    <select
                                        value={formData.pd_review_status || ''}
                                        onChange={e => setFormData({ ...formData, pd_review_status: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Confirmed">Potwierdzono / Confirmed</option>
                                        <option value="Rejected">Odrzucono / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Leave Request: PRK Review */}
                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_Review_PRK') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Kierownika JO:</label>
                                    <input value={formData.head_ou_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PRK (PRK Review Status):</label>
                                    <select
                                        value={formData.prk_review_status || ''}
                                        onChange={e => setFormData({ ...formData, prk_review_status: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Leave Request: PRN Review */}
                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_Review_PRN') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PRK:</label>
                                    <input value={formData.prk_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Kierownika JO:</label>
                                    <input value={formData.head_ou_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PRN (PRN Review Status):</label>
                                    <select
                                        value={formData.prn_review_status || ''}
                                        onChange={e => setFormData({ ...formData, prn_review_status: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Końcowa (Final Decision):</label>
                                    <select
                                        value={formData.final_decision || ''}
                                        onChange={e => setFormData({ ...formData, final_decision: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_ReviewApplication_PD' && formData.leave_type) && (
                            <div className="form-group">
                                <label style={{ color: 'red' }}>Czy jest Nauczycielem Akademickim? (Wymusza ścieżkę Rektorską)</label>
                                <select value={formData.is_academic ? 'true' : 'false'} onChange={e => setFormData({ ...formData, is_academic: e.target.value === 'true' })}>
                                    <option value="false">Nie</option>
                                    <option value="true">Tak</option>
                                </select>
                            </div>
                        )}

                        {/* --- Change of Employment Fields --- */}
                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_ReviewAndForward_HeadOU' || task.task_definition_key.includes('Start')) && (
                            <>
                                {/* Employee Name removed (duplicate) */}
                                <div className="form-group">
                                    <label>Proponowane Warunki:</label>
                                    <textarea rows={3} value={formData.proposed_conditions || ''} onChange={e => setFormData({ ...formData, proposed_conditions: e.target.value })} disabled={task.task_definition_key !== 'StartEvent_1'} />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={3} value={formData.change_justification || ''} onChange={e => setFormData({ ...formData, change_justification: e.target.value })} disabled={task.task_definition_key !== 'StartEvent_1'} />
                                </div>
                                <div className="form-group">
                                    <label>Data wejścia w życie:</label>
                                    <input type="date" value={formData.change_effective_date || ''} onChange={e => setFormData({ ...formData, change_effective_date: e.target.value })} disabled={task.task_definition_key !== 'StartEvent_1'} />
                                </div>
                                {task.task_definition_key === 'Task_ReviewAndForward_HeadOU' && (
                                    <div className="form-group">
                                        <label>Opinia Kierownika JO (Head of O.U. Review Status):</label>
                                        <select
                                            value={formData.head_ou_review_status || ''}
                                            onChange={e => setFormData({ ...formData, head_ou_review_status: e.target.value })}
                                        >
                                            <option value="">Wybierz...</option>
                                            <option value="Approved">Zatwierdź / Approved</option>
                                            <option value="Rejected">Odrzuć / Rejected</option>
                                        </select>
                                    </div>
                                )}
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_ReviewApplication_PD') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Proponowane Warunki:</label>
                                    <textarea rows={3} value={formData.proposed_conditions || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={3} value={formData.change_justification || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Kierownika JO (Head of O.U. Review Status):</label>
                                    <input value={formData.head_ou_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label style={{ color: 'red', fontWeight: 'bold' }}>Czy jest Nauczycielem Akademickim? (Wymusza ścieżkę Rektorską)</label>
                                    <select
                                        value={formData.is_academic !== undefined ? (formData.is_academic ? 'true' : 'false') : ''}
                                        onChange={e => setFormData({ ...formData, is_academic: e.target.value === 'true' })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="false">Nie</option>
                                        <option value="true">Tak</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PD (PD Review Status):</label>
                                    <select
                                        value={formData.pd_review_status || ''}
                                        onChange={e => setFormData({ ...formData, pd_review_status: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Confirmed">Potwierdzono / Confirmed</option>
                                        <option value="Rejected">Odrzucono / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_Review_KWE') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Proponowane Warunki:</label>
                                    <textarea rows={3} value={formData.proposed_conditions || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={3} value={formData.change_justification || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Kierownika JO:</label>
                                    <input value={formData.head_ou_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Finansowa KWE:</label>
                                    <select
                                        value={formData.kwe_financial_opinion || ''}
                                        onChange={e => setFormData({ ...formData, kwe_financial_opinion: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Funds Available">Środki Dostępne / Funds Available</option>
                                        <option value="Funds Not Available">Brak Środków / Funds Not Available</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_Review_PRK') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Proponowane Warunki:</label>
                                    <textarea rows={3} value={formData.proposed_conditions || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Kierownika JO:</label>
                                    <input value={formData.head_ou_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Finansowa KWE:</label>
                                    <input value={formData.kwe_financial_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label> Opinia PRK (PRK Opinion):</label>
                                    <select
                                        value={formData.prk_opinion || ''}
                                        onChange={e => setFormData({ ...formData, prk_opinion: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_Review_PRN') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <textarea rows={3} value={formData.proposed_conditions || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Kierownika JO:</label>
                                    <input value={formData.head_ou_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Finansowa KWE:</label>
                                    <input value={formData.kwe_financial_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PRK (VRE):</label>
                                    <input value={formData.prk_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PRN (PRN Opinion):</label>
                                    <select
                                        value={formData.prn_opinion || ''}
                                        onChange={e => setFormData({ ...formData, prn_opinion: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Leave Request: RKR Decision */}
                        {processKey === 'leave_request' && (task.task_definition_key === 'Task_MakeDecision_RKR') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Kierownika JO:</label>
                                    <input value={formData.head_ou_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PRK:</label>
                                    <input value={formData.prk_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Status Przeglądu PRN:</label>
                                    <input value={formData.prn_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Końcowa (Final Decision):</label>
                                    <select
                                        value={formData.final_decision || ''}
                                        onChange={e => setFormData({ ...formData, final_decision: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_MakeDecision_RKR') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Pracownika:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Proponowane Warunki:</label>
                                    <textarea rows={3} value={formData.proposed_conditions || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Kierownika JO:</label>
                                    <input value={formData.head_ou_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PD:</label>
                                    <input value={formData.pd_review_status || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia Finansowa KWE:</label>
                                    <input value={formData.kwe_financial_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PRK (VRE):</label>
                                    <input value={formData.prk_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PRN (VRScientific):</label>
                                    <input value={formData.prn_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Końcowa (Final Decision):</label>
                                    <select
                                        value={formData.final_decision || ''}
                                        onChange={e => setFormData({ ...formData, final_decision: e.target.value })}
                                    >
                                        <option value="">Wybierz...</option>
                                        <option value="Approved">Zatwierdź / Approved</option>
                                        <option value="Rejected">Odrzuć / Rejected</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_ImplementAndPrepare') && (
                            <>
                                <div className="form-group">
                                    <label>Decyzja Rektora:</label>
                                    <input value={formData.rkr_decision || formData.final_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Checklista (Implementacja):</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '5px' }}>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={!!formData.checklist_impl_inform_head}
                                                onChange={e => setFormData({ ...formData, checklist_impl_inform_head: e.target.checked })}
                                            /> Poinformuj Kierownika JO o decyzji
                                        </label>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={!!formData.checklist_impl_hr_system}
                                                onChange={e => setFormData({ ...formData, checklist_impl_hr_system: e.target.checked })}
                                            /> Wprowadź zmiany w systemie kadrowym
                                        </label>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={!!formData.checklist_impl_prepare_docs}
                                                onChange={e => setFormData({ ...formData, checklist_impl_prepare_docs: e.target.checked })}
                                            /> Przygotuj dokumenty potwierdzające
                                        </label>
                                    </div>
                                </div>
                            </>
                        )}

                        {processKey === 'change_employment' && (task.task_definition_key === 'Task_HandOverAndArchive') && (
                            <>
                                <div className="form-group">
                                    <label>Wykonane Zadania (Implementacja):</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '5px' }}>
                                        <label>
                                            <input type="checkbox" checked={String(formData.checklist_impl_inform_head) === 'true' || formData.checklist_impl_inform_head === true} disabled /> Poinformuj Kierownika JO o decyzji
                                        </label>
                                        <label>
                                            <input type="checkbox" checked={String(formData.checklist_impl_hr_system) === 'true' || formData.checklist_impl_hr_system === true} disabled /> Wprowadź zmiany w systemie kadrowym
                                        </label>
                                        <label>
                                            <input type="checkbox" checked={String(formData.checklist_impl_prepare_docs) === 'true' || formData.checklist_impl_prepare_docs === true} disabled /> Przygotuj dokumenty potwierdzające
                                        </label>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Checklista (Archiwizacja):</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '5px' }}>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={!!formData.checklist_arch_handover}
                                                onChange={e => setFormData({ ...formData, checklist_arch_handover: e.target.checked })}
                                            /> Przekaż dokumenty pracownikowi
                                        </label>
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={!!formData.checklist_arch_attach_copy}
                                                onChange={e => setFormData({ ...formData, checklist_arch_attach_copy: e.target.checked })}
                                            /> Dołącz kopię do akt osobowych
                                        </label>
                                    </div>
                                </div>
                            </>
                        )}

                        {/* --- Decorations Fields --- */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_SubmitApplication') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Nominowanego:</label>
                                    <input value={formData.employee_name || ''} onChange={e => setFormData({ ...formData, employee_name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Jednostka Organizacyjna:</label>
                                    <input value={formData.organizational_unit || ''} onChange={e => setFormData({ ...formData, organizational_unit: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Typ Odznaczenia:</label>
                                    <select value={formData.decoration_type || ''} onChange={e => setFormData({ ...formData, decoration_type: e.target.value })}>
                                        <option value="">Wybierz...</option>
                                        <option value="Gold Medal for Long Service">Gold Medal for Long Service</option>
                                        <option value="Silver Medal">Silver Medal</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={4} value={formData.application_justification || ''} onChange={e => setFormData({ ...formData, application_justification: e.target.value })} />
                                </div>

                            </>
                        )}

                        {/* Decorations: PD Review */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_PresentApplicationsForAcceptance') && (
                            <>
                                <div className="form-group">
                                    <label>Jednostka Organizacyjna:</label>
                                    <input value={formData.organizational_unit || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Typ Odznaczenia:</label>
                                    <input value={formData.decoration_type || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={4} value={formData.application_justification || ''} disabled />
                                </div>
                            </>
                        )}

                        {/* Decorations: PRK Review */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_ReviewApplications') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Nominowanego:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Jednostka Organizacyjna:</label>
                                    <input value={formData.organizational_unit || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Typ Odznaczenia:</label>
                                    <input value={formData.decoration_type || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={4} value={formData.application_justification || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Reviewer Opinion:</label>
                                    <select value={formData.prk_opinion || ''} onChange={e => setFormData({ ...formData, prk_opinion: e.target.value })}>
                                        <option value="">Wybierz...</option>
                                        <option value="Strongly support">Strongly support</option>
                                        <option value="Support">Support</option>
                                        <option value="Do not support">Do not support</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Decorations: PD Present to RKR */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_PresentApplicationsToRKR') && (
                            <>
                                <div className="form-group">
                                    <label>Imię i Nazwisko Nominowanego:</label>
                                    <input value={formData.employee_name || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Jednostka Organizacyjna:</label>
                                    <input value={formData.organizational_unit || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Typ Odznaczenia:</label>
                                    <input value={formData.decoration_type || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={4} value={formData.application_justification || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Opinia PRK:</label>
                                    <input value={formData.prk_opinion || ''} disabled />
                                </div>
                                {/* No decision needed here, just forward */}
                            </>
                        )}

                        {/* Decorations: RKR Decision */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_MakeDecision') && (
                            <>
                                <div className="form-group">
                                    <label>Jednostka Organizacyjna:</label>
                                    <input value={formData.organizational_unit || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Typ Odznaczenia:</label>
                                    <input value={formData.decoration_type || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Uzasadnienie:</label>
                                    <textarea rows={4} value={formData.application_justification || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Reviewer Opinion:</label>
                                    <input value={formData.prk_opinion || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Decyzja Rektora (RKR Decision):</label>
                                    <select value={formData.rkr_decision || ''} onChange={e => setFormData({ ...formData, rkr_decision: e.target.value })}>
                                        <option value="">Wybierz...</option>
                                        <option value="Accepted">Zaakceptuj / Accept</option>
                                        <option value="Rejected">Odrzuć / Reject</option>
                                    </select>
                                </div>
                            </>
                        )}

                        {/* Decorations: PD Forward to MPD */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_ForwardApplicationsToMPD') && (
                            <>
                                <div className="form-group">
                                    <label>Decyzja Rektora:</label>
                                    <input value={formData.rkr_decision || ''} disabled />
                                </div>
                            </>
                        )}

                        {/* Decorations: MPD Handle Applications */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_HandleApplicationsExternal') && (
                            <>
                                <div className="form-group">
                                    <label>Status:</label>
                                    <p>Wniosek jest przetwarzany przez organ zewnętrzny. Oczekuj na decyzję.</p>
                                </div>
                            </>
                        )}

                        {/* Decorations: PD Receive Decision */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_ReceiveDecision') && (
                            <>
                                <div className="form-group">
                                    <label>Otrzymana Decyzja Zewnętrzna / Received External Decision:</label>
                                    <select value={formData.external_decision || ''} onChange={e => setFormData({ ...formData, external_decision: e.target.value })}>
                                        <option value="">Wybierz...</option>
                                        <option value="Awarded">Przyznano / Awarded</option>
                                        <option value="Refused">Odmowa / Refused</option>
                                    </select>
                                </div>
                            </>

                        )}

                        {/* Decorations: PD Enter to Register */}
                        {processKey === 'decorations' && (task.task_definition_key === 'Task_EnterToRegister') && (
                            <>
                                <div className="form-group">
                                    <label>Decyzja Zewnętrzna:</label>
                                    <input value={formData.external_decision || ''} disabled />
                                </div>
                                <div className="form-group">
                                    <label>Data Nadania Nagrody / Award Grant Date:</label>
                                    <input type="date" value={formData.award_grant_date || ''} onChange={e => setFormData({ ...formData, award_grant_date: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label>Status Rejestracji:</label>
                                    <p>Wprowadź odznaczenie do rejestru.</p>
                                </div>
                            </>
                        )}

                        {/* --- Common Action Buttons --- */}
                        <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                            {/* Dynamic Buttons based on Task Type */}
                            {task.task_definition_key !== 'Task_MakeDecision' && (
                                <>
                                    <button type="button" onClick={() => handleSubmit('Approved')}>Zatwierdź / Approved</button>
                                    <button type="button" className="btn-danger" onClick={() => handleSubmit('Rejected')}>Odrzuć / Rejected</button>
                                </>
                            )}

                            {(task.task_definition_key.includes('Enter') ||
                                task.task_definition_key.includes('Implement') ||
                                task.task_definition_key.includes('HandOver')) && (
                                    <button type="button" onClick={() => handleSubmit('Completed')}>Wykonaj / Complete</button>
                                )}
                            {(task.task_definition_key === 'Task_MakeDecision' && !task.task_definition_key.includes('Chancellor')) && (
                                // RKR Decision for Decorations requires specific values for Gateway
                                <>
                                    <button type="button" onClick={() => handleSubmit('Accepted')}>Accepted</button>
                                    <button type="button" className="btn-danger" onClick={() => handleSubmit('Rejected')}>Rejected</button>
                                </>
                            )}
                        </div>
                    </form>
                </div>

                <div style={{ flex: 1 }}>
                    {task && <ProcessHistoryView processInstanceId={task.process_instance_id} />}
                </div>

            </div>
        </div >
    );
}
