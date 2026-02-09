import { ProcessType, ProcessStep, AnyProcessData, DecorationsData, LeaveRequestData, EmploymentConditionsData, ProcessStatus } from './types/processes';

export interface WorkflowTransition {
    nextStep: ProcessStep | null;
    nextStatus: ProcessStatus;
    nextAssigneeRole: string;
}

// Helper to get role code based on step
export function getAssigneeRoleForStep(step: ProcessStep): string {
    switch (step) {
        // --- DECORATIONS ---
        case ProcessStep.DECORATIONS_SUBMIT: return 'Head of O.U.'; // Initiator
        case ProcessStep.DECORATIONS_PD_ACCEPTANCE: return 'PD';
        case ProcessStep.DECORATIONS_PRK_REVIEW: return 'PRK'; // PRK / Chancellor shared lane in BPMN, but usually PRK acts
        case ProcessStep.DECORATIONS_PD_TO_RKR: return 'PD';
        case ProcessStep.DECORATIONS_RKR_DECISION: return 'RKR';
        case ProcessStep.DECORATIONS_PD_TO_MPD: return 'PD';
        case ProcessStep.DECORATIONS_MPD_EXTERNAL: return 'MPD/WKW'; // Military Personnel Dept
        case ProcessStep.DECORATIONS_PD_RECEIVE_DECISION: return 'PD';
        case ProcessStep.DECORATIONS_PD_REGISTER: return 'PD';

        // --- LEAVE ---
        case ProcessStep.LEAVE_SUBMIT: return 'Any'; // Usually self-service, but for this demo let's say initiator
        case ProcessStep.LEAVE_HEAD_OU_REVIEW: return 'Head of O.U.';
        case ProcessStep.LEAVE_PD_REVIEW: return 'PD';
        case ProcessStep.LEAVE_PRK_REVIEW: return 'PRK';
        case ProcessStep.LEAVE_PRN_REVIEW: return 'PRN';
        case ProcessStep.LEAVE_RKR_DECISION: return 'RKR';
        case ProcessStep.LEAVE_KAN_DECISION: return 'KAN';
        case ProcessStep.LEAVE_PD_INFORM: return 'PD';
        case ProcessStep.LEAVE_PD_REGISTER: return 'PD';

        // --- EMPLOYMENT ---
        case ProcessStep.EMPLOYMENT_SUBMIT: return 'Head of O.U.';
        case ProcessStep.EMPLOYMENT_HEAD_OU_FORWARD: return 'Head of O.U.';
        case ProcessStep.EMPLOYMENT_PD_REVIEW: return 'PD';
        case ProcessStep.EMPLOYMENT_KWE_REVIEW: return 'KWE';
        case ProcessStep.EMPLOYMENT_PRK_REVIEW: return 'PRK';
        case ProcessStep.EMPLOYMENT_PRN_REVIEW: return 'PRN';
        case ProcessStep.EMPLOYMENT_RKR_DECISION: return 'RKR';
        case ProcessStep.EMPLOYMENT_PD_IMPLEMENT: return 'PD';
        case ProcessStep.EMPLOYMENT_PD_ARCHIVE: return 'PD';

        default: return 'Admin';
    }
}

export function getInitialStep(type: ProcessType): ProcessStep {
    switch (type) {
        case ProcessType.DECORATIONS: return ProcessStep.DECORATIONS_SUBMIT;
        case ProcessType.LEAVE_REQUEST: return ProcessStep.LEAVE_SUBMIT;
        case ProcessType.EMPLOYMENT_CONDITIONS: return ProcessStep.EMPLOYMENT_SUBMIT;
    }
}

