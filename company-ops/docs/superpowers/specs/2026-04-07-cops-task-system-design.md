# cops - Rust Task Management System Design Spec

> **Version**: 1.0.0
> **Created**: 2026-04-07
> **Status**: Approved

---

## 1. Overview

### 1.1 Purpose

`cops` (company operations) is a standalone Rust CLI tool for task management, providing unified access via CLI and Web UI for Orchestrator, Agents, and Humans to collaborate on company tasks.

### 1.2 Problem Statement

The existing company-ops architecture lacks a dedicated task coordination system that:
- Provides multi-terminal access (CLI + Web)
- Supports structured Q&A between agents and humans
- Enables real-time task tracking for Orchestrator monitoring loops

### 1.3 Solution

A Rust-based CLI tool with embedded Vue 3 SPA, using SQLite (default) or MariaDB for persistence.

---

## 2. Architecture

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Systems                          │
│                                                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│   │ Orchestrator│    │  cc-connect │    │   Human User    │   │
│   │ (polling)   │    │  (CLI calls)│    │ (Web UI / CLI)  │   │
│   │             │    │             │    │                 │   │
│   │ cops status │    │ cops task   │    │ cops web        │   │
│   └──────┬──────┘    └──────┬──────┘    └────────┬────────┘   │
│          │                  │                     │             │
└──────────┼──────────────────┼─────────────────────┼─────────────┘
           │                  │                     │
           ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                          cops CLI                                │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    CLI Layer (clap)                      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                            │                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                   Core Services                          │  │
│   │   Task Engine │ Q&A System │ Relationship Manager        │  │
│   └─────────────────────────────────────────────────────────┘  │
│                            │                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    Data Layer                            │  │
│   │   SQLite (default) │ MariaDB (optional)                 │  │
│   └─────────────────────────────────────────────────────────┘  │
│                            │                                    │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                 Web Server (Axum)                        │  │
│   │   REST API ◄──────────────► Vue 3 SPA (bundled)         │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Deployment Model

- **Single binary**: All functionality in one `cops` executable
- **Embedded frontend**: Vue 3 SPA bundled into binary via `rust-embed`
- **Local database**: SQLite file in project directory (default) or MariaDB
- **No auth**: Single-user system, no authentication required

### 2.3 Integration Pattern

`cops` is a **passive subsystem** — it does not initiate connections to external systems. Other components call `cops` via:
- CLI commands (subprocess execution)
- REST API (when web server is running)
- WebSocket (for real-time updates)

---

## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌─────────────────────────────────┐
│             TASK                │
├─────────────────────────────────┤
│ id: UUID (PK)                   │
│ title: TEXT                     │
│ description: TEXT               │
│ status: ENUM (8 states)         │
│ priority: ENUM                  │
│ tags: JSON                      │
│ assignees: JSON                 │
│ blocked_by: JSON                │
│ parent_id: UUID (FK, nullable)  │
│ created_at: TIMESTAMP           │
│ updated_at: TIMESTAMP           │
└───────────────┬─────────────────┘
                │
                │ 1:N
                ▼
