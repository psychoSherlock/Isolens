# IsoLens Architecture

## Overview
IsoLens is a modular malware sandbox. The architecture is divided into several layers within the `core/` directory.

## Component Responsibilities

### `core/interface/`
Handles all user-facing logic, including file uploads and report visualization.

### `core/gateway/`
The system entry layer that routes API requests to the controller.

### `core/controller/`
The orchestration brain that coordinates the VM lifecycle and analysis workflow, including VirtualBox control via VBoxManage.

### `core/agent/`
Guest-side API service running inside the isolated container/VM. It gathers logs and tool outputs from within the sandbox.

### `core/modules/`
Functional processing layer for parsing logs, extracting IOCs, and risk scoring.

### `core/observer/`
Monitoring layer that collects raw data from the host perspective (process tracking, network, etc.).

### `core/threatintelligence/`
AI-assisted layer that provides threat classification and natural language summaries.

### `core/storage/`
Persistent storage for databases, samples, logs, and reports.
