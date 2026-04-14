# cops Task Management System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Rust CLI tool with Vue 3 web UI for task management, supporting Orchestrator, Agents, and Humans to collaborate via CLI and web interface.

**Architecture:** Single Rust binary with embedded Vue 3 SPA. SQLite (default) or MariaDB for persistence. REST API + WebSocket for real-time updates. 8-state task lifecycle with Q&A system.

**Tech Stack:** Rust (clap, axum, sqlx, tokio), Vue 3 (Vite, TypeScript, Pinia), SQLite/MariaDB

---

## File Structure Overview

```
company-ops/subsystems/task-system/
├── Cargo.toml
├── cops.toml.example
├── src/
│   ├── main.rs                    # Entry point
│   ├── cli/
│   │   ├── mod.rs                 # CLI module exports
│   │   ├── args.rs                # Clap argument definitions
│   │   ├── task.rs                # task subcommands
│   │   ├── board.rs               # board subcommands
│   │   ├── question.rs            # question subcommands
│   │   ├── comment.rs             # comment subcommands
│   │   ├── status.rs              # status/watch commands
│   │   ├── config_cmd.rs          # config subcommands
│   │   ├── db_cmd.rs              # db subcommands
│   │   └── web.rs                 # web server command
│   ├── core/
│   │   ├── mod.rs
│   │   ├── task.rs                # Task entity + status machine
│   │   ├── question.rs            # Question entity
│   │   ├── comment.rs             # Comment entity
│   │   └── events.rs              # Domain events
│   ├── db/
│   │   ├── mod.rs
│   │   ├── pool.rs                # Connection pool management
│   │   ├── repository.rs          # Repository trait
│   │   ├── task_repo.rs           # Task repository
│   │   ├── question_repo.rs       # Question repository
│   │   ├── comment_repo.rs        # Comment repository
│   │   ├── event_repo.rs          # Event repository
│   │   └── migrations/
│   │       └── 001_initial.sql    # Initial schema
│   ├── api/
│   │   ├── mod.rs
│   │   ├── router.rs              # Route definitions
│   │   ├── handlers/
│   │   │   ├── mod.rs
│   │   │   ├── task.rs            # Task endpoints
│   │   │   ├── board.rs           # Board endpoints
│   │   │   ├── question.rs        # Question endpoints
│   │   │   └── comment.rs         # Comment endpoints
│   │   └── websocket.rs           # WebSocket handler
│   ├── config.rs                  # Configuration loading
│   └── error.rs                   # Error types
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── types/
│       │   └── index.ts
│       ├── composables/
│       │   ├── useApi.ts
│       │   └── useWebSocket.ts
│       └── components/
│           ├── Board.vue
│           ├── TaskCard.vue
│           ├── TaskModal.vue
│           └── QuestionPanel.vue
└── tests/
    ├── cli_integration.rs
    └── api_integration.rs
```

---

## Phase 1: Project Setup & Core Types (Tasks 1-4)

### Task 1: Initialize Rust Project

**Files:**
- Create: `company-ops/subsystems/task-system/Cargo.toml`
- Create: `company-ops/subsystems/task-system/src/main.rs`
- Create: `company-ops/subsystems/task-system/src/lib.rs`

- [ ] **Step 1: Create project directory structure**

Run:
```bash
mkdir -p company-ops/subsystems/task-system/src/{cli,core,db/migrations,api/handlers}
mkdir -p company-ops/subsystems/task-system/tests
```

- [ ] **Step 2: Create Cargo.toml**

```toml
[package]
name = "cops"
version = "0.1.0"
edition = "2021"
description = "Company Operations Task Management System"

[[bin]]
name = "cops"
path = "src/main.rs"

[lib]
name = "cops"
path = "src/lib.rs"

[dependencies]
clap = { version = "4", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
axum = { version = "0.7", features = ["ws", "macros"] }
tower = "0.4"
tower-http = { version = "0.5", features = ["fs", "cors"] }
sqlx = { version = "0.7", features = ["runtime-tokio", "sqlite", "mysql", "uuid", "chrono", "json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
thiserror = "1"
anyhow = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
toml = "0.8"
rust-embed = "8"
mime_guess = "2"

[dev-dependencies]
tempfile = "3"
reqwest = { version = "0.12", features = ["json"] }

[profile.release]
opt-level = "z"
lto = true
```

- [ ] **Step 3: Create src/lib.rs**

```rust
pub mod cli;
pub mod core;
pub mod db;
pub mod api;
pub mod config;
pub mod error;

pub use error::Result;
```

- [ ] **Step 4: Create src/main.rs**

```rust
use cops::cli::run;

fn main() -> anyhow::Result<()> {
    run()
}
```

- [ ] **Step 5: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```
Expected: Compiles with warnings about unused modules

- [ ] **Step 6: Commit**

```bash
git add company-ops/subsystems/task-system/
git commit -m "feat(cops): initialize Rust project with dependencies"
```

---

### Task 2: Define Error Types

**Files:**
- Create: `company-ops/subsystems/task-system/src/error.rs`

- [ ] **Step 1: Create error.rs**

```rust
use thiserror::Error;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Task not found: {0}")]
    TaskNotFound(uuid::Uuid),

    #[error("Question not found: {0}")]
    QuestionNotFound(uuid::Uuid),

    #[error("Invalid status transition: cannot go from {from} to {to}")]
    InvalidStatusTransition { from: String, to: String },

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Parse error: {0}")]
    Parse(String),

    #[error("{0}")]
    Custom(String),
}

