'use server';

import { prisma } from '@/lib/db';
import { ProcessStatus, ProcessType } from '@/lib/types/processes';
import { revalidatePath } from 'next/cache';

export async function getProcesses() {
    try {
        const processes = await prisma.process.findMany({
            orderBy: { createdAt: 'desc' },
        });
        return processes.map((p: any) => ({
            ...p,
            data: p.data as any,
            history: p.history as any,
            type: p.type as ProcessType,
            status: p.status as ProcessStatus,
            currentStep: p.currentStep as any,
        }));
    } catch (error) {
        console.error('Failed to fetch processes:', error);
        return [];
    }
}

export async function createProcess(data: any) {
    try {
        const newProcess = await prisma.process.create({
            data: {
                type: data.type,
                status: data.status,
                currentStep: data.currentStep,
                assignedRole: data.assignedRole,
                data: data.data,
                history: data.history,
            },
        });
        revalidatePath('/dashboard');
        return newProcess;
    } catch (error) {
        console.error('Failed to create process:', error);
        throw new Error('Failed to create process');
    }
}

export async function updateProcess(id: string, data: any) {
    try {
        const updated = await prisma.process.update({
            where: { id },
            data: {
                status: data.status,
                currentStep: data.currentStep,
                assignedRole: data.assignedRole,
                data: data.data,
                history: data.history,
            },
        });
        revalidatePath('/dashboard');
        return updated;
    } catch (error) {
        console.error('Failed to update process:', error);
        throw new Error('Failed to update process');
    }
}