┌─────────────────────────────────┐
│           QUESTION              │
├─────────────────────────────────┤
│ id: UUID (PK)                   │
│ task_id: UUID (FK)              │
│ question_type: ENUM             │
│ question_text: TEXT             │
│ options: JSON (optional)        │
│ answer: TEXT (nullable)         │
│ answered_at: TIMESTAMP          │
│ answered_by: TEXT               │
│ urgency: ENUM                   │
│ created_at: TIMESTAMP           │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│           COMMENT               │
├─────────────────────────────────┤
│ id: UUID (PK)                   │
│ task_id: UUID (FK)              │
│ author_id: TEXT                 │
│ author_type: ENUM (AGENT, HUMAN)│
│ content: TEXT                   │
│ created_at: TIMESTAMP           │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│            EVENT                │
├─────────────────────────────────┤
│ id: UUID (PK)                   │
│ entity_type: ENUM (TASK, QUESTION, COMMENT) │
│ entity_id: UUID                 │
│ event_type: ENUM (CREATED, UPDATED, STATUS_CHANGED, ANSWERED) │
│ payload: JSON                   │
│ created_at: TIMESTAMP           │
└─────────────────────────────────┘
```

### 3.2 Task Status State Machine

```
                    ┌─────────┐
                    │   NEW   │
                    └────┬────┘
                         │ assign
                         ▼
                    ┌─────────┐
          ┌────────│ASSIGNED │────────┐
          │        └─────────┘        │
          │             │             │
          │             │ start       │ block
          │             ▼             │
          │        ┌─────────┐        │
          │        │IN_PROG- │        │
          │        │ RESS    │────────┼──────►┌─────────┐
          │        └─────────┘        │       │ BLOCKED │
          │             │             │       └────┬────┘
          │             │ wait        │            │
          │             ▼             │            │ unblock
          │        ┌─────────┐        │            │
          └───────►│ WAITING │◄───────┘◄───────────┘
                   └────┬────┘
                        │ ready
                        ▼
                   ┌─────────┐
                   │ REVIEW  │
                   └────┬────┘
                        │ approve
                        ▼
                   ┌─────────┐        ┌──────────┐
                   │  DONE   │───────►│ ARCHIVED │
                   └─────────┘        └──────────┘
```

### 3.3 Field Definitions

#### Task.assignees Format
```json
[
  {"id": "tech-agent-001", "type": "AGENT", "role": "primary"},
  {"id": "product-agent", "type": "AGENT", "role": "reviewer"},
  {"id": "human-001", "type": "HUMAN", "role": "approver"}
]
```

#### Task.blocked_by Format
```json
["uuid-1", "uuid-2"]  // Task cannot proceed until these are DONE
```

#### Question Types
| Type | Description | options field |
|------|-------------|---------------|
| `OPEN_ENDED` | Free text answer | null |
| `SINGLE_CHOICE` | Select one option | `["A", "B", "C"]` |
| `MULTI_CHOICE` | Select multiple | `["Red", "Blue", "Green"]` |

---

## 4. CLI Interface

### 4.1 Command Structure

Git-style subcommands:

```bash
cops <noun> <verb> [options]
```

### 4.2 Command Reference

#### Task Management

```bash
cops task create <title> [options]
  --description, -d <text>      Task description (markdown)
  --assignee, -a <id>           Assign to agent/human (repeatable)
  --parent, -p <task-id>        Parent task for subtask
  --blocked-by <task-id>        Dependency task (repeatable)
  --priority <level>            low | medium | high | urgent
  --tags <tag>                  Tags (repeatable)

cops task list [options]
  --status <state>              Filter by status (repeatable)
  --assignee <id>               Filter by assignee
  --tag <tag>                   Filter by tag
  --parent <task-id>            Filter by parent task
  --blocked                     Show only blocked tasks
  --format <fmt>                table | json | simple

cops task show <task-id>
  --with-children               Include subtasks
  --with-dependencies           Show dependency chain

cops task update <task-id> [options]
  --status <state>              New status
  --add-assignee <id>           Add assignee
  --remove-assignee <id>        Remove assignee
  --description <text>          Update description
  --blocked-by <id>             Add blocking dependency
  --unblock <id>                Remove blocking dependency

cops task move <task-id> <status>
  # Quick status change shortcut
```

#### Board / Kanban

```bash
cops board show [options]
  --filter <status>             Column filter
  --assignee <id>               Filter by assignee
  --watch                       Auto-refresh every 5s

cops board view <view-name>
  # Saved board views (defined in config)
```

#### Q&A System

```bash
cops question create <task-id> <question> [options]
  --type <type>                 open | single | multi
  --options <opt>               Options for choice types (repeatable)
  --urgency <level>             low | normal | high

cops question list [options]
  --task <task-id>              Filter by task
  --unanswered                  Only unanswered questions
  --urgent                      Only urgent questions

cops question answer <question-id> <answer>
  # Answer a question (free text or option key)
```

#### Comment Thread

```bash
cops comment add <task-id> <message>
  --author <id>                 Author ID (default: system)