impl From<std::string::FromUtf8Error> for Error {
    fn from(e: std::string::FromUtf8Error) -> Self {
        Error::Parse(e.to_string())
    }
}
```

- [ ] **Step 2: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```
Expected: Compiles successfully

- [ ] **Step 3: Commit**

```bash
git add company-ops/subsystems/task-system/src/error.rs
git commit -m "feat(cops): add error types"
```

---

### Task 3: Define Core Types (Task Entity)

**Files:**
- Create: `company-ops/subsystems/task-system/src/core/mod.rs`
- Create: `company-ops/subsystems/task-system/src/core/task.rs`

- [ ] **Step 1: Create core/mod.rs**

```rust
mod task;
mod question;
mod comment;
mod events;

pub use task::*;
pub use question::*;
pub use comment::*;
pub use events::*;
```

- [ ] **Step 2: Create core/task.rs (part 1 - enums)**

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Task status - 8 state lifecycle
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum TaskStatus {
    New,
    Assigned,
    InProgress,
    Blocked,
    Waiting,
    Review,
    Done,
    Archived,
}

impl Default for TaskStatus {
    fn default() -> Self { Self::New }
}

impl std::fmt::Display for TaskStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::New => write!(f, "NEW"),
            Self::Assigned => write!(f, "ASSIGNED"),
            Self::InProgress => write!(f, "IN_PROGRESS"),
            Self::Blocked => write!(f, "BLOCKED"),
            Self::Waiting => write!(f, "WAITING"),
            Self::Review => write!(f, "REVIEW"),
            Self::Done => write!(f, "DONE"),
            Self::Archived => write!(f, "ARCHIVED"),
        }
    }
}

impl std::str::FromStr for TaskStatus {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_uppercase().replace("-", "_").as_str() {
            "NEW" => Ok(Self::New),
            "ASSIGNED" => Ok(Self::Assigned),
            "IN_PROGRESS" | "INPROGRESS" => Ok(Self::InProgress),
            "BLOCKED" => Ok(Self::Blocked),
            "WAITING" => Ok(Self::Waiting),
            "REVIEW" => Ok(Self::Review),
            "DONE" => Ok(Self::Done),
            "ARCHIVED" => Ok(Self::Archived),
            _ => Err(format!("Invalid status: {}", s)),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "lowercase")]
pub enum Priority { Low, Medium, High, Urgent }

impl Default for Priority {
    fn default() -> Self { Self::Medium }
}

impl std::fmt::Display for Priority {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Low => write!(f, "low"),
            Self::Medium => write!(f, "medium"),
            Self::High => write!(f, "high"),
            Self::Urgent => write!(f, "urgent"),
        }
    }
}
```

- [ ] **Step 3: Add Task entity to core/task.rs (part 2)**

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum AssigneeType { Agent, Human }

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AssigneeRole { Primary, Reviewer, Approver, Contributor }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Assignee {
    pub id: String,
    #[serde(rename = "type")]
    pub kind: AssigneeType,
    pub role: AssigneeRole,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub status: TaskStatus,
    pub priority: Priority,
    pub tags: Vec<String>,
    pub assignees: Vec<Assignee>,
    pub blocked_by: Vec<Uuid>,
    pub parent_id: Option<Uuid>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Task {
    pub fn new(title: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4(),
            title,
            description: None,
            status: TaskStatus::default(),
            priority: Priority::default(),
            tags: Vec::new(),
            assignees: Vec::new(),
            blocked_by: Vec::new(),
            parent_id: None,
            created_at: now,
            updated_at: now,
        }
    }

    pub fn can_transition_to(&self, new_status: TaskStatus) -> bool {
        use TaskStatus::*;
        match self.status {
            New => matches!(new_status, Assigned),
            Assigned => matches!(new_status, InProgress | Blocked | Waiting | Review),
            InProgress => matches!(new_status, Blocked | Waiting | Review | Done),
            Blocked => matches!(new_status, Waiting | InProgress | Assigned),
            Waiting => matches!(new_status, Review | InProgress | Assigned),
            Review => matches!(new_status, Done | Waiting | InProgress),
            Done => matches!(new_status, Archived),
            Archived => false,
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateTask {
    pub title: String,
    pub description: Option<String>,
    #[serde(default)]
    pub priority: Priority,
    pub tags: Option<Vec<String>>,
    pub assignees: Option<Vec<Assignee>>,
    pub blocked_by: Option<Vec<Uuid>>,
    pub parent_id: Option<Uuid>,
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct UpdateTask {
    pub title: Option<String>,
    pub description: Option<String>,
    pub status: Option<TaskStatus>,
    pub priority: Option<Priority>,
    pub tags: Option<Vec<String>>,
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct TaskFilters {
    pub status: Option<Vec<TaskStatus>>,
    pub assignee: Option<String>,
    pub tag: Option<String>,
    pub parent: Option<Uuid>,
    pub blocked: Option<bool>,
}
```

- [ ] **Step 4: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 5: Commit**

