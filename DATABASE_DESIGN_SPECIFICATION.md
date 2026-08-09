# Database Design Specification

## Entity List

The database should support mission execution, user interaction, progress tracking, output review, memory, and operational transparency.

### Core Entities
- users
- organizations
- missions
- milestones
- tasks
- strategies
- strategy_options
- outputs
- reviews
- activity_feed_entries
- memory_records
- mission_events
- mission_artifacts
- mission_permissions
- audit_logs

---

## ER Diagram (Text)

users
  1 --- * organizations
  1 --- * missions
  1 --- * activity_feed_entries
  1 --- * memory_records
  1 --- * audit_logs

organizations
  1 --- * missions
  1 --- * mission_permissions

missions
  1 --- * milestones
  1 --- * tasks
  1 --- * strategies
  1 --- * outputs
  1 --- * reviews
  1 --- * activity_feed_entries
  1 --- * mission_events
  1 --- * mission_artifacts
  1 --- * mission_permissions

milestones
  1 --- * tasks
  1 --- * mission_events

tasks
  1 --- * strategy_options
  1 --- * outputs
  1 --- * reviews
  1 --- * mission_events

strategies
  1 --- * strategy_options
  1 --- * mission_events

strategy_options
  1 --- * reviews

outputs
  1 --- * mission_artifacts

reviews
  1 --- * mission_events

---

## Table Definitions

### 1. users
Purpose: Represents platform users such as founders, creators, marketers, or administrators.

Key fields:
- id: primary key
- organization_id: foreign key to organizations
- email: unique
- username: unique
- full_name
- role
- is_active
- created_at
- updated_at
- last_login_at

Why this table exists:
- To identify users and associate them with missions and permissions.

---

### 2. organizations
Purpose: Represents a tenant or working group for shared missions and collaboration.

Key fields:
- id: primary key
- name
- slug
- is_active
- created_at
- updated_at

Why this table exists:
- To support future multi-tenant or team-based usage.

---

### 3. missions
Purpose: Represents a high-level autonomous business mission.

Key fields:
- id: primary key
- organization_id: foreign key to organizations
- created_by_user_id: foreign key to users
- title
- objective
- description
- status
- priority
- current_phase
- started_at
- completed_at
- created_at
- updated_at

Why this table exists:
- To represent the central unit of autonomous execution.

Status examples:
- draft
- queued
- running
- paused
- completed
- failed
- cancelled

---

### 4. milestones
Purpose: Represents major phases or checkpoints within a mission.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- title
- description
- sequence_number
- status
- started_at
- completed_at
- created_at
- updated_at

Why this table exists:
- To break a mission into understandable execution stages.

---

### 5. tasks
Purpose: Represents the discrete work items generated during mission execution.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- milestone_id: foreign key to milestones
- title
- description
- task_type
- status
- priority
- assigned_agent_role
- started_at
- completed_at
- created_at
- updated_at

Why this table exists:
- To track the atomic work units performed during mission execution.

---

### 6. strategies
Purpose: Stores the selected or candidate strategic approach for a mission.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- name
- description
- rationale
- status
- selected_at
- created_at
- updated_at

Why this table exists:
- To capture the reasoning behind how the system chose to proceed.

---

### 7. strategy_options
Purpose: Stores alternative strategies considered by the agent before selection.

Key fields:
- id: primary key
- strategy_id: foreign key to strategies
- task_id: foreign key to tasks
- title
- description
- rationale
- score
- status
- created_at
- updated_at

Why this table exists:
- To preserve decision-making context and support future explanation and evaluation.

---

### 8. outputs
Purpose: Stores generated deliverables or assets created during mission execution.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- task_id: foreign key to tasks
- output_type
- title
- summary
- content_reference
- quality_score
- status
- created_at
- updated_at

Why this table exists:
- To preserve generated artifacts and connect them to mission work.

---

### 9. reviews
Purpose: Stores self-review, quality assessments, and evaluation results.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- task_id: foreign key to tasks
- strategy_option_id: foreign key to strategy_options
- review_type
- score
- summary
- recommendations
- created_at
- updated_at

Why this table exists:
- To capture quality checks and self-evaluation performed by the system.

---

### 10. activity_feed_entries
Purpose: Stores meaningful progress updates that should be surfaced to the user dashboard.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- user_id: foreign key to users
- event_type
- message
- metadata_json
- created_at

Why this table exists:
- To power the progress feed and provide transparency into autonomous execution.

---