cops comment list <task-id>
  --reverse                     Newest first
```

#### Monitoring

```bash
cops status [options]
  --format <fmt>                json | simple
  --since <timestamp>           Only changes since time
  --watch                       Stream changes (JSON lines)

cops watch
  # Continuous event stream (for Orchestrator polling)
```

#### Web Server

```bash
cops web [options]
  --port <port>                 Port number (default: 9090)
  --host <host>                 Bind host (default: 127.0.0.1)
  --open                        Open browser on start
  --no-ui                       API only (no SPA frontend)
```

#### Configuration

```bash
cops config init
  # Initialize cops.toml in current directory

cops config show
  # Display current configuration
```

#### Database

```bash
cops db migrate
  # Run database migrations

cops db status
  # Show migration status
```

### 4.3 Output Formats

| Format | Use Case |
|--------|----------|
| `table` | Human reading (default) |
| `json` | Scripting, Orchestrator parsing |
| `simple` | Quick terminal scanning |

---

## 5. REST API

### 5.1 Endpoints

#### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | List tasks (filterable) |
| `GET` | `/api/tasks/:id` | Get single task |
| `POST` | `/api/tasks` | Create task |
| `PATCH` | `/api/tasks/:id` | Update task |
| `DELETE` | `/api/tasks/:id` | Delete task |
| `POST` | `/api/tasks/:id/assign` | Assign/unassign |
| `POST` | `/api/tasks/:id/block` | Add dependency |
| `DELETE` | `/api/tasks/:id/block/:depId` | Remove dependency |
| `POST` | `/api/tasks/:id/move` | Change status |

#### Board

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/board` | Get board columns with tasks |
| `GET` | `/api/board/views` | List saved views |
| `GET` | `/api/board/views/:name` | Get saved view |

#### Questions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks/:id/questions` | List questions for task |
| `POST` | `/api/tasks/:id/questions` | Create question |
| `PATCH` | `/api/questions/:id` | Update question |
| `POST` | `/api/questions/:id/answer` | Answer question |

#### Comments

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks/:id/comments` | List comments |
| `POST` | `/api/tasks/:id/comments` | Add comment |

### 5.2 WebSocket Events

| Event | Payload | When Fired |
|-------|---------|------------|
| `task.created` | Task object | New task created |
| `task.updated` | Task + changed fields | Task modified |
| `task.moved` | Task ID + old/new status | Status changed |
| `question.asked` | Question object | New question created |
| `question.answered` | Question ID + answer | Question answered |

---

## 6. Web UI

### 6.1 Technology

- **Framework**: Vue 3 with Composition API
- **Build**: Vite
- **State**: Pinia (optional, for complex state)
- **HTTP**: fetch API with composables
- **WebSocket**: native WebSocket API

### 6.2 Views

| View | Description |
|------|-------------|
| Board | Kanban board with drag-drop |
| Task Detail | Modal with task info, comments, questions |
| Search | Global search results |

### 6.3 Features

- **Drag & Drop**: Move tasks between columns
- **Real-time**: WebSocket updates board without refresh
- **Dark theme only**: Matches developer workflow
- **Responsive**: Works on desktop and tablet

---

## 7. Configuration

### 7.1 Config File (`cops.toml`)

```toml
# cops.toml - Task System Configuration

[database]
backend = "sqlite"                    # "sqlite" or "mariadb"
sqlite.path = "./data/cops.db"

# MariaDB (when backend = "mariadb")
# mariadb.host = "127.0.0.1"
# mariadb.port = 3306
# mariadb.database = "company_ops"
# mariadb.username = "company_ops"
# mariadb.password = "company_opsPassword"

[server]
host = "127.0.0.1"
port = 9090
websocket.enabled = true