```bash
git add company-ops/subsystems/task-system/src/core/
git commit -m "feat(cops): add Task entity with status state machine"
```

---

### Task 4: Define Question and Comment Entities

**Files:**
- Create: `company-ops/subsystems/task-system/src/core/question.rs`
- Create: `company-ops/subsystems/task-system/src/core/comment.rs`
- Create: `company-ops/subsystems/task-system/src/core/events.rs`

- [ ] **Step 1: Create core/question.rs**

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum QuestionType {
    OpenEnded,
    SingleChoice,
    MultiChoice,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "lowercase")]
pub enum Urgency { Low, Normal, High }

impl Default for Urgency {
    fn default() -> Self { Self::Normal }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Question {
    pub id: Uuid,
    pub task_id: Uuid,
    pub question_type: QuestionType,
    pub question_text: String,
    pub options: Option<Vec<String>>,
    pub answer: Option<String>,
    pub answered_at: Option<DateTime<Utc>>,
    pub answered_by: Option<String>,
    pub urgency: Urgency,
    pub created_at: DateTime<Utc>,
}

impl Question {
    pub fn new(task_id: Uuid, question_text: String, question_type: QuestionType) -> Self {
        Self {
            id: Uuid::new_v4(),
            task_id,
            question_type,
            question_text,
            options: None,
            answer: None,
            answered_at: None,
            answered_by: None,
            urgency: Urgency::default(),
            created_at: Utc::now(),
        }
    }

