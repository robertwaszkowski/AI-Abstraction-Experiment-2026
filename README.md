# AI-Abstraction-Experiment-2026

## Overview
This repository hosts the dataset, source code, and experimental logs for the research paper **"The Symbiotic Future of AI and Runtime-Based Low-Code Platforms: Elevating Abstraction in Citizen Development"**[cite: 488].

The project empirically validates the **Abstraction-Effectiveness Hypothesis**[cite: 494], which posits that the reliability and efficiency of AI-driven software generation are positively correlated with the abstraction level of the target artifact.

## Experiment Structure
The study compares two experimental conditions across 6 independent teams:
1.  **Low-Abstraction (Code Generation):** Using AI to generate full-stack imperative code (Node.js, React, SQL)[cite: 710].
2.  **High-Abstraction (Model Generation):** Using AI to generate declarative models (BPMN 2.0, JSON Schema) for direct execution on a runtime platform[cite: 719].

## Benchmark Applications
The experiment tasked participants with generating three specific business applications[cite: 731]:
1.  **Expense Approval System:** A workflow for submitting and approving expenses[cite: 732].
2.  **IT Support Ticketing System:** A system for managing support requests and status tracking[cite: 734].
3.  **Employee Leave Request System:** A process for requesting and managing time off[cite: 736].

## Repository Organization
The data is organized by independent experimental teams (`Team_01` to `Team_06`).

* **📂 /Team_XX:** Contains the specific results for one experimental group.
    * `Prompt_Log.txt`: The complete conversational transcript with the AI (ChatGPT/Gemini/Claude), documenting the prompting strategy and error correction process[cite: 758].
    * `/App_1_Expense`: Source code or models for the first application.
    * `/App_2_Ticket`: Source code or models for the second application.
    * `/App_3_Leave`: Source code or models for the third application.

* **📊 RESULTS_Summary.xlsx:** The master data file containing:
    * **Development Time:** Total time (in minutes) to complete the task[cite: 770].
    * **Prompting Efficiency:** Number of conversational turns required[cite: 771].
    * **Functional Correctness:** Pass/Fail rates against the standardized test suite[cite: 773].

## Citation
If you use this dataset, please cite the associated paper:
> Waszkowski, R. (2025). The Symbiotic Future of AI and Runtime-Based Low-Code Platforms. IEEE Transactions on Software Engineering (Under Review).