### 11. mission_events
Purpose: Stores event history for mission execution, including adaptation events and milestones.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- milestone_id: foreign key to milestones
- task_id: foreign key to tasks
- strategy_id: foreign key to strategies
- event_type
- event_payload
- created_at

Why this table exists:
- To preserve a detailed execution timeline and support observability.

---

### 12. mission_artifacts
Purpose: Stores supporting files or references linked to outputs or mission progress.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- output_id: foreign key to outputs
- artifact_type
- file_name
- storage_reference
- created_at
- updated_at

Why this table exists:
- To support future file-based assets and deliverables without overloading the outputs table.

---

### 13. mission_permissions
Purpose: Stores access permissions for missions and related records.

Key fields:
- id: primary key
- mission_id: foreign key to missions
- organization_id: foreign key to organizations
- user_id: foreign key to users
- permission_level
- created_at
- updated_at

Why this table exists:
- To support access control and future collaboration features.

---

### 14. memory_records
Purpose: Stores lessons learned and reusable patterns from prior missions.

Key fields:
- id: primary key
- user_id: foreign key to users
- organization_id: foreign key to organizations
- mission_id: foreign key to missions
- memory_type
- summary
- insight
- confidence_score
- created_at
- updated_at

Why this table exists:
- To provide long-term learning and future mission improvement.

---

### 15. audit_logs
Purpose: Stores system and administrative audit events.

Key fields:
- id: primary key
- user_id: foreign key to users
- entity_type
- entity_id
- action
- details_json
- created_at

Why this table exists:
- To support traceability, security, and operational accountability.

---

## Relationships

### One-to-Many Relationships
- organizations to users
- organizations to missions
- missions to milestones
- missions to tasks
- missions to strategies
- missions to outputs
- missions to reviews
- missions to activity_feed_entries
- missions to mission_events
- missions to mission_artifacts
- missions to mission_permissions
- users to activity_feed_entries
- users to memory_records
- users to audit_logs
- strategies to strategy_options
- tasks to outputs
- tasks to reviews
- tasks to mission_events
- outputs to mission_artifacts

### Many-to-Many Relationships
- A future extension may require many-to-many relationships between users and missions or organizations and users if richer collaboration is needed.
- For the initial design, the current model should keep relationships explicit and normalized.

---

## Index Strategy

Recommended indexes should be based on performance-critical access patterns.

### High-Priority Indexes
- missions(status, created_at)
- missions(organization_id, status)
- milestones(mission_id, sequence_number)
- tasks(mission_id, status)
- tasks(milestone_id, status)
- strategies(mission_id, status)
- outputs(mission_id, status)
- reviews(mission_id, review_type)
- activity_feed_entries(mission_id, created_at)
- mission_events(mission_id, created_at)
- memory_records(user_id, created_at)
- mission_permissions(mission_id, user_id)
- audit_logs(entity_type, entity_id, created_at)

### Additional Indexes
- users(email)
- users(username)
- organizations(slug)
- missions(created_by_user_id)
- tasks(priority, status)
- outputs(output_type)

### Why Indexes Matter
- Improves dashboard and feed performance
- Speeds up mission lifecycle queries
- Helps with status-based filtering and history retrieval
- Supports scale as mission volume grows

---

## Audit Fields

Each major table should include audit fields where appropriate:
- created_at
- updated_at
- created_by
- updated_by

For historical or immutable datasets such as mission_events and audit_logs, creation time is especially important.

---

## Status Fields

Recommended status fields:
- missions.status
- milestones.status
- tasks.status
- strategies.status
- strategy_options.status
- outputs.status
- reviews.review_type or review_state if split into status and type

This allows clear lifecycle tracking and operational visibility.

---

## Normalization Notes

The proposed schema is normalized by separating:
- users from organizations
- missions from milestones/tasks
- strategies from their options
- outputs from supporting artifacts
- activity feed and mission events from primary transaction entities

This reduces duplication and improves maintainability.

---

## Scalability Considerations

To support growth, the design should favor:
- Vertical partitioning of large activity and event tables if needed later
- Clear separation between operational and historical data
- JSON metadata fields only where flexibility is required
- Indexes aligned with expected query patterns
- Careful use of large text or binary content storage references rather than embedding everything directly

---

## Future Expansion Notes

The schema can evolve to support:
- Multi-tenant collaboration with richer permissions
- Shared mission templates
- Team-based assignments and ownership
- Analytics dashboards and reporting tables
- External integrations and connectors
- Richer memory structures with embeddings or semantic metadata
- Message queues or workflow state tables for distributed orchestration