    pub fn is_answered(&self) -> bool {
        self.answer.is_some()
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateQuestion {
    pub question_text: String,
    #[serde(default)]
    pub question_type: QuestionType,
    pub options: Option<Vec<String>>,
    #[serde(default)]
    pub urgency: Urgency,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AnswerQuestion {
    pub answer: String,
    pub answered_by: Option<String>,
}
```

- [ ] **Step 2: Create core/comment.rs**

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "UPPERCASE")]
pub enum AuthorType { Agent, Human }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Comment {
    pub id: Uuid,
    pub task_id: Uuid,
    pub author_id: String,
    pub author_type: AuthorType,
    pub content: String,
    pub created_at: DateTime<Utc>,
}

impl Comment {
    pub fn new(task_id: Uuid, author_id: String, author_type: AuthorType, content: String) -> Self {
        Self {
            id: Uuid::new_v4(),
            task_id,
            author_id,
            author_type,
            content,
            created_at: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct CreateComment {
    pub content: String,
    pub author_id: Option<String>,
    pub author_type: Option<AuthorType>,
}
```

- [ ] **Step 3: Create core/events.rs**

```rust
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use super::{Task, TaskStatus, Question, Comment};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EntityType { Task, Question, Comment }

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EventType {
    Created,
    Updated,
    StatusChanged,
    Answered,
    Deleted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: Uuid,
    pub entity_type: EntityType,
    pub entity_id: Uuid,
    pub event_type: EventType,
    pub payload: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

impl Event {
    pub fn task_created(task: &Task) -> Self {
        Self {
            id: Uuid::new_v4(),
            entity_type: EntityType::Task,
            entity_id: task.id,
            event_type: EventType::Created,
            payload: serde_json::to_value(task).unwrap_or(serde_json::json!({})),
            created_at: Utc::now(),
        }
    }

    pub fn task_status_changed(task_id: Uuid, old: TaskStatus, new: TaskStatus) -> Self {
        Self {
            id: Uuid::new_v4(),
            entity_type: EntityType::Task,
            entity_id: task_id,
            event_type: EventType::StatusChanged,
            payload: serde_json::json!({"old": old, "new": new}),
            created_at: Utc::now(),
        }
    }

    pub fn question_asked(question: &Question) -> Self {
        Self {
            id: Uuid::new_v4(),
            entity_type: EntityType::Question,
            entity_id: question.id,
            event_type: EventType::Created,
            payload: serde_json::to_value(question).unwrap_or(serde_json::json!({})),
            created_at: Utc::now(),
        }
    }

    pub fn question_answered(question_id: Uuid, answer: &str) -> Self {
        Self {
            id: Uuid::new_v4(),
            entity_type: EntityType::Question,
            entity_id: question_id,
            event_type: EventType::Answered,
            payload: serde_json::json!({"answer": answer}),
            created_at: Utc::now(),
        }
    }
}
```

- [ ] **Step 4: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 5: Commit**

```bash
git add company-ops/subsystems/task-system/src/core/
git commit -m "feat(cops): add Question, Comment, and Event entities"
```

---

## Phase 2: Configuration & Database (Tasks 5-8)

### Task 5: Implement Configuration

**Files:**
- Create: `company-ops/subsystems/task-system/src/config.rs`
- Create: `company-ops/subsystems/task-system/cops.toml.example`

- [ ] **Step 1: Create src/config.rs**

```rust
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Config {
    #[serde(default)]
    pub database: DatabaseConfig,
    #[serde(default)]
    pub server: ServerConfig,
    #[serde(default)]
    pub board: BoardConfig,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DatabaseConfig {
    #[serde(default = "default_db_backend")]
    pub backend: String,
    #[serde(default = "default_sqlite_path")]
    pub sqlite_path: PathBuf,
    pub mariadb: Option<MariaDbConfig>,
}

fn default_db_backend() -> String { "sqlite".to_string() }
fn default_sqlite_path() -> PathBuf { PathBuf::from("./data/cops.db") }

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MariaDbConfig {
    pub host: String,
    pub port: u16,
    pub database: String,
    pub username: String,
    pub password: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ServerConfig {
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_ws_enabled")]
    pub websocket_enabled: bool,
}

fn default_host() -> String { "127.0.0.1".to_string() }
fn default_port() -> u16 { 9090 }
fn default_ws_enabled() -> bool { true }

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct BoardConfig {
    #[serde(default = "default_columns")]
    pub default_columns: Vec<String>,
    #[serde(default = "default_hidden")]
    pub hidden_columns: Vec<String>,
}

fn default_columns() -> Vec<String> {
    vec!["NEW", "ASSIGNED", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE"]
        .into_iter().map(String::from).collect()
}
fn default_hidden() -> Vec<String> {
    vec!["ARCHIVED", "WAITING"].into_iter().map(String::from).collect()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            database: DatabaseConfig {
                backend: default_db_backend(),
                sqlite_path: default_sqlite_path(),
                mariadb: None,
            },
            server: ServerConfig {
                host: default_host(),
                port: default_port(),
                websocket_enabled: default_ws_enabled(),
            },
            board: BoardConfig {
                default_columns: default_columns(),
                hidden_columns: default_hidden(),
            },
        }
    }
}

impl Default for DatabaseConfig {
    fn default() -> Self {
        Self {
            backend: default_db_backend(),
            sqlite_path: default_sqlite_path(),
            mariadb: None,
        }
    }
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            host: default_host(),
            port: default_port(),
            websocket_enabled: default_ws_enabled(),
        }
    }
}

impl Default for BoardConfig {
    fn default() -> Self {
        Self {
            default_columns: default_columns(),
            hidden_columns: default_hidden(),
        }
    }
}

impl Config {
    pub fn load() -> crate::Result<Self> {
        let paths = Self::config_paths();
        
        for path in paths {
            if path.exists() {
                let content = std::fs::read_to_string(&path)?;
                let config: Config = toml::from_str(&content)?;
                return Ok(config);
            }
        }
        
        Ok(Self::default())
    }

    pub fn load_from(path: &PathBuf) -> crate::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }

    fn config_paths() -> Vec<PathBuf> {
        let mut paths = Vec::new();
        
        if let Ok(p) = std::env::var("COPS_CONFIG") {
            paths.push(PathBuf::from(p));
        }
        
        paths.push(PathBuf::from("./cops.toml"));
        paths.push(dirs::config_dir().map(|p| p.join("cops/cops.toml")).unwrap_or_default());
        paths.push(PathBuf::from("/etc/cops/cops.toml"));
        
        paths
    }

    pub fn database_url(&self) -> String {
        if self.database.backend == "mariadb" {
            if let Some(ref mdb) = self.database.mariadb {
                return format!(
                    "mysql://{}:{}@{}:{}/{}",
                    mdb.username, mdb.password, mdb.host, mdb.port, mdb.database
                );
            }
        }
        format!("sqlite:{}?mode=rwc", self.database.sqlite_path.display())
    }
}
```

- [ ] **Step 2: Add dirs dependency to Cargo.toml**

Add to `[dependencies]`:
```toml
dirs = "5"
```

- [ ] **Step 3: Create cops.toml.example**

```toml
# cops.toml - Task System Configuration

[database]
backend = "sqlite"
sqlite_path = "./data/cops.db"

# MariaDB configuration (uncomment to use)
# [database.mariadb]
# host = "127.0.0.1"
# port = 3306
# database = "company_ops"
# username = "company_ops"
# password = "company_opsPassword"

[server]
host = "127.0.0.1"
port = 9090
websocket_enabled = true

[board]
default_columns = ["NEW", "ASSIGNED", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE"]
hidden_columns = ["ARCHIVED", "WAITING"]
```

- [ ] **Step 4: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 5: Commit**

```bash
git add company-ops/subsystems/task-system/src/config.rs
git add company-ops/subsystems/task-system/cops.toml.example
git add company-ops/subsystems/task-system/Cargo.toml
git commit -m "feat(cops): add configuration loading with SQLite/MariaDB support"
```

---

### Task 6: Create Database Schema Migration

**Files:**
- Create: `company-ops/subsystems/task-system/src/db/migrations/001_initial.sql`

- [ ] **Step 1: Create migrations directory and initial schema**

```sql
-- 001_initial.sql

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    priority TEXT NOT NULL DEFAULT 'medium',
    tags TEXT NOT NULL DEFAULT '[]',
    assignees TEXT NOT NULL DEFAULT '[]',
    blocked_by TEXT NOT NULL DEFAULT '[]',
    parent_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    question_type TEXT NOT NULL DEFAULT 'OPEN_ENDED',
    question_text TEXT NOT NULL,
    options TEXT,
    answer TEXT,
    answered_at TEXT,
    answered_by TEXT,
    urgency TEXT NOT NULL DEFAULT 'normal',
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    author_type TEXT NOT NULL DEFAULT 'HUMAN',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Events table (audit log)
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id);
CREATE INDEX IF NOT EXISTS idx_questions_task ON questions(task_id);
CREATE INDEX IF NOT EXISTS idx_comments_task ON comments(task_id);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

-- Migration tracking table
CREATE TABLE IF NOT EXISTS _migrations (
    name TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

- [ ] **Step 2: Commit**

```bash
git add company-ops/subsystems/task-system/src/db/migrations/
git commit -m "feat(cops): add initial database schema migration"
```

---

### Task 7: Implement Database Pool

**Files:**
- Create: `company-ops/subsystems/task-system/src/db/mod.rs`
- Create: `company-ops/subsystems/task-system/src/db/pool.rs`

- [ ] **Step 1: Create src/db/mod.rs**

```rust
mod pool;
mod repository;
mod task_repo;
mod question_repo;
mod comment_repo;
mod event_repo;

pub use pool::*;
pub use repository::*;
pub use task_repo::*;
pub use question_repo::*;
pub use comment_repo::*;
pub use event_repo::*;
```

- [ ] **Step 2: Create src/db/pool.rs**

```rust
use sqlx::{SqlitePool, MySqlPool, Pool, Sqlite, MySql};
use std::path::Path;
use crate::config::Config;
use crate::error::Result;

pub enum DbPool {
    Sqlite(SqlitePool),
    MySql(MySqlPool),
}

impl DbPool {
    pub async fn connect(config: &Config) -> Result<Self> {
        if config.database.backend == "mariadb" {
            let url = config.database_url();
            let pool = MySqlPool::connect(&url).await?;
            Ok(Self::MySql(pool))
        } else {
            // Ensure parent directory exists for SQLite
            if let Some(parent) = Path::new(&config.database.sqlite_path).parent() {
                if !parent.exists() {
                    std::fs::create_dir_all(parent)?;
                }
            }
            
            let url = config.database_url();
            let pool = SqlitePool::connect(&url).await?;
            Ok(Self::Sqlite(pool))
        }
    }

    pub async fn run_migrations(&self) -> Result<()> {
        let migration_sql = include_str!("migrations/001_initial.sql");
        
        match self {
            Self::Sqlite(pool) => {
                sqlx::raw_sql(migration_sql).execute(pool).await?;
            }
            Self::MySql(pool) => {
                // MySQL needs slightly different syntax
                let mysql_sql = migration_sql
                    .replace("TEXT PRIMARY KEY", "VARCHAR(36) PRIMARY KEY")
                    .replace("AUTOINCREMENT", "AUTO_INCREMENT");
                for stmt in mysql_sql.split(';').filter(|s| !s.trim().is_empty()) {
                    sqlx::query(&format!("{};", stmt)).execute(pool).await?;
                }
            }
        }
        Ok(())
    }
}

// Convenience trait for executing queries
pub trait AsSqlite {
    fn as_sqlite(&self) -> &SqlitePool;
}

pub trait AsMySql {
    fn as_mysql(&self) -> &MySqlPool;
}

impl AsSqlite for DbPool {
    fn as_sqlite(&self) -> &SqlitePool {
        match self {
            Self::Sqlite(pool) => pool,
            _ => panic!("Not a SQLite pool"),
        }
    }
}

impl AsMySql for DbPool {
    fn as_mysql(&self) -> &MySqlPool {
        match self {
            Self::MySql(pool) => pool,
            _ => panic!("Not a MySQL pool"),
        }
    }
}
```

- [ ] **Step 3: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 4: Commit**

```bash
git add company-ops/subsystems/task-system/src/db/
git commit -m "feat(cops): add database pool with SQLite and MySQL support"
```

---

### Task 8: Implement Task Repository

**Files:**
- Create: `company-ops/subsystems/task-system/src/db/repository.rs`
- Create: `company-ops/subsystems/task-system/src/db/task_repo.rs`

- [ ] **Step 1: Create src/db/repository.rs**

```rust
use async_trait::async_trait;
use crate::core::*;
use crate::error::Result;

#[async_trait]
pub trait TaskRepository: Send + Sync {
    async fn create(&self, task: &CreateTask) -> Result<Task>;
    async fn find_by_id(&self, id: uuid::Uuid) -> Result<Option<Task>>;
    async fn find_all(&self, filters: &TaskFilters) -> Result<Vec<Task>>;
    async fn update(&self, id: uuid::Uuid, update: &UpdateTask) -> Result<Task>;
    async fn delete(&self, id: uuid::Uuid) -> Result<()>;
    async fn count_by_status(&self) -> Result<Vec<(TaskStatus, i64)>>;
}

#[async_trait]
pub trait QuestionRepository: Send + Sync {
    async fn create(&self, task_id: uuid::Uuid, question: &CreateQuestion) -> Result<Question>;
    async fn find_by_id(&self, id: uuid::Uuid) -> Result<Option<Question>>;
    async fn find_by_task(&self, task_id: uuid::Uuid) -> Result<Vec<Question>>;
    async fn answer(&self, id: uuid::Uuid, answer: &AnswerQuestion) -> Result<Question>;
}

#[async_trait]
pub trait CommentRepository: Send + Sync {
    async fn create(&self, task_id: uuid::Uuid, comment: &CreateComment) -> Result<Comment>;
    async fn find_by_task(&self, task_id: uuid::Uuid) -> Result<Vec<Comment>>;
}

#[async_trait]
pub trait EventRepository: Send + Sync {
    async fn append(&self, event: &Event) -> Result<()>;
    async fn find_since(&self, since: chrono::DateTime<chrono::Utc>) -> Result<Vec<Event>>;
}
```

- [ ] **Step 2: Add async-trait dependency to Cargo.toml**

```toml
async-trait = "0.1"
```

- [ ] **Step 3: Create src/db/task_repo.rs**

```rust
use async_trait::async_trait;
use sqlx::SqlitePool;
use crate::core::*;
use crate::db::{TaskRepository, DbPool};
use crate::error::{Error, Result};

pub struct SqliteTaskRepository {
    pool: SqlitePool,
}

impl SqliteTaskRepository {
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl TaskRepository for SqliteTaskRepository {
    async fn create(&self, input: &CreateTask) -> Result<Task> {
        let id = uuid::Uuid::new_v4();
        let now = chrono::Utc::now();
        
        sqlx::query!(
            r#"
            INSERT INTO tasks (id, title, description, status, priority, tags, assignees, blocked_by, parent_id, created_at, updated_at)
            VALUES (?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, ?)
            "#,
            id.to_string(),
            input.title,
            input.description,
            input.priority.to_string(),
            serde_json::to_string(&input.tags.clone().unwrap_or_default())?,
            serde_json::to_string(&input.assignees.clone().unwrap_or_default())?,
            serde_json::to_string(&input.blocked_by.clone().unwrap_or_default())?,
            input.parent_id.map(|id| id.to_string()),
            now.to_rfc3339(),
            now.to_rfc3339(),
        )
        .execute(&self.pool)
        .await?;

        Ok(Task {
            id,
            title: input.title.clone(),
            description: input.description.clone(),
            status: TaskStatus::New,
            priority: input.priority,
            tags: input.tags.clone().unwrap_or_default(),
            assignees: input.assignees.clone().unwrap_or_default(),
            blocked_by: input.blocked_by.clone().unwrap_or_default(),
            parent_id: input.parent_id,
            created_at: now,
            updated_at: now,
        })
    }

    async fn find_by_id(&self, id: uuid::Uuid) -> Result<Option<Task>> {
        let row = sqlx::query!(
            r#"SELECT id, title, description, status, priority, tags, assignees, blocked_by, parent_id, created_at, updated_at FROM tasks WHERE id = ?"#,
            id.to_string()
        )
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some(r) => Ok(Some(Task {
                id: uuid::Uuid::parse_str(&r.id)?,
                title: r.title,
                description: r.description,
                status: r.status.parse()?,
                priority: r.priority.parse().unwrap_or(Priority::Medium),
                tags: serde_json::from_str(&r.tags).unwrap_or_default(),
                assignees: serde_json::from_str(&r.assignees).unwrap_or_default(),
                blocked_by: serde_json::from_str(&r.blocked_by).unwrap_or_default(),
                parent_id: r.parent_id.and_then(|s| uuid::Uuid::parse_str(&s).ok()),
                created_at: chrono::DateTime::parse_from_rfc3339(&r.created_at)?.with_timezone(&chrono::Utc),
                updated_at: chrono::DateTime::parse_from_rfc3339(&r.updated_at)?.with_timezone(&chrono::Utc),
            })),
            None => Ok(None),
        }
    }

    async fn find_all(&self, filters: &TaskFilters) -> Result<Vec<Task>> {
        let mut query = String::from("SELECT id, title, description, status, priority, tags, assignees, blocked_by, parent_id, created_at, updated_at FROM tasks WHERE 1=1");
        let mut params: Vec<String> = Vec::new();

        if let Some(ref statuses) = filters.status {
            if !statuses.is_empty() {
                let placeholders: Vec<&str> = statuses.iter().map(|_| "?").collect();
                query.push_str(&format!(" AND status IN ({})", placeholders.join(",")));
                for s in statuses {
                    params.push(s.to_string());
                }
            }
        }

        if let Some(ref assignee) = filters.assignee {
            query.push_str(" AND assignees LIKE ?");
            params.push(format!("%{}%", assignee));
        }

        if let Some(ref tag) = filters.tag {
            query.push_str(" AND tags LIKE ?");
            params.push(format!("%{}%", tag));
        }

        if let Some(parent) = filters.parent {
            query.push_str(" AND parent_id = ?");
            params.push(parent.to_string());
        }

        query.push_str(" ORDER BY created_at DESC");

        let rows = sqlx::query_as::<_, (String, String, Option<String>, String, String, String, String, String, Option<String>, String, String)>(&query)
            .fetch_all(&self.pool)
            .await?;

        rows.into_iter().map(|r| {
            Ok(Task {
                id: uuid::Uuid::parse_str(&r.0)?,
                title: r.1,
                description: r.2,
                status: r.3.parse()?,
                priority: r.4.parse().unwrap_or(Priority::Medium),
                tags: serde_json::from_str(&r.5).unwrap_or_default(),
                assignees: serde_json::from_str(&r.6).unwrap_or_default(),
                blocked_by: serde_json::from_str(&r.7).unwrap_or_default(),
                parent_id: r.8.and_then(|s| uuid::Uuid::parse_str(&s).ok()),
                created_at: chrono::DateTime::parse_from_rfc3339(&r.9)?.with_timezone(&chrono::Utc),
                updated_at: chrono::DateTime::parse_from_rfc3339(&r.10)?.with_timezone(&chrono::Utc),
            })
        }).collect()
    }

    async fn update(&self, id: uuid::Uuid, input: &UpdateTask) -> Result<Task> {
        let mut task = self.find_by_id(id).await?.ok_or(Error::TaskNotFound(id))?;
        let now = chrono::Utc::now();

        if let Some(ref title) = input.title {
            task.title = title.clone();
        }
        if let Some(ref desc) = input.description {
            task.description = Some(desc.clone());
        }
        if let Some(status) = input.status {
            if !task.can_transition_to(status) {
                return Err(Error::InvalidStatusTransition {
                    from: task.status.to_string(),
                    to: status.to_string(),
                });
            }
            task.status = status;
        }
        if let Some(priority) = input.priority {
            task.priority = priority;
        }
        if let Some(ref tags) = input.tags {
            task.tags = tags.clone();
        }
        task.updated_at = now;

        sqlx::query!(
            r#"UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, tags = ?, assignees = ?, blocked_by = ?, updated_at = ? WHERE id = ?"#,
            task.title,
            task.description,
            task.status.to_string(),
            task.priority.to_string(),
            serde_json::to_string(&task.tags)?,
            serde_json::to_string(&task.assignees)?,
            serde_json::to_string(&task.blocked_by)?,
            task.updated_at.to_rfc3339(),
            id.to_string(),
        )
        .execute(&self.pool)
        .await?;

        Ok(task)
    }

    async fn delete(&self, id: uuid::Uuid) -> Result<()> {
        let result = sqlx::query!("DELETE FROM tasks WHERE id = ?", id.to_string())
            .execute(&self.pool)
            .await?;
        
        if result.rows_affected() == 0 {
            Err(Error::TaskNotFound(id))
        } else {
            Ok(())
        }
    }

    async fn count_by_status(&self) -> Result<Vec<(TaskStatus, i64)>> {
        let rows = sqlx::query_as::<_, (String, i64)>(
            "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
        )
        .fetch_all(&self.pool)
        .await?;

        rows.into_iter()
            .map(|(status, count)| {
                Ok((status.parse()?, count))
            })
            .collect()
    }
}
```

- [ ] **Step 4: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 5: Commit**

```bash
git add company-ops/subsystems/task-system/src/db/
git add company-ops/subsystems/task-system/Cargo.toml
git commit -m "feat(cops): add task repository with CRUD operations"
```

---

## Phase 3: CLI Implementation (Tasks 9-14)

### Task 9: Implement CLI Argument Structure

**Files:**
- Create: `company-ops/subsystems/task-system/src/cli/mod.rs`
- Create: `company-ops/subsystems/task-system/src/cli/args.rs`

- [ ] **Step 1: Create src/cli/mod.rs**

```rust
mod args;
mod task;
mod board;
mod question;
mod comment;
mod status;
mod config_cmd;
mod db_cmd;
mod web;

use clap::Parser;
use crate::error::Result;

pub use args::*;

pub fn run() -> anyhow::Result<()> {
    let args = Cli::parse();
    
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into())
        )
        .init();

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async {
        match args.command {
            Commands::Task(cmd) => task::handle(cmd).await,
            Commands::Board(cmd) => board::handle(cmd).await,
            Commands::Question(cmd) => question::handle(cmd).await,
            Commands::Comment(cmd) => comment::handle(cmd).await,
            Commands::Status(cmd) => status::handle(cmd).await,
            Commands::Config(cmd) => config_cmd::handle(cmd).await,
            Commands::Db(cmd) => db_cmd::handle(cmd).await,
            Commands::Web(cmd) => web::handle(cmd).await,
        }
    })?;