export function getNextState(
    currentStep: ProcessStep,
    data: AnyProcessData
): WorkflowTransition {
    const defaultTransition = { nextStep: currentStep, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: getAssigneeRoleForStep(currentStep) };

    // --- DECORATIONS ---
    if (currentStep === ProcessStep.DECORATIONS_SUBMIT) {
        return { nextStep: ProcessStep.DECORATIONS_PD_ACCEPTANCE, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.DECORATIONS_PD_ACCEPTANCE) {
        return { nextStep: ProcessStep.DECORATIONS_PRK_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PRK' };
    }
    if (currentStep === ProcessStep.DECORATIONS_PRK_REVIEW) {
        return { nextStep: ProcessStep.DECORATIONS_PD_TO_RKR, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.DECORATIONS_PD_TO_RKR) {
        return { nextStep: ProcessStep.DECORATIONS_RKR_DECISION, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'RKR' };
    }
    if (currentStep === ProcessStep.DECORATIONS_RKR_DECISION) {
        const d = data as DecorationsData;
        if (d.rkrDecision === 'Accepted') {
            return { nextStep: ProcessStep.DECORATIONS_PD_TO_MPD, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
        } else {
            return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' };
        }
    }
    if (currentStep === ProcessStep.DECORATIONS_PD_TO_MPD) {
        return { nextStep: ProcessStep.DECORATIONS_MPD_EXTERNAL, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'MPD/WKW' };
    }
    if (currentStep === ProcessStep.DECORATIONS_MPD_EXTERNAL) {
        return { nextStep: ProcessStep.DECORATIONS_PD_RECEIVE_DECISION, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.DECORATIONS_PD_RECEIVE_DECISION) {
        return { nextStep: ProcessStep.DECORATIONS_PD_REGISTER, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.DECORATIONS_PD_REGISTER) {
        return { nextStep: null, nextStatus: ProcessStatus.COMPLETED, nextAssigneeRole: '' };
    }


    // --- LEAVE REQUEST ---
    if (currentStep === ProcessStep.LEAVE_SUBMIT) {
        return { nextStep: ProcessStep.LEAVE_HEAD_OU_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'Head of O.U.' };
    }
    if (currentStep === ProcessStep.LEAVE_HEAD_OU_REVIEW) {
        const d = data as LeaveRequestData;
        if (d.headOuDecision === 'Rejected') return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' };
        return { nextStep: ProcessStep.LEAVE_PD_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.LEAVE_PD_REVIEW) {
        const d = data as LeaveRequestData;
        // Gateway: Is Academic Teacher?
        if (d.isAcademicTeacher) {
            return { nextStep: ProcessStep.LEAVE_PRK_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PRK' };
        } else {
            return { nextStep: ProcessStep.LEAVE_KAN_DECISION, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'KAN' };
        }
    }
    if (currentStep === ProcessStep.LEAVE_PRK_REVIEW) {
        return { nextStep: ProcessStep.LEAVE_PRN_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PRN' };
    }
    if (currentStep === ProcessStep.LEAVE_PRN_REVIEW) {
        return { nextStep: ProcessStep.LEAVE_RKR_DECISION, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'RKR' };
    }
    // Decision Merging
    if (currentStep === ProcessStep.LEAVE_RKR_DECISION || currentStep === ProcessStep.LEAVE_KAN_DECISION) {
        const d = data as LeaveRequestData;
        if (d.finalDecision === 'Rejected') return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' };
        return { nextStep: ProcessStep.LEAVE_PD_INFORM, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.LEAVE_PD_INFORM) {
        return { nextStep: ProcessStep.LEAVE_PD_REGISTER, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.LEAVE_PD_REGISTER) {
        return { nextStep: null, nextStatus: ProcessStatus.COMPLETED, nextAssigneeRole: '' };
    }


    // --- EMPLOYMENT CONDITIONS ---
    if (currentStep === ProcessStep.EMPLOYMENT_SUBMIT) {
        // Actually usually starts with Review and Forward since it's the Initiator's task in BPMN
        return { nextStep: ProcessStep.EMPLOYMENT_HEAD_OU_FORWARD, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'Head of O.U.' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_HEAD_OU_FORWARD) {
        // Step 2 in scenario
        return { nextStep: ProcessStep.EMPLOYMENT_PD_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_PD_REVIEW) {
        // Step 3 -> 4
        return { nextStep: ProcessStep.EMPLOYMENT_KWE_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'KWE' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_KWE_REVIEW) {
        const d = data as EmploymentConditionsData;

        // Critical Logic: Check funds first
        if (d.kweFinancialOpinion === 'No Funds') {
            return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' };
        }

        // Gateway: Is Academic?
        // Note: The UI sets this as a string "true" or "false" in Select.
        // We should ensure we handle string or boolean if possible, but the Select likely returns string "true".
        // Let's coerce to boolean.
        const isAcademic = String(d.isAcademicTeacher) === 'true';

        if (isAcademic) {
            return { nextStep: ProcessStep.EMPLOYMENT_PRK_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PRK' };
        } else {
            // Non-academic path
            return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' }; // TODO: KAN path
        }
    }
    if (currentStep === ProcessStep.EMPLOYMENT_PRK_REVIEW) {
        return { nextStep: ProcessStep.EMPLOYMENT_PRN_REVIEW, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PRN' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_PRN_REVIEW) {
        return { nextStep: ProcessStep.EMPLOYMENT_RKR_DECISION, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'RKR' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_RKR_DECISION) {
        const d = data as EmploymentConditionsData;
        if (d.finalDecision === 'Rejected') return { nextStep: null, nextStatus: ProcessStatus.REJECTED, nextAssigneeRole: '' };
        return { nextStep: ProcessStep.EMPLOYMENT_PD_IMPLEMENT, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_PD_IMPLEMENT) {
        return { nextStep: ProcessStep.EMPLOYMENT_PD_ARCHIVE, nextStatus: ProcessStatus.ACTIVE, nextAssigneeRole: 'PD' };
    }
    if (currentStep === ProcessStep.EMPLOYMENT_PD_ARCHIVE) {
        return { nextStep: null, nextStatus: ProcessStatus.COMPLETED, nextAssigneeRole: '' };
    }

    // ... existing code ...

    return defaultTransition;
}

// Helper for display names
export const PROCESS_NAMES: Record<ProcessType, string> = {
    [ProcessType.DECORATIONS]: 'Decorations and Medals',
    [ProcessType.LEAVE_REQUEST]: 'Leave Request',
    [ProcessType.EMPLOYMENT_CONDITIONS]: 'Change of Employment Conditions',
};

// Helper for step names
export const STEP_NAMES: Record<string, string> = {
    [ProcessStep.DECORATIONS_SUBMIT]: 'Submit Application',
    [ProcessStep.DECORATIONS_PD_ACCEPTANCE]: 'Present application for acceptance (PD)',
    [ProcessStep.DECORATIONS_PRK_REVIEW]: 'Review application (PRK)',
    [ProcessStep.DECORATIONS_PD_TO_RKR]: 'Present application to Rector (PD)',
    [ProcessStep.DECORATIONS_RKR_DECISION]: 'Rector Decision',
    [ProcessStep.DECORATIONS_PD_TO_MPD]: 'Forward to MPD (PD)',
    [ProcessStep.DECORATIONS_MPD_EXTERNAL]: 'External Processing (MPD/WKW)',
    [ProcessStep.DECORATIONS_PD_RECEIVE_DECISION]: 'Receive Decision (PD)',
    [ProcessStep.DECORATIONS_PD_REGISTER]: 'Register Award (PD)',

    [ProcessStep.LEAVE_SUBMIT]: 'Submit Request',
    [ProcessStep.LEAVE_HEAD_OU_REVIEW]: 'Head of O.U. Review',
    [ProcessStep.LEAVE_PD_REVIEW]: 'PD Verification',
    [ProcessStep.LEAVE_PRK_REVIEW]: 'PRK Review',
    [ProcessStep.LEAVE_PRN_REVIEW]: 'PRN Review',
    [ProcessStep.LEAVE_RKR_DECISION]: 'Rector Decision',
    [ProcessStep.LEAVE_KAN_DECISION]: 'Chancellor Decision',
    [ProcessStep.LEAVE_PD_INFORM]: 'Inform Head of O.U.',
    [ProcessStep.LEAVE_PD_REGISTER]: 'Register Leave in HR',

    [ProcessStep.EMPLOYMENT_SUBMIT]: 'Submit Proposal',
    [ProcessStep.EMPLOYMENT_HEAD_OU_FORWARD]: 'Review and Forward (Head of O.U.)',
    [ProcessStep.EMPLOYMENT_PD_REVIEW]: 'PD Review',
    [ProcessStep.EMPLOYMENT_KWE_REVIEW]: 'Quartermaster Financial Opinion',
    [ProcessStep.EMPLOYMENT_PRK_REVIEW]: 'PRK Opinion',
    [ProcessStep.EMPLOYMENT_PRN_REVIEW]: 'PRN Opinion',
    [ProcessStep.EMPLOYMENT_RKR_DECISION]: 'Final Decision (RKR)',
    [ProcessStep.EMPLOYMENT_PD_IMPLEMENT]: 'Prepare Contract Supplement (PD)',
    [ProcessStep.EMPLOYMENT_PD_ARCHIVE]: 'Archive Documents (PD)',
};

export const getProcessName = (type: ProcessType) => PROCESS_NAMES[type] || type;
export const getStepName = (step: string) => STEP_NAMES[step] || step;
