'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ProcessInstance, ProcessType, ProcessStatus, AnyProcessData, ProcessStep } from '@/lib/types/processes';
import { getNextState, getInitialStep, getAssigneeRoleForStep } from '@/lib/workflows';
import { useAuth } from '@/hooks/useAuth';
import { getProcesses, createProcess, updateProcess } from '@/actions/process';
import { useEffect } from 'react';

interface ProcessContextType {
    processes: ProcessInstance[];
    startProcess: (type: ProcessType, initialData: AnyProcessData) => void;
    completeTask: (processId: string, updatedData: AnyProcessData) => void;
}

const ProcessContext = createContext<ProcessContextType | undefined>(undefined);

export const ProcessProvider = ({ children }: { children: ReactNode }) => {
    const [processes, setProcesses] = useState<ProcessInstance[]>([]);
    const { user } = useAuth();

    useEffect(() => {
        const loadProcesses = async () => {
            const loaded = await getProcesses();
            setProcesses(loaded as ProcessInstance[]);
        };
        loadProcesses();
    }, []);

    const startProcess = (type: ProcessType, initialData: AnyProcessData) => {
        const initialStep = getInitialStep(type);
        // The form submission counts as completing the 'SUBMIT' step.
        // So we immediately calculate the NEXT state from the initial step.

        // 1. Create base data with metadata
        const dataWithMeta = {
            ...initialData,
            initiatorUsername: user?.username || 'unknown',
            startDate: new Date().toISOString(),
        };

        // 2. Calculate the transition from the initial step
        const transition = getNextState(initialStep, dataWithMeta);

        const newProcess: ProcessInstance = {
            id: '', // Will be set by server
            type,
            status: transition.nextStatus,
            currentStep: transition.nextStep,
            assignedRole: transition.nextAssigneeRole,
            assignedUser: undefined,
            data: dataWithMeta,
            history: [
                {
                    step: 'INIT',
                    user: user?.username || 'system',
                    timestamp: new Date().toISOString(),
                    action: 'Started Process',
                },
                {
                    step: initialStep,
                    user: user?.username || 'unknown',
                    timestamp: new Date().toISOString(),
                    action: 'Submitted Request',
                }
            ],
        };

        // Optimistic update
        const tempId = Math.random().toString(36).substring(7);
        setProcesses((prev) => [{ ...newProcess, id: tempId }, ...prev]);

        createProcess(newProcess).then((created) => {
            setProcesses((prev) => prev.map(p => p.id === tempId ? (created as ProcessInstance) : p));
        });
    };

    const completeTask = (processId: string, updatedData: AnyProcessData) => {
        setProcesses((prev) => {
            const index = prev.findIndex(p => p.id === processId);
            if (index === -1) return prev;
            const proc = prev[index];
            if (!proc.currentStep) return prev;

            // Merge new data with existing data to ensure getNextState has full context
            const mergedData = { ...proc.data, ...updatedData };
            const transition = getNextState(proc.currentStep, mergedData);

            const updatedProcess = {
                ...proc,
                data: mergedData,
                currentStep: transition.nextStep,
                status: transition.nextStatus,
                assignedRole: transition.nextAssigneeRole,
                history: [
                    ...proc.history,
                    {
                        step: proc.currentStep || 'UNKNOWN',
                        user: user?.username || 'unknown',
                        timestamp: new Date().toISOString(),
                        action: 'Completed Task',
                    },
                ],
            };

            // Trigger server update
            updateProcess(processId, updatedProcess);

            // Return new state
            const newProcesses = [...prev];
            newProcesses[index] = updatedProcess;
            return newProcesses;
        });
    };

    return (
        <ProcessContext.Provider value={{ processes, startProcess, completeTask }}>
            {children}
        </ProcessContext.Provider>
    );
};

export const useProcesses = () => {
    const context = useContext(ProcessContext);
    if (!context) {
        throw new Error('useProcesses must be used within a ProcessProvider');
    }
    return context;
};