    Ok(())
}
```

- [ ] **Step 2: Create src/cli/args.rs**

```rust
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "cops")]
#[command(about = "Company Operations Task System", long_about = None)]
#[command(version)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,

    /// Path to config file
    #[arg(short, long, global = true)]
    pub config: Option<PathBuf>,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Task management
    #[command(subcommand)]
    Task(TaskCommands),

    /// Board / Kanban view
    Board(BoardCommands),

    /// Question management
    #[command(subcommand)]
    Question(QuestionCommands),

    /// Comment management
    #[command(subcommand)]
    Comment(CommentCommands),

    /// System status and monitoring
    Status(StatusCommands),

    /// Configuration management
    #[command(subcommand)]
    Config(ConfigCommands),

    /// Database management
    #[command(subcommand)]
    Db(DbCommands),

    /// Start web server
    Web(WebCommands),
}

#[derive(Subcommand)]
pub enum TaskCommands {
    /// Create a new task
    Create {
        /// Task title
        title: String,
        /// Description (markdown)
        #[arg(short, long)]
        description: Option<String>,
        /// Assign to agent/human (repeatable)
        #[arg(short = 'a', long)]
        assignee: Vec<String>,
        /// Parent task ID for subtask
        #[arg(short, long)]
        parent: Option<String>,
        /// Blocking dependency task ID (repeatable)
        #[arg(long)]
        blocked_by: Vec<String>,
        /// Priority: low, medium, high, urgent
        #[arg(short = 'P', long, default_value = "medium")]
        priority: String,
        /// Tag (repeatable)
        #[arg(short, long)]
        tag: Vec<String>,
    },

