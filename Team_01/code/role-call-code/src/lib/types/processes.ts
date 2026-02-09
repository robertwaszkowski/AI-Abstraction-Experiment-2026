
export enum ProcessType {
    DECORATIONS = 'DECORATIONS',
    LEAVE_REQUEST = 'LEAVE_REQUEST',
    EMPLOYMENT_CONDITIONS = 'EMPLOYMENT_CONDITIONS',
}

export enum ProcessStatus {
    ACTIVE = 'ACTIVE',
    COMPLETED = 'COMPLETED',
    REJECTED = 'REJECTED',
}

// Ensure these match the BPMN task names or IDs roughly for clarity
export enum ProcessStep {
    // Decorations
    START_DECORATIONS = 'START_DECORATIONS',
    HEAD_OU_REVIEW_DECORATIONS = 'HEAD_OU_REVIEW_DECORATIONS', // Submit application for distinction (Initiator doing it) - Wait, the doc says "Submit" is the start.
    // Actually, let's map steps to the BPMN User Tasks

    // Decorations Sequence
    DECORATIONS_SUBMIT = 'DECORATIONS_SUBMIT',
    DECORATIONS_PD_ACCEPTANCE = 'DECORATIONS_PD_ACCEPTANCE', // Present applications for acceptance
    DECORATIONS_PRK_REVIEW = 'DECORATIONS_PRK_REVIEW', // Review applications and forward to PD
    DECORATIONS_PD_TO_RKR = 'DECORATIONS_PD_TO_RKR', // Present reviewed applications to Rector
    DECORATIONS_RKR_DECISION = 'DECORATIONS_RKR_DECISION', // Make decision
    DECORATIONS_PD_TO_MPD = 'DECORATIONS_PD_TO_MPD', // Forward accepted applications to MPD
    DECORATIONS_MPD_EXTERNAL = 'DECORATIONS_MPD_EXTERNAL', // Handle applications (external transfer)
    DECORATIONS_PD_RECEIVE_DECISION = 'DECORATIONS_PD_RECEIVE_DECISION', // Receive decision on award
    DECORATIONS_PD_REGISTER = 'DECORATIONS_PD_REGISTER', // Enter decoration into register

    // Leave Request Sequence
    LEAVE_SUBMIT = 'LEAVE_SUBMIT',
    LEAVE_HEAD_OU_REVIEW = 'LEAVE_HEAD_OU_REVIEW',
    LEAVE_PD_REVIEW = 'LEAVE_PD_REVIEW',
    LEAVE_PRK_REVIEW = 'LEAVE_PRK_REVIEW',
    LEAVE_PRN_REVIEW = 'LEAVE_PRN_REVIEW',
    LEAVE_RKR_DECISION = 'LEAVE_RKR_DECISION',
    LEAVE_KAN_DECISION = 'LEAVE_KAN_DECISION',
    LEAVE_PD_INFORM = 'LEAVE_PD_INFORM',
    LEAVE_PD_REGISTER = 'LEAVE_PD_REGISTER',

    // Employment Conditions Sequence
    EMPLOYMENT_SUBMIT = 'EMPLOYMENT_SUBMIT', // Filled by Head OU usually
    EMPLOYMENT_HEAD_OU_FORWARD = 'EMPLOYMENT_HEAD_OU_FORWARD',
    EMPLOYMENT_PD_REVIEW = 'EMPLOYMENT_PD_REVIEW',
    EMPLOYMENT_KWE_REVIEW = 'EMPLOYMENT_KWE_REVIEW',
    EMPLOYMENT_PRK_REVIEW = 'EMPLOYMENT_PRK_REVIEW',
    EMPLOYMENT_PRN_REVIEW = 'EMPLOYMENT_PRN_REVIEW',
    EMPLOYMENT_RKR_DECISION = 'EMPLOYMENT_RKR_DECISION',
    EMPLOYMENT_PD_IMPLEMENT = 'EMPLOYMENT_PD_IMPLEMENT',
    EMPLOYMENT_PD_ARCHIVE = 'EMPLOYMENT_PD_ARCHIVE',
}

export interface BaseProcessData {
    initiatorUsername: string;
    startDate: string;
}

// --- Decorations Data ---
export interface DecorationsData extends BaseProcessData {
    employeeName: string;
    organizationalUnit: string;
    decorationType: string;
    justification: string;
    // Approval chain data
    reviewerOpinion?: string; // PRK/Chorus
    rkrDecision?: 'Accepted' | 'Rejected';
    awardGrantDate?: string;
    processOutcome?: 'Completed' | 'Rejected';
}

// --- Leave Request Data ---
export interface LeaveRequestData extends BaseProcessData {
    employeeName: string;
    employeePosition: string;
    leaveType: string;
    leaveStartDate: string;
    leaveEndDate: string;
    leaveDurationDays: number;
    leaveSubstitute?: string;
    requestDate: string;

    // Routing context
    isAcademicTeacher?: boolean; // Default true
    leaveEntitlementBalance?: number; // Default 26

    // Decisions
    headOuDecision?: 'Approved' | 'Rejected';
    pdReviewStatus?: 'Entitlement Confirmed' | 'Entitlement Exceeded';
    lssOpinionNotes?: string;
    prkReviewStatus?: 'Approved' | 'Rejected';
    prnReviewStatus?: 'Approved' | 'Rejected';
    finalDecision?: 'Approved' | 'Rejected'; // KAN or RKR
    finalDecisionMaker?: 'Rector' | 'Chancellor';
}

// --- Employment Conditions Data ---
export interface EmploymentConditionsData extends BaseProcessData {
    employeeName: string;
    proposedConditions: string;
    changeJustification: string;
    changeEffectiveDate: string;

    // Routing
    isAcademicTeacher?: boolean; // Default true

    // Decisions
    headOuReviewStatus?: 'Approved' | 'Rejected';
    pdReviewStatus?: 'Confirmed' | 'Rejected';
    kweFinancialOpinion?: 'Funds Available' | 'No Funds';
    prkOpinion?: 'Approved' | 'Rejected';
    prnOpinion?: 'Approved' | 'Rejected';
    finalDecision?: 'Approved' | 'Rejected';
}

export type AnyProcessData = DecorationsData | LeaveRequestData | EmploymentConditionsData;

export interface ProcessInstance {
    id: string;
    type: ProcessType;
    status: ProcessStatus;
    currentStep: ProcessStep | null; // null if ended
    assignedRole: string; // The role code authorized to act, e.g., 'PD', 'RKR'
    assignedUser?: string; // Specific username if required, usually role-based
    data: AnyProcessData;
    history: { step: string; user: string; timestamp: string; action: string }[];
}
