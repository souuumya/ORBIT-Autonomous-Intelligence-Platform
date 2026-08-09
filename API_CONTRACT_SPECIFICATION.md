# API Contract Specification

## Overview

The API provides a RESTful interface for mission initialization, mission lifecycle management, progress feed access, memory management, analytics retrieval, and health monitoring.

The API is designed to support an autonomous mission-driven system where a user submits a high-level mission, monitors execution progress, and reviews outcomes.

---

## 1. Agent APIs

### POST /api/agent/init

Purpose:
- Initialize a new mission for autonomous execution.

Request Body:
- mission_title: string
- mission_objective: string
- mission_description: string
- priority: string
- context: object
- user_id: string

Response Body:
- mission_id: string
- status: string
- created_at: string
- message: string

Error Responses:
- 400 Bad Request: invalid mission payload
- 401 Unauthorized: missing or invalid authentication
- 422 Unprocessable Entity: validation rules violated
- 500 Internal Server Error: unexpected server failure

Validation Rules:
- mission_title must be a non-empty string
- mission_objective must be a non-empty string
- mission_description must be a non-empty string
- priority must be one of a defined set of values
- user_id must be a valid identifier

---

### GET /api/agent/feed

Purpose:
- Retrieve meaningful progress updates for an active mission.

Request Parameters:
- mission_id: string (required)
- limit: integer (optional)
- offset: integer (optional)

Response Body:
- mission_id: string
- entries: array of feed items
- total_count: integer

Error Responses:
- 400 Bad Request: missing mission_id
- 401 Unauthorized: missing or invalid authentication
- 404 Not Found: mission not found
- 500 Internal Server Error: unexpected server failure

Validation Rules:
- mission_id must be a valid mission identifier
- limit must be a positive integer if provided
- offset must be a non-negative integer if provided

---

## 2. Mission APIs

### POST /api/missions

Purpose:
- Create a new mission.

Request Body:
- title: string
- objective: string
- description: string
- priority: string
- organization_id: string
- created_by_user_id: string

Response Body:
- id: string
- title: string
- status: string
- created_at: string

Error Responses:
- 400 Bad Request: invalid payload
- 401 Unauthorized: authentication required
- 422 Unprocessable Entity: validation failure

Validation Rules:
- title and objective are required
- description must be a string if provided
- priority must be valid

---

### GET /api/missions/{mission_id}

Purpose:
- Retrieve mission details.

Response Body:
- id: string
- title: string
- objective: string
- status: string
- current_phase: string
- created_at: string
- updated_at: string

Error Responses:
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

Validation Rules:
- mission_id must be a valid UUID or identifier format

---

### GET /api/missions

Purpose:
- Retrieve a list of missions.

Query Parameters:
- status: string
- organization_id: string
- created_by_user_id: string
- limit: integer
- offset: integer

Response Body:
- missions: array
- total_count: integer

Error Responses:
- 400 Bad Request: invalid query parameter
- 401 Unauthorized

Validation Rules:
- status must be one of allowed values if provided
- limit and offset must be valid integers

---

### PATCH /api/missions/{mission_id}

Purpose:
- Update mission metadata or status.

Request Body:
- status: string
- current_phase: string
- title: string
- objective: string

Response Body:
- id: string
- status: string
- updated_at: string

Error Responses:
- 400 Bad Request
- 404 Not Found
- 422 Unprocessable Entity

Validation Rules:
- only supported fields may be updated
- status must be valid

---

### GET /api/missions/{mission_id}/milestones

Purpose:
- Retrieve milestone breakdown for a mission.

Response Body:
- mission_id: string
- milestones: array

Error Responses:
- 404 Not Found
- 401 Unauthorized

Validation Rules:
- mission_id must be valid

---

### GET /api/missions/{mission_id}/tasks

Purpose:
- Retrieve task list for a mission.

Response Body:
- mission_id: string
- tasks: array

Error Responses:
- 404 Not Found
- 401 Unauthorized

Validation Rules:
- mission_id must be valid

---

### GET /api/missions/{mission_id}/outputs

Purpose:
- Retrieve generated outputs for a mission.

Response Body:
- mission_id: string
- outputs: array

Error Responses:
- 404 Not Found
- 401 Unauthorized

Validation Rules:
- mission_id must be valid

---

## 3. Memory APIs

### POST /api/memory

Purpose:
- Store a lesson learned or reusable insight.

Request Body:
- mission_id: string
- memory_type: string
- summary: string
- insight: string
- confidence_score: number

Response Body:
- id: string
- created_at: string

Error Responses:
- 400 Bad Request
- 401 Unauthorized
- 422 Unprocessable Entity

Validation Rules:
- mission_id must be valid
- memory_type must be a valid value
- summary and insight must be non-empty
- confidence_score must be numeric and within an allowed range

---

### GET /api/memory

Purpose:
- Retrieve memory records for a user or organization.

Query Parameters:
- user_id: string
- organization_id: string
- limit: integer
- offset: integer

Response Body:
- memories: array
- total_count: integer

Error Responses:
- 400 Bad Request
- 401 Unauthorized

Validation Rules:
- at least one of user_id or organization_id must be provided
- limit and offset must be valid integers

---

### GET /api/memory/{memory_id}

Purpose:
- Retrieve a specific memory record.

Response Body:
- id: string
- memory_type: string
- summary: string
- insight: string
- confidence_score: number

Error Responses:
- 404 Not Found
- 401 Unauthorized

Validation Rules:
- memory_id must be valid

---

## 4. Analytics APIs

### GET /api/analytics/missions

Purpose:
- Retrieve mission-level analytics.

Query Parameters:
- organization_id: string
- period: string
- status: string

Response Body:
- total_missions: integer
- completed_missions: integer
- active_missions: integer
- average_duration: number
- status_breakdown: object

Error Responses:
- 400 Bad Request
- 401 Unauthorized

Validation Rules:
- organization_id must be valid if provided
- period must be a supported value if provided

---

### GET /api/analytics/performance

Purpose:
- Retrieve performance insights for completed missions.

Query Parameters:
- organization_id: string
- mission_id: string

Response Body:
- average_quality_score: number
- average_completion_time: number
- adaptation_count: integer
- success_rate: number

Error Responses:
- 400 Bad Request
- 401 Unauthorized

Validation Rules:
- at least one of organization_id or mission_id must be provided

---

## 5. Health APIs

### GET /api/health

Purpose:
- Basic health status for the backend service.

Response Body:
- status: string
- service: string
- timestamp: string

Error Responses:
- 500 Internal Server Error

Validation Rules:
- No request body required

---

### GET /api/health/ready

Purpose:
- Indicate whether the service is ready to handle requests.

Response Body:
- status: string
- ready: boolean

Error Responses:
- 503 Service Unavailable: dependencies not ready
- 500 Internal Server Error

Validation Rules:
- No request body required

---

## Common Response Conventions

### Success Response Shape
- status: string
- data: object
- message: string

### Error Response Shape
- error: object
- code: string
- message: string
- details: object

---

## Validation Rules Summary

- All required fields must be present and non-empty where applicable.
- IDs must be in a valid identifier format.
- Enumerated values must be restricted to known business values.
- Numeric values must be within reasonable limits.
- Authentication is required for protected endpoints.
- Access control should enforce mission ownership or organization membership.

---

## Notes for Future Expansion

The contract should remain RESTful while allowing future growth for:
- richer mission lifecycle states
- expanded analytics summaries
- advanced memory retrieval patterns
- additional real-time updates through the feed APIs
- permission-aware collaboration workflows