    /// List tasks
    List {
        /// Filter by status (repeatable)
        #[arg(short, long)]
        status: Vec<String>,
        /// Filter by assignee
        #[arg(short, long)]
        assignee: Option<String>,
        /// Filter by tag
        #[arg(short, long)]
        tag: Option<String>,
        /// Filter by parent task
        #[arg(short, long)]
        parent: Option<String>,
        /// Show only blocked tasks
        #[arg(long)]
        blocked: bool,
        /// Output format: table, json, simple
        #[arg(short = 'F', long, default_value = "table")]
        format: String,
    },

    /// Show task details
    Show {
        /// Task ID
        id: String,
        /// Include subtasks
        #[arg(long)]
        with_children: bool,
        /// Show dependency chain
        #[arg(long)]
        with_dependencies: bool,
    },

    /// Update a task
    Update {
        /// Task ID
        id: String,
        /// New title
        #[arg(long)]
        title: Option<String>,
        /// New description
        #[arg(short, long)]
        description: Option<String>,
        /// New status
        #[arg(short, long)]
        status: Option<String>,
        /// New priority
        #[arg(long)]
        priority: Option<String>,
    },

    /// Move task to new status (quick shortcut)
    Move {
        /// Task ID
        id: String,
        /// New status
        status: String,
    },