[board]
default_columns = ["NEW", "ASSIGNED", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE"]
hidden_columns = ["ARCHIVED", "WAITING"]

[agents.tech-agent]
name = "Tech Agent"
type = "AGENT"

[agents.product-agent]
name = "Product Agent"
type = "AGENT"

[agents.human-001]
name = "Founder"
type = "HUMAN"
```

### 7.2 Config File Locations (search order)

1. `--config /path/to/cops.toml` (CLI flag)
2. `$COPS_CONFIG` (environment variable)
3. `./cops.toml` (current directory)
4. `~/.config/cops/cops.toml` (user config)
5. `/etc/cops/cops.toml` (system config)

### 7.3 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COPS_CONFIG` | Path to config file | `./cops.toml` |
| `COPS_DB_PATH` | SQLite database path | `./data/cops.db` |
| `COPS_PORT` | Web server port | `9090` |
| `COPS_LOG_LEVEL` | Logging level | `info` |

---

## 8. Project Structure

```
company-ops/subsystems/task-system/
├── Cargo.toml
├── README.md
├── cops.toml.example
│
├── src/
│   ├── main.rs
│   │
│   ├── cli/
│   │   ├── mod.rs
│   │   ├── task.rs
│   │   ├── board.rs
│   │   ├── question.rs
│   │   ├── comment.rs
│   │   ├── status.rs
│   │   └── web.rs
│   │
│   ├── core/
│   │   ├── mod.rs
│   │   ├── task.rs
│   │   ├── question.rs
│   │   ├── comment.rs
│   │   ├── relationships.rs
│   │   └── events.rs
│   │
│   ├── db/
│   │   ├── mod.rs
│   │   ├── sqlite.rs
│   │   ├── mariadb.rs
│   │   ├── migrations/
│   │   └── traits.rs
│   │
│   ├── api/
│   │   ├── mod.rs
│   │   ├── routes.rs
│   │   ├── handlers/
│   │   └── websocket.rs
│   │
│   └── config.rs
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   ├── composables/
│   │   └── types/
│   └── dist/                  # Bundled into binary
│
└── tests/
    ├── cli_tests.rs
    ├── api_tests.rs
    └── integration/
```

---

## 9. Dependencies

### 9.1 Rust (Cargo.toml)

| Crate | Version | Purpose |
|-------|---------|---------|
| `clap` | 4.x | CLI argument parsing |
| `tokio` | 1.x | Async runtime |
| `axum` | 0.7.x | Web framework |
| `tower-http` | 0.5.x | Middleware (CORS, fs) |
| `sqlx` | 0.7.x | Database (SQLite, MySQL) |
| `serde` | 1.x | JSON serialization |
| `uuid` | 1.x | UUID generation |
| `chrono` | 0.4.x | Timestamps |
| `thiserror` | 1.x | Error handling |
| `tracing` | 0.1.x | Logging |
| `toml` | 0.8.x | Config parsing |
| `rust-embed` | 8.x | Embed frontend |

### 9.2 Frontend (package.json)

| Package | Version | Purpose |
|---------|---------|---------|
| `vue` | ^3.4 | UI framework |
| `@vueuse/core` | ^10 | Composables |
| `pinia` | ^2 | State management |
| `vite` | ^5 | Build tool |
| `typescript` | ^5 | Type checking |

---

## 10. MVP Scope

### 10.1 Included

- ✅ Task CRUD with 8-state lifecycle
- ✅ Kanban board (Web UI)
- ✅ Q&A system (questions + comments)
- ✅ Subtasks and dependencies
- ✅ Multi-assignee support
- ✅ CLI + Web access
- ✅ Polling status for Orchestrator
- ✅ SQLite and MariaDB support

### 10.2 Future (Post-MVP)

- ❌ Metrics/Charts
- ❌ Activity feed timeline
- ❌ System health panel
- ❌ Authentication
- ❌ Task templates
- ❌ Bulk operations
- ❌ Export/Import

---

## 11. Success Criteria

| Criteria | Measurement |
|----------|-------------|
| CLI responsiveness | All commands complete < 100ms |
| Web UI load time | Initial load < 500ms |
| WebSocket latency | Events delivered < 50ms |
| Database operations | All queries < 10ms |
| Binary size | < 20MB (release build) |

---

*Document version: 1.0.0*
*Last updated: 2026-04-07*