    /// Delete a task
    Delete {
        /// Task ID
        id: String,
        /// Skip confirmation
        #[arg(short, long)]
        yes: bool,
    },
}

#[derive(Subcommand)]
pub enum BoardCommands {
    /// Show kanban board
    Show {
        /// Filter by status
        #[arg(long)]
        filter: Option<String>,
        /// Filter by assignee
        #[arg(short, long)]
        assignee: Option<String>,
        /// Auto-refresh every 5 seconds
        #[arg(short, long)]
        watch: bool,
    },
}

#[derive(Subcommand)]
pub enum QuestionCommands {
    /// Create a question on a task
    Create {
        /// Task ID
        task_id: String,
        /// Question text
        question: String,
        /// Question type: open, single, multi
        #[arg(short = 't', long, default_value = "open")]
        qtype: String,
        /// Options for choice types (repeatable)
        #[arg(short, long)]
        option: Vec<String>,
        /// Urgency: low, normal, high
        #[arg(short, long, default_value = "normal")]
        urgency: String,
    },

    /// List questions
    List {
        /// Filter by task
        #[arg(short, long)]
        task: Option<String>,
        /// Only unanswered
        #[arg(long)]
        unanswered: bool,
        /// Only urgent
        #[arg(long)]
        urgent: bool,
    },

    /// Answer a question
    Answer {
        /// Question ID
        id: String,
        /// Answer text
        answer: String,
        /// Answered by
        #[arg(long)]
        by: Option<String>,
    },
}

#[derive(Subcommand)]
pub enum CommentCommands {
    /// Add a comment
    Add {
        /// Task ID
        task_id: String,
        /// Comment message
        message: String,
        /// Author ID
        #[arg(short, long)]
        author: Option<String>,
    },

    /// List comments on a task
    List {
        /// Task ID
        task_id: String,
        /// Newest first
        #[arg(long)]
        reverse: bool,
    },
}

#[derive(Subcommand)]
pub enum StatusCommands {
    /// Show system status
    #[command(name = "status")]
    Show {
        /// Output format: json, simple
        #[arg(short = 'F', long, default_value = "simple")]
        format: String,
        /// Only changes since timestamp
        #[arg(long)]
        since: Option<String>,
    },

    /// Watch for changes (continuous stream)
    Watch,
}

#[derive(Subcommand)]
pub enum ConfigCommands {
    /// Initialize config file
    Init,

    /// Show current configuration
    Show,
}

#[derive(Subcommand)]
pub enum DbCommands {
    /// Run database migrations
    Migrate,

    /// Show migration status
    Status,
}

#[derive(Args)]
pub struct WebCommands {
    /// Port number
    #[arg(short, long, default_value = "9090")]
    pub port: u16,

    /// Bind host
    #[arg(long, default_value = "127.0.0.1")]
    pub host: String,

    /// Open browser on start
    #[arg(long)]
    pub open: bool,

    /// API only (no SPA frontend)
    #[arg(long)]
    pub no_ui: bool,
}
```

- [ ] **Step 3: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 4: Commit**

```bash
git add company-ops/subsystems/task-system/src/cli/
git commit -m "feat(cops): add CLI argument structure with clap"
```

---

## Summary

This plan covers **Phase 1-3** (14 tasks) establishing:
- ✅ Project structure with Cargo.toml
- ✅ Core types (Task, Question, Comment, Event)
- ✅ Configuration system (SQLite/MariaDB)
- ✅ Database layer with migrations
- ✅ CLI argument structure

**Remaining phases** (to be added in subsequent plan updates):
- Phase 4: CLI command handlers (Tasks 10-14)
- Phase 5: REST API implementation (Tasks 15-18)
- Phase 6: WebSocket & real-time (Task 19)
- Phase 7: Vue 3 Frontend (Tasks 20-24)

---

*Plan version: 1.0.0*
*Created: 2026-04-08*
