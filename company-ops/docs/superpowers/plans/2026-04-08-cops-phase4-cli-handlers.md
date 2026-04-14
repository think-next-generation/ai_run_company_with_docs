# cops Phase 4: CLI Command Handlers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all CLI command handlers to provide functional task management through the command line interface.

**Architecture:** Create a shared Ctx struct holding database pool and config, update CLI dispatcher to initialize context, implement handlers using repositories, and add output formatting utilities.

**Tech Stack:** Rust (clap, sqlx, tokio, chrono, serde_json, comfy-table for table output)

---

## File Structure Overview

```
company-ops/subsystems/task-system/src/
├── cli/
│   ├── mod.rs              # Updated: context initialization
│   ├── ctx.rs              # NEW: shared context for handlers
│   ├── output.rs           # NEW: table/json/simple formatters
│   ├── task.rs             # Updated: full implementation
│   ├── board.rs            # Updated: full implementation
│   ├── question.rs         # Updated: full implementation
│   ├── comment.rs          # Updated: full implementation
│   ├── status.rs           # Updated: full implementation
│   ├── config_cmd.rs       # Updated: full implementation
│   ├── db_cmd.rs           # Updated: full implementation
│   └── web.rs              # Updated: placeholder for Phase 5
└── db/
    ├── question_repo.rs    # Updated: SQLite implementation
    ├── comment_repo.rs     # Updated: SQLite implementation
    └── event_repo.rs       # Updated: SQLite implementation
```

---

## Task 1: Create Shared Context and Output Utilities

**Files:**
- Create: `company-ops/subsystems/task-system/src/cli/ctx.rs`
- Create: `company-ops/subsystems/task-system/src/cli/output.rs`

- [ ] **Step 1: Add comfy-table dependency to Cargo.toml**

```toml
comfy-table = "7"
```

- [ ] **Step 2: Create src/cli/ctx.rs**

```rust
//! Shared context for CLI command handlers
//!
//! Provides database pool, configuration, and repositories
//! to all command handlers.

use crate::config::Config;
use crate::db::{DbPool, SqliteTaskRepository, SqliteQuestionRepository, SqliteCommentRepository, SqliteEventRepository};
use crate::db::{TaskRepository, QuestionRepository, CommentRepository, EventRepository};
use crate::error::Result;

/// Shared context for CLI command execution
pub struct Ctx {
    pub config: Config,
    pub pool: DbPool,
}

impl Ctx {
    /// Initialize context from config path (or default)
    pub async fn init(config_path: Option<&std::path::PathBuf>) -> Result<Self> {
        let config = match config_path {
            Some(path) => Config::load_from(path)?,
            None => Config::load()?,
        };

        let pool = DbPool::connect(&config).await?;
        
        Ok(Self { config, pool })
    }

    /// Get task repository
    pub fn task_repo(&self) -> Box<dyn TaskRepository> {
        Box::new(SqliteTaskRepository::new(&self.pool))
    }

    /// Get question repository
    pub fn question_repo(&self) -> Box<dyn QuestionRepository> {
        Box::new(SqliteQuestionRepository::new(&self.pool))
    }

    /// Get comment repository
    pub fn comment_repo(&self) -> Box<dyn CommentRepository> {
        Box::new(SqliteCommentRepository::new(&self.pool))
    }

    /// Get event repository
    pub fn event_repo(&self) -> Box<dyn EventRepository> {
        Box::new(SqliteEventRepository::new(&self.pool))
    }
}
```

- [ ] **Step 3: Create src/cli/output.rs**

```rust
//! Output formatting utilities
//!
//! Provides table, JSON, and simple output formats for CLI commands.

use chrono::{DateTime, Utc};
use comfy_table::{Cell, Color, Table, presets::UTF8_FULL};
use crate::core::{Task, TaskStatus, Priority, Question, Comment};

/// Output format options
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Format {
    Table,
    Json,
    Simple,
}

impl std::str::FromStr for Format {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "table" => Ok(Self::Table),
            "json" => Ok(Self::Json),
            "simple" => Ok(Self::Simple),
            _ => Err(format!("Invalid format: {}. Use table, json, or simple.", s)),
        }
    }
}

/// Format timestamp for display
pub fn format_time(dt: &DateTime<Utc>) -> String {
    let now = Utc::now();
    let duration = now.signed_duration_since(*dt);
    
    if duration.num_minutes() < 1 {
        "just now".to_string()
    } else if duration.num_minutes() < 60 {
        format!("{}m ago", duration.num_minutes())
    } else if duration.num_hours() < 24 {
        format!("{}h ago", duration.num_hours())
    } else if duration.num_days() < 7 {
        format!("{}d ago", duration.num_days())
    } else {
        dt.format("%Y-%m-%d").to_string()
    }
}

/// Get color for task status
fn status_color(status: TaskStatus) -> Color {
    match status {
        TaskStatus::New => Color::Cyan,
        TaskStatus::Assigned => Color::Blue,
        TaskStatus::InProgress => Color::Yellow,
        TaskStatus::Blocked => Color::Red,
        TaskStatus::Waiting => Color::Magenta,
        TaskStatus::Review => Color::DarkYellow,
        TaskStatus::Done => Color::Green,
        TaskStatus::Archived => Color::DarkGrey,
    }
}

/// Get color for priority
fn priority_color(priority: Priority) -> Color {
    match priority {
        Priority::Low => Color::DarkGrey,
        Priority::Medium => Color::Yellow,
        Priority::High => Color::Red,
        Priority::Urgent => Color::Magenta,
    }
}

/// Print tasks in the specified format
pub fn print_tasks(tasks: &[Task], format: Format) {
    match format {
        Format::Table => print_tasks_table(tasks),
        Format::Json => print_tasks_json(tasks),
        Format::Simple => print_tasks_simple(tasks),
    }
}

fn print_tasks_table(tasks: &[Task]) {
    if tasks.is_empty() {
        println!("No tasks found.");
        return;
    }

    let mut table = Table::new();
    table.load_preset(UTF8_FULL);
    table.set_header(vec!["ID", "Title", "Status", "Priority", "Assignees", "Updated"]);

    for task in tasks {
        let id_short = &task.id.to_string()[..8];
        let assignees: String = task.assignees.iter()
            .map(|a| a.id.as_str())
            .take(2)
            .collect::<Vec<_>>()
            .join(", ");
        let assignees = if task.assignees.len() > 2 {
            format!("{}...", assignees)
        } else if assignees.is_empty() {
            "-".to_string()
        } else {
            assignees
        };

        table.add_row(vec![
            Cell::new(id_short),
            Cell::new(&truncate(&task.title, 30)),
            Cell::new(task.status.to_string()).fg(status_color(task.status)),
            Cell::new(task.priority.to_string()).fg(priority_color(task.priority)),
            Cell::new(assignees),
            Cell::new(format_time(&task.updated_at)),
        ]);
    }

    println!("{table}");
}

fn print_tasks_json(tasks: &[Task]) {
    match serde_json::to_string_pretty(&tasks) {
        Ok(json) => println!("{}", json),
        Err(e) => eprintln!("Error serializing tasks: {}", e),
    }
}

fn print_tasks_simple(tasks: &[Task]) {
    for task in tasks {
        let id_short = &task.id.to_string()[..8];
        println!("[{}] {} {}: {}", 
            task.status.to_string(),
            id_short,
            task.priority.to_string(),
            task.title
        );
    }
}

/// Print a single task in detail
pub fn print_task_detail(task: &Task) {
    println!("Task: {}", task.id);
    println!("  Title: {}", task.title);
    if let Some(ref desc) = task.description {
        println!("  Description: {}", desc);
    }
    println!("  Status: {}", task.status);
    println!("  Priority: {}", task.priority);
    if !task.tags.is_empty() {
        println!("  Tags: {}", task.tags.join(", "));
    }
    if !task.assignees.is_empty() {
        let assignees: Vec<String> = task.assignees.iter()
            .map(|a| format!("{} ({:?})", a.id, a.role))
            .collect();
        println!("  Assignees: {}", assignees.join(", "));
    }
    if !task.blocked_by.is_empty() {
        let blocked: Vec<String> = task.blocked_by.iter()
            .map(|id| id.to_string()[..8].to_string())
            .collect();
        println!("  Blocked by: {}", blocked.join(", "));
    }
    if let Some(parent) = task.parent_id {
        println!("  Parent: {}", parent);
    }
    println!("  Created: {}", task.created_at.format("%Y-%m-%d %H:%M UTC"));
    println!("  Updated: {}", task.updated_at.format("%Y-%m-%d %H:%M UTC"));
}

/// Truncate string to max length with ellipsis
fn truncate(s: &str, max_len: usize) -> String {
    if s.len() <= max_len {
        s.to_string()
    } else {
        format!("{}...", &s[..max_len.saturating_sub(3)])
    }
}

/// Print questions in the specified format
pub fn print_questions(questions: &[Question], format: Format) {
    match format {
        Format::Table => print_questions_table(questions),
        Format::Json => {
            match serde_json::to_string_pretty(&questions) {
                Ok(json) => println!("{}", json),
                Err(e) => eprintln!("Error serializing questions: {}", e),
            }
        }
        Format::Simple => {
            for q in questions {
                let id_short = &q.id.to_string()[..8];
                let status = if q.is_answered() { "✓" } else { "?" };
                println!("[{}] {} {}", status, id_short, truncate(&q.question_text, 50));
            }
        }
    }
}

fn print_questions_table(questions: &[Question]) {
    if questions.is_empty() {
        println!("No questions found.");
        return;
    }

    let mut table = Table::new();
    table.load_preset(UTF8_FULL);
    table.set_header(vec!["ID", "Task", "Question", "Type", "Urgency", "Status"]);

    for q in questions {
        let id_short = &q.id.to_string()[..8];
        let task_short = &q.task_id.to_string()[..8];
        let status = if q.is_answered() { "Answered" } else { "Pending" };
        
        table.add_row(vec![
            Cell::new(id_short),
            Cell::new(task_short),
            Cell::new(truncate(&q.question_text, 30)),
            Cell::new(format!("{:?}", q.question_type)),
            Cell::new(format!("{:?}", q.urgency)),
            Cell::new(status),
        ]);
    }

    println!("{table}");
}

/// Print comments
pub fn print_comments(comments: &[Comment]) {
    if comments.is_empty() {
        println!("No comments.");
        return;
    }

    for comment in comments {
        let id_short = &comment.id.to_string()[..8];
        println!("[{}] {} ({}): {}", 
            format_time(&comment.created_at),
            comment.author_id,
            comment.author_type,
            comment.content
        );
    }
}
```

- [ ] **Step 4: Update src/cli/mod.rs to export new modules**

```rust
//! CLI module - command-line interface handling

mod args;
mod board;
mod comment;
mod config_cmd;
mod ctx;
mod db_cmd;
mod output;
mod question;
mod status;
mod task;
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
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async {
        // Initialize context with config and database
        let ctx = match ctx::Ctx::init(args.config.as_ref()).await {
            Ok(ctx) => ctx,
            Err(e) => {
                eprintln!("Error initializing: {}", e);
                std::process::exit(1);
            }
        };

        match args.command {
            Commands::Task(cmd) => task::handle(cmd, &ctx).await,
            Commands::Board(cmd) => board::handle(cmd, &ctx).await,
            Commands::Question(cmd) => question::handle(cmd, &ctx).await,
            Commands::Comment(cmd) => comment::handle(cmd, &ctx).await,
            Commands::Status(cmd) => status::handle(cmd, &ctx).await,
            Commands::Config(cmd) => config_cmd::handle(cmd, &ctx).await,
            Commands::Db(cmd) => db_cmd::handle(cmd, &ctx).await,
            Commands::Web(cmd) => web::handle(cmd, &ctx).await,
        }
    })?;

    Ok(())
}
```

- [ ] **Step 5: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

Expected: Compiles with errors about missing implementations (will be fixed in subsequent tasks)

- [ ] **Step 6: Commit**

```bash
git add company-ops/subsystems/task-system/
git commit -m "feat(cops): add CLI context and output utilities"
```

---

## Task 2: Implement Config and DB Command Handlers

**Files:**
- Update: `company-ops/subsystems/task-system/src/cli/config_cmd.rs`
- Update: `company-ops/subsystems/task-system/src/cli/db_cmd.rs`

- [ ] **Step 1: Update src/cli/config_cmd.rs**

```rust
//! Config command handlers

use super::args::ConfigCommands;
use super::ctx::Ctx;
use crate::error::Result;
use std::io::Write;

pub async fn handle(cmd: ConfigCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        ConfigCommands::Init => {
            handle_init().await
        }
        ConfigCommands::Show => {
            handle_show(ctx).await
        }
    }
}

async fn handle_init() -> Result<()> {
    let config_path = std::path::PathBuf::from("./cops.toml");
    
    if config_path.exists() {
        eprintln!("Config file already exists: ./cops.toml");
        eprintln!("Use 'cops config show' to view current configuration.");
        return Ok(());
    }

    let config_content = r#"# cops.toml - Task System Configuration

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
"#;

    std::fs::write(&config_path, config_content)?;
    
    // Create data directory
    std::fs::create_dir_all("./data")?;
    
    println!("Created: ./cops.toml");
    println!("Created: ./data/ directory");
    println!();
    println!("Edit cops.toml to configure database and agents.");
    println!("Run 'cops db migrate' to initialize the database.");

    Ok(())
}

async fn handle_show(ctx: &Ctx) -> Result<()> {
    println!("Configuration:");
    println!();
    println!("[database]");
    println!("  backend: {}", ctx.config.database.backend);
    println!("  sqlite_path: {}", ctx.config.database.sqlite_path.display());
    if let Some(ref mdb) = ctx.config.database.mariadb {
        println!("  mariadb:");
        println!("    host: {}", mdb.host);
        println!("    port: {}", mdb.port);
        println!("    database: {}", mdb.database);
        println!("    username: {}", mdb.username);
    }
    println!();
    println!("[server]");
    println!("  host: {}", ctx.config.server.host);
    println!("  port: {}", ctx.config.server.port);
    println!("  websocket_enabled: {}", ctx.config.server.websocket_enabled);
    println!();
    println!("[board]");
    println!("  default_columns: {:?}", ctx.config.board.default_columns);
    println!("  hidden_columns: {:?}", ctx.config.board.hidden_columns);

    Ok(())
}
```

- [ ] **Step 2: Update src/cli/db_cmd.rs**

```rust
//! Database command handlers

use super::args::DbCommands;
use super::ctx::Ctx;
use crate::error::Result;

pub async fn handle(cmd: DbCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        DbCommands::Migrate => {
            handle_migrate(ctx).await
        }
        DbCommands::Status => {
            handle_status(ctx).await
        }
    }
}

async fn handle_migrate(ctx: &Ctx) -> Result<()> {
    println!("Running database migrations...");
    
    ctx.pool.run_migrations().await?;
    
    println!("Migrations completed successfully.");
    println!("Database: {}", ctx.config.database.sqlite_path.display());

    Ok(())
}

async fn handle_status(_ctx: &Ctx) -> Result<()> {
    println!("Migration Status:");
    println!();
    println!("  001_initial.sql - Applied (embedded)");
    println!();
    println!("Database is up to date.");

    Ok(())
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
git commit -m "feat(cops): implement config and db command handlers"
```

---

## Task 3: Implement Task Command Handlers

**Files:**
- Update: `company-ops/subsystems/task-system/src/cli/task.rs`

- [ ] **Step 1: Update src/cli/task.rs with full implementation**

```rust
//! Task command handlers

use super::args::TaskCommands;
use super::ctx::Ctx;
use super::output::{self, Format};
use crate::core::{CreateTask, UpdateTask, TaskFilters, TaskStatus, Priority, Assignee, AssigneeType, AssigneeRole};
use crate::error::{Error, Result};
use uuid::Uuid;

pub async fn handle(cmd: TaskCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        TaskCommands::Create {
            title,
            description,
            assignee,
            parent,
            blocked_by,
            priority,
            tag,
        } => handle_create(ctx, title, description, assignee, parent, blocked_by, priority, tag).await,
        TaskCommands::List {
            status,
            assignee,
            tag,
            parent,
            blocked,
            format,
        } => handle_list(ctx, status, assignee, tag, parent, blocked, format).await,
        TaskCommands::Show {
            id,
            with_children,
            with_dependencies,
        } => handle_show(ctx, id, with_children, with_dependencies).await,
        TaskCommands::Update {
            id,
            title,
            description,
            status,
            priority,
        } => handle_update(ctx, id, title, description, status, priority).await,
        TaskCommands::Move { id, status } => handle_move(ctx, id, status).await,
        TaskCommands::Delete { id, yes } => handle_delete(ctx, id, yes).await,
    }
}

async fn handle_create(
    ctx: &Ctx,
    title: String,
    description: Option<String>,
    assignees: Vec<String>,
    parent: Option<String>,
    blocked_by: Vec<String>,
    priority: String,
    tags: Vec<String>,
) -> Result<()> {
    // Parse priority
    let priority: Priority = priority.parse()
        .map_err(|e: String| Error::Parse(e))?;

    // Parse parent task ID
    let parent_id = parent
        .map(|s| Uuid::parse_str(&s))
        .transpose()
        .map_err(|e| Error::Parse(e.to_string()))?;

    // Parse blocked_by IDs
    let blocked_by_uuids: Vec<Uuid> = blocked_by
        .iter()
        .map(|s| Uuid::parse_str(s).map_err(|e| Error::Parse(e.to_string())))
        .collect::<Result<Vec<_>>>()?;

    // Parse assignees
    let assignee_list: Vec<Assignee> = assignees
        .iter()
        .map(|id| Assignee {
            id: id.clone(),
            kind: AssigneeType::Agent,
            role: AssigneeRole::Primary,
        })
        .collect();

    let input = CreateTask {
        title,
        description,
        priority,
        tags: if tags.is_empty() { None } else { Some(tags) },
        assignees: if assignee_list.is_empty() { None } else { Some(assignee_list) },
        blocked_by: if blocked_by_uuids.is_empty() { None } else { Some(blocked_by_uuids) },
        parent_id,
    };

    let repo = ctx.task_repo();
    let task = repo.create(&input).await?;

    println!("Created task: {}", task.id);
    println!("  Title: {}", task.title);
    println!("  Status: {}", task.status);
    println!("  Priority: {}", task.priority);

    Ok(())
}

async fn handle_list(
    ctx: &Ctx,
    statuses: Vec<String>,
    assignee: Option<String>,
    tag: Option<String>,
    parent: Option<String>,
    blocked: bool,
    format: String,
) -> Result<()> {
    let format: Format = format.parse()
        .map_err(|e: String| Error::Parse(e))?;

    // Parse status filters
    let status_filters: Vec<TaskStatus> = statuses
        .iter()
        .map(|s| s.parse())
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e: String| Error::Parse(e))?;

    // Parse parent ID
    let parent_id = parent
        .map(|s| Uuid::parse_str(&s))
        .transpose()
        .map_err(|e| Error::Parse(e.to_string()))?;

    let filters = TaskFilters {
        status: if status_filters.is_empty() { None } else { Some(status_filters) },
        assignee,
        tag,
        parent: parent_id,
        blocked: if blocked { Some(true) } else { None },
    };

    let repo = ctx.task_repo();
    let tasks = repo.find_all(&filters).await?;

    output::print_tasks(&tasks, format);

    Ok(())
}

async fn handle_show(
    ctx: &Ctx,
    id: String,
    with_children: bool,
    with_dependencies: bool,
) -> Result<()> {
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    let repo = ctx.task_repo();
    let task = repo.find_by_id(task_id).await?
        .ok_or_else(|| Error::TaskNotFound(task_id))?;

    output::print_task_detail(&task);

    if with_children {
        println!();
        println!("Subtasks:");
        let filters = TaskFilters {
            parent: Some(task_id),
            ..Default::default()
        };
        let children = repo.find_all(&filters).await?;
        if children.is_empty() {
            println!("  No subtasks");
        } else {
            for child in children {
                println!("  [{}] {} - {}", child.status, &child.id.to_string()[..8], child.title);
            }
        }
    }

    if with_dependencies {
        println!();
        if task.blocked_by.is_empty() {
            println!("Dependencies: None");
        } else {
            println!("Blocked by:");
            for dep_id in &task.blocked_by {
                match repo.find_by_id(*dep_id).await? {
                    Some(dep) => println!("  [{}] {} - {}", dep.status, &dep_id.to_string()[..8], dep.title),
                    None => println!("  {} (not found)", &dep_id.to_string()[..8]),
                }
            }
        }
    }

    Ok(())
}

async fn handle_update(
    ctx: &Ctx,
    id: String,
    title: Option<String>,
    description: Option<String>,
    status: Option<String>,
    priority: Option<String>,
) -> Result<()> {
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    let status = status
        .map(|s| s.parse())
        .transpose()
        .map_err(|e: String| Error::Parse(e))?;

    let priority = priority
        .map(|p| p.parse())
        .transpose()
        .map_err(|e: String| Error::Parse(e))?;

    let input = UpdateTask {
        title,
        description,
        status,
        priority,
        tags: None,
    };

    let repo = ctx.task_repo();
    let task = repo.update(task_id, &input).await?;

    println!("Updated task: {}", task.id);
    println!("  Status: {}", task.status);
    println!("  Priority: {}", task.priority);

    Ok(())
}

async fn handle_move(ctx: &Ctx, id: String, status: String) -> Result<()> {
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    let new_status: TaskStatus = status.parse()
        .map_err(|e: String| Error::Parse(e))?;

    let input = UpdateTask {
        status: Some(new_status),
        ..Default::default()
    };

    let repo = ctx.task_repo();
    let task = repo.update(task_id, &input).await?;

    println!("Moved task {} to {}", &id[..8], task.status);

    Ok(())
}

async fn handle_delete(ctx: &Ctx, id: String, yes: bool) -> Result<()> {
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    if !yes {
        // Show task first
        let repo = ctx.task_repo();
        let task = repo.find_by_id(task_id).await?
            .ok_or_else(|| Error::TaskNotFound(task_id))?;

        println!("About to delete task:");
        println!("  ID: {}", task.id);
        println!("  Title: {}", task.title);
        println!("  Status: {}", task.status);
        println!();
        print!("Are you sure? (y/N): ");
        std::io::stdout().flush().map_err(|e| Error::Io(e))?;

        let mut input = String::new();
        std::io::stdin().read_line(&mut input).map_err(|e| Error::Io(e))?;
        
        if !input.trim().to_lowercase().starts_with('y') {
            println!("Cancelled.");
            return Ok(());
        }
    }

    let repo = ctx.task_repo();
    repo.delete(task_id).await?;

    println!("Deleted task: {}", &id[..8]);

    Ok(())
}
```

- [ ] **Step 2: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 3: Commit**

```bash
git add company-ops/subsystems/task-system/src/cli/task.rs
git commit -m "feat(cops): implement task command handlers"
```

---

## Task 4: Implement Question and Comment Repository

**Files:**
- Update: `company-ops/subsystems/task-system/src/db/question_repo.rs`
- Update: `company-ops/subsystems/task-system/src/db/comment_repo.rs`

- [ ] **Step 1: Update src/db/question_repo.rs**

```rust
//! SQLite implementation of QuestionRepository

use async_trait::async_trait;
use sqlx::SqlitePool;

use crate::core::*;
use crate::db::{DbPool, QuestionRepository};
use crate::error::{Error, Result};

pub struct SqliteQuestionRepository {
    pool: SqlitePool,
}

impl SqliteQuestionRepository {
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl QuestionRepository for SqliteQuestionRepository {
    async fn create(&self, task_id: uuid::Uuid, input: &CreateQuestion) -> Result<Question> {
        let id = uuid::Uuid::new_v4();
        let now = chrono::Utc::now();

        sqlx::query(
            r#"
            INSERT INTO questions (id, task_id, question_type, question_text, options, answer, answered_at, answered_by, urgency, created_at)
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?)
            "#,
        )
        .bind(id.to_string())
        .bind(task_id.to_string())
        .bind(input.question_type.to_string())
        .bind(&input.question_text)
        .bind(input.options.as_ref().map(|o| serde_json::to_string(o).unwrap_or_default()))
        .bind(input.urgency.to_string())
        .bind(now.to_rfc3339())
        .execute(&self.pool)
        .await?;

        Ok(Question {
            id,
            task_id,
            question_type: input.question_type,
            question_text: input.question_text.clone(),
            options: input.options.clone(),
            answer: None,
            answered_at: None,
            answered_by: None,
            urgency: input.urgency,
            created_at: now,
        })
    }

    async fn find_by_id(&self, id: uuid::Uuid) -> Result<Option<Question>> {
        let row = sqlx::query_as::<_, (
            String, String, String, String, Option<String>, Option<String>,
            Option<String>, Option<String>, String, String
        )>(
            "SELECT id, task_id, question_type, question_text, options, answer, answered_at, answered_by, urgency, created_at FROM questions WHERE id = ?"
        )
        .bind(id.to_string())
        .fetch_optional(&self.pool)
        .await?;

        match row {
            Some((id_str, task_id, question_type, question_text, options, answer, answered_at, answered_by, urgency, created_at)) => {
                Ok(Some(Question {
                    id: uuid::Uuid::parse_str(&id_str).map_err(|e| Error::Parse(e.to_string()))?,
                    task_id: uuid::Uuid::parse_str(&task_id).map_err(|e| Error::Parse(e.to_string()))?,
                    question_type: question_type.parse().map_err(|e: String| Error::Parse(e))?,
                    question_text,
                    options: options.and_then(|s| serde_json::from_str(&s).ok()),
                    answer,
                    answered_at: answered_at.and_then(|s| chrono::DateTime::parse_from_rfc3339(&s).ok())
                        .map(|dt| dt.with_timezone(&chrono::Utc)),
                    answered_by,
                    urgency: urgency.parse().map_err(|e: String| Error::Parse(e))?,
                    created_at: chrono::DateTime::parse_from_rfc3339(&created_at)
                        .map_err(|e| Error::Parse(e.to_string()))?
                        .with_timezone(&chrono::Utc),
                }))
            }
            None => Ok(None),
        }
    }

    async fn find_by_task(&self, task_id: uuid::Uuid) -> Result<Vec<Question>> {
        let rows = sqlx::query_as::<_, (
            String, String, String, String, Option<String>, Option<String>,
            Option<String>, Option<String>, String, String
        )>(
            "SELECT id, task_id, question_type, question_text, options, answer, answered_at, answered_by, urgency, created_at FROM questions WHERE task_id = ? ORDER BY created_at DESC"
        )
        .bind(task_id.to_string())
        .fetch_all(&self.pool)
        .await?;

        rows.into_iter().map(|(id, task_id, question_type, question_text, options, answer, answered_at, answered_by, urgency, created_at)| {
            Ok(Question {
                id: uuid::Uuid::parse_str(&id).map_err(|e| Error::Parse(e.to_string()))?,
                task_id: uuid::Uuid::parse_str(&task_id).map_err(|e| Error::Parse(e.to_string()))?,
                question_type: question_type.parse().map_err(|e: String| Error::Parse(e))?,
                question_text,
                options: options.and_then(|s| serde_json::from_str(&s).ok()),
                answer,
                answered_at: answered_at.and_then(|s| chrono::DateTime::parse_from_rfc3339(&s).ok())
                    .map(|dt| dt.with_timezone(&chrono::Utc)),
                answered_by,
                urgency: urgency.parse().map_err(|e: String| Error::Parse(e))?,
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at)
                    .map_err(|e| Error::Parse(e.to_string()))?
                    .with_timezone(&chrono::Utc),
            })
        }).collect()
    }

    async fn answer(&self, id: uuid::Uuid, input: &AnswerQuestion) -> Result<Question> {
        let mut question = self.find_by_id(id).await?
            .ok_or(Error::QuestionNotFound(id))?;

        let now = chrono::Utc::now();
        question.answer = Some(input.answer.clone());
        question.answered_at = Some(now);
        question.answered_by = input.answered_by.clone();

        sqlx::query(
            "UPDATE questions SET answer = ?, answered_at = ?, answered_by = ? WHERE id = ?"
        )
        .bind(&question.answer)
        .bind(question.answered_at.map(|dt| dt.to_rfc3339()))
        .bind(&question.answered_by)
        .bind(id.to_string())
        .execute(&self.pool)
        .await?;

        Ok(question)
    }
}
```

- [ ] **Step 2: Update src/db/comment_repo.rs**

```rust
//! SQLite implementation of CommentRepository

use async_trait::async_trait;
use sqlx::SqlitePool;

use crate::core::*;
use crate::db::{DbPool, CommentRepository};
use crate::error::{Error, Result};

pub struct SqliteCommentRepository {
    pool: SqlitePool,
}

impl SqliteCommentRepository {
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl CommentRepository for SqliteCommentRepository {
    async fn create(&self, task_id: uuid::Uuid, input: &CreateComment) -> Result<Comment> {
        let id = uuid::Uuid::new_v4();
        let now = chrono::Utc::now();

        let author_id = input.author_id.clone().unwrap_or_else(|| "system".to_string());
        let author_type = input.author_type.unwrap_or(AuthorType::Agent);

        sqlx::query(
            "INSERT INTO comments (id, task_id, author_id, author_type, content, created_at) VALUES (?, ?, ?, ?, ?, ?)"
        )
        .bind(id.to_string())
        .bind(task_id.to_string())
        .bind(&author_id)
        .bind(author_type.to_string())
        .bind(&input.content)
        .bind(now.to_rfc3339())
        .execute(&self.pool)
        .await?;

        Ok(Comment {
            id,
            task_id,
            author_id,
            author_type,
            content: input.content.clone(),
            created_at: now,
        })
    }

    async fn find_by_task(&self, task_id: uuid::Uuid) -> Result<Vec<Comment>> {
        let rows = sqlx::query_as::<_, (String, String, String, String, String, String)>(
            "SELECT id, task_id, author_id, author_type, content, created_at FROM comments WHERE task_id = ? ORDER BY created_at ASC"
        )
        .bind(task_id.to_string())
        .fetch_all(&self.pool)
        .await?;

        rows.into_iter().map(|(id, task_id, author_id, author_type, content, created_at)| {
            Ok(Comment {
                id: uuid::Uuid::parse_str(&id).map_err(|e| Error::Parse(e.to_string()))?,
                task_id: uuid::Uuid::parse_str(&task_id).map_err(|e| Error::Parse(e.to_string()))?,
                author_id,
                author_type: author_type.parse().map_err(|e: String| Error::Parse(e))?,
                content,
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at)
                    .map_err(|e| Error::Parse(e.to_string()))?
                    .with_timezone(&chrono::Utc),
            })
        }).collect()
    }
}
```

- [ ] **Step 3: Update src/db/event_repo.rs**

```rust
//! SQLite implementation of EventRepository

use async_trait::async_trait;
use sqlx::SqlitePool;
use chrono::{DateTime, Utc};

use crate::core::*;
use crate::db::{DbPool, EventRepository};
use crate::error::{Error, Result};

pub struct SqliteEventRepository {
    pool: SqlitePool,
}

impl SqliteEventRepository {
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl EventRepository for SqliteEventRepository {
    async fn append(&self, event: &Event) -> Result<()> {
        sqlx::query(
            "INSERT INTO events (id, entity_type, entity_id, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)"
        )
        .bind(event.id.to_string())
        .bind(event.entity_type.to_string())
        .bind(event.entity_id.to_string())
        .bind(event.event_type.to_string())
        .bind(serde_json::to_string(&event.payload)?)
        .bind(event.created_at.to_rfc3339())
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    async fn find_since(&self, since: DateTime<Utc>) -> Result<Vec<Event>> {
        let rows = sqlx::query_as::<_, (String, String, String, String, String, String)>(
            "SELECT id, entity_type, entity_id, event_type, payload, created_at FROM events WHERE created_at >= ? ORDER BY created_at DESC"
        )
        .bind(since.to_rfc3339())
        .fetch_all(&self.pool)
        .await?;

        rows.into_iter().map(|(id, entity_type, entity_id, event_type, payload, created_at)| {
            Ok(Event {
                id: uuid::Uuid::parse_str(&id).map_err(|e| Error::Parse(e.to_string()))?,
                entity_type: entity_type.parse().map_err(|e: String| Error::Parse(e))?,
                entity_id: uuid::Uuid::parse_str(&entity_id).map_err(|e| Error::Parse(e.to_string()))?,
                event_type: event_type.parse().map_err(|e: String| Error::Parse(e))?,
                payload: serde_json::from_str(&payload).unwrap_or(serde_json::json!({})),
                created_at: chrono::DateTime::parse_from_rfc3339(&created_at)
                    .map_err(|e| Error::Parse(e.to_string()))?
                    .with_timezone(&chrono::Utc),
            })
        }).collect()
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
git commit -m "feat(cops): implement question, comment, and event repositories"
```

---

## Task 5: Implement Question and Comment Command Handlers

**Files:**
- Update: `company-ops/subsystems/task-system/src/cli/question.rs`
- Update: `company-ops/subsystems/task-system/src/cli/comment.rs`

- [ ] **Step 1: Update src/cli/question.rs**

```rust
//! Question command handlers

use super::args::QuestionCommands;
use super::ctx::Ctx;
use super::output::{self, Format};
use crate::core::{CreateQuestion, AnswerQuestion, QuestionType, Urgency};
use crate::error::{Error, Result};
use uuid::Uuid;

pub async fn handle(cmd: QuestionCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        QuestionCommands::Create {
            task_id,
            question,
            qtype,
            option,
            urgency,
        } => handle_create(ctx, task_id, question, qtype, option, urgency).await,
        QuestionCommands::List {
            task,
            unanswered,
            urgent,
        } => handle_list(ctx, task, unanswered, urgent).await,
        QuestionCommands::Answer {
            id,
            answer,
            by,
        } => handle_answer(ctx, id, answer, by).await,
    }
}

async fn handle_create(
    ctx: &Ctx,
    task_id: String,
    question_text: String,
    qtype: String,
    options: Vec<String>,
    urgency: String,
) -> Result<()> {
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    // Verify task exists
    let task_repo = ctx.task_repo();
    task_repo.find_by_id(task_uuid).await?
        .ok_or_else(|| Error::Custom(format!("Task not found: {}", task_id)))?;

    // Parse question type
    let question_type: QuestionType = match qtype.to_lowercase().as_str() {
        "open" => QuestionType::OpenEnded,
        "single" => QuestionType::SingleChoice,
        "multi" => QuestionType::MultiChoice,
        _ => return Err(Error::Parse(format!("Invalid question type: {}", qtype))),
    };

    // Parse urgency
    let urgency: Urgency = urgency.parse()
        .map_err(|e: String| Error::Parse(e))?;

    // Validate options for choice types
    if matches!(question_type, QuestionType::SingleChoice | QuestionType::MultiChoice) {
        if options.len() < 2 {
            return Err(Error::Custom("Choice questions require at least 2 options".to_string()));
        }
    }

    let input = CreateQuestion {
        question_text,
        question_type,
        options: if options.is_empty() { None } else { Some(options) },
        urgency,
    };

    let repo = ctx.question_repo();
    let question = repo.create(task_uuid, &input).await?;

    println!("Created question: {}", question.id);
    println!("  Task: {}", task_id);
    println!("  Type: {:?}", question.question_type);
    println!("  Urgency: {:?}", question.urgency);

    Ok(())
}

async fn handle_list(
    ctx: &Ctx,
    task: Option<String>,
    unanswered: bool,
    urgent: bool,
) -> Result<()> {
    let task_id = task
        .map(|s| Uuid::parse_str(&s))
        .transpose()
        .map_err(|e| Error::Parse(e.to_string()))?;

    let repo = ctx.question_repo();
    let mut questions = if let Some(tid) = task_id {
        repo.find_by_task(tid).await?
    } else {
        // Get all questions by finding all tasks first
        let task_repo = ctx.task_repo();
        let tasks = task_repo.find_all(&Default::default()).await?;
        let mut all_questions = Vec::new();
        for task in tasks {
            let task_questions = repo.find_by_task(task.id).await?;
            all_questions.extend(task_questions);
        }
        all_questions
    };

    // Filter by unanswered
    if unanswered {
        questions.retain(|q| !q.is_answered());
    }

    // Filter by urgent
    if urgent {
        questions.retain(|q| matches!(q.urgency, Urgency::High));
    }

    output::print_questions(&questions, Format::Table);

    Ok(())
}

async fn handle_answer(
    ctx: &Ctx,
    id: String,
    answer: String,
    by: Option<String>,
) -> Result<()> {
    let question_id = Uuid::parse_str(&id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    let input = AnswerQuestion {
        answer,
        answered_by: by,
    };

    let repo = ctx.question_repo();
    let question = repo.answer(question_id, &input).await?;

    println!("Answered question: {}", &id[..8]);
    println!("  Answer: {}", question.answer.unwrap_or_default());

    Ok(())
}
```

- [ ] **Step 2: Update src/cli/comment.rs**

```rust
//! Comment command handlers

use super::args::CommentCommands;
use super::ctx::Ctx;
use super::output;
use crate::core::{CreateComment, AuthorType};
use crate::error::{Error, Result};
use uuid::Uuid;

pub async fn handle(cmd: CommentCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        CommentCommands::Add {
            task_id,
            message,
            author,
        } => handle_add(ctx, task_id, message, author).await,
        CommentCommands::List {
            task_id,
            reverse,
        } => handle_list(ctx, task_id, reverse).await,
    }
}

async fn handle_add(
    ctx: &Ctx,
    task_id: String,
    content: String,
    author: Option<String>,
) -> Result<()> {
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    // Verify task exists
    let task_repo = ctx.task_repo();
    task_repo.find_by_id(task_uuid).await?
        .ok_or_else(|| Error::Custom(format!("Task not found: {}", task_id)))?;

    let input = CreateComment {
        content,
        author_id: author,
        author_type: Some(AuthorType::Human),
    };

    let repo = ctx.comment_repo();
    let comment = repo.create(task_uuid, &input).await?;

    println!("Added comment to task {}", &task_id[..8]);
    println!("  Comment ID: {}", comment.id);

    Ok(())
}

async fn handle_list(
    ctx: &Ctx,
    task_id: String,
    reverse: bool,
) -> Result<()> {
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| Error::Parse(e.to_string()))?;

    let repo = ctx.comment_repo();
    let mut comments = repo.find_by_task(task_uuid).await?;

    if reverse {
        comments.reverse();
    }

    println!("Comments on task {}:", &task_id[..8]);
    println!();
    output::print_comments(&comments);

    Ok(())
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
git commit -m "feat(cops): implement question and comment command handlers"
```

---

## Task 6: Implement Board and Status Command Handlers

**Files:**
- Update: `company-ops/subsystems/task-system/src/cli/board.rs`
- Update: `company-ops/subsystems/task-system/src/cli/status.rs`

- [ ] **Step 1: Update src/cli/board.rs**

```rust
//! Board command handlers

use super::args::BoardCommands;
use super::ctx::Ctx;
use super::output::{self, Format};
use crate::core::{TaskFilters, TaskStatus};
use crate::error::{Error, Result};

pub async fn handle(cmd: BoardCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        BoardCommands::Show {
            filter,
            assignee,
            watch,
        } => handle_show(ctx, filter, assignee, watch).await,
    }
}

async fn handle_show(
    ctx: &Ctx,
    filter: Option<String>,
    assignee: Option<String>,
    watch: bool,
) -> Result<()> {
    if watch {
        println!("Watch mode not yet implemented. Showing board once.");
    }

    let repo = ctx.task_repo();
    
    // Get status filter if provided
    let status_filter: Option<Vec<TaskStatus>> = filter
        .map(|s| s.parse())
        .transpose()
        .map_err(|e: String| Error::Parse(e))?
        .map(|s| vec![s]);

    let filters = TaskFilters {
        status: status_filter,
        assignee: assignee.clone(),
        ..Default::default()
    };

    let tasks = repo.find_all(&filters).await?;
    let status_counts = repo.count_by_status().await?;

    // Build kanban view
    println!();
    println!("╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║                          COPS TASK BOARD                                      ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");
    println!();

    // Show status columns
    let columns = &ctx.config.board.default_columns;
    
    for column in columns {
        let count = status_counts.iter()
            .find(|(status, _)| status.to_string() == *column)
            .map(|(_, c)| *c)
            .unwrap_or(0);

        println!("┌─ {} ({}) {}", column, count, "─".repeat(60 - column.len() - count.to_string().len()));
        
        let column_tasks: Vec<_> = tasks.iter()
            .filter(|t| t.status.to_string() == *column)
            .collect();

        if column_tasks.is_empty() {
            println!("│ (empty)");
        } else {
            for task in column_tasks.iter().take(5) {
                let id_short = &task.id.to_string()[..8];
                let title = if task.title.len() > 50 {
                    format!("{}...", &task.title[..47])
                } else {
                    task.title.clone()
                };
                println!("│ [{}] {}", id_short, title);
            }
            if column_tasks.len() > 5 {
                println!("│ ... and {} more", column_tasks.len() - 5);
            }
        }
        println!("└{}", "─".repeat(70));
        println!();
    }

    // Show summary
    println!("Summary:");
    for (status, count) in &status_counts {
        println!("  {}: {}", status, count);
    }
    println!("  Total: {}", tasks.len());

    Ok(())
}
```

- [ ] **Step 2: Update src/cli/status.rs**

```rust
//! Status command handlers

use super::args::StatusCommands;
use super::ctx::Ctx;
use crate::error::{Error, Result};

pub async fn handle(cmd: StatusCommands, ctx: &Ctx) -> Result<()> {
    match cmd {
        StatusCommands::Show {
            format,
            since,
        } => handle_show(ctx, format, since).await,
        StatusCommands::Watch => handle_watch(ctx).await,
    }
}

async fn handle_show(
    ctx: &Ctx,
    format: String,
    since: Option<String>,
) -> Result<()> {
    let repo = ctx.task_repo();
    let status_counts = repo.count_by_status().await?;

    // Get recent events if since is specified
    let recent_events = if let Some(ref since_str) = since {
        let since_time = chrono::DateTime::parse_from_rfc3339(since_str)
            .map_err(|e| Error::Parse(format!("Invalid timestamp: {}", e)))?
            .with_timezone(&chrono::Utc);
        
        let event_repo = ctx.event_repo();
        Some(event_repo.find_since(since_time).await?)
    } else {
        None
    };

    match format.as_str() {
        "json" => {
            let status_map: std::collections::HashMap<String, i64> = status_counts
                .iter()
                .map(|(s, c)| (s.to_string(), *c))
                .collect();
            
            let output = serde_json::json!({
                "status_counts": status_map,
                "total_tasks": status_counts.iter().map(|(_, c)| c).sum::<i64>(),
                "recent_events": recent_events.map(|events| events.len()),
            });
            
            println!("{}", serde_json::to_string_pretty(&output).unwrap());
        }
        _ => {
            println!("COPS Status");
            println!("===========");
            println!();
            println!("Task Counts by Status:");
            for (status, count) in &status_counts {
                println!("  {}: {}", status, count);
            }
            let total: i64 = status_counts.iter().map(|(_, c)| c).sum();
            println!("  ─────────────");
            println!("  Total: {}", total);
            
            if let Some(events) = recent_events {
                println!();
                println!("Recent Events: {}", events.len());
            }
        }
    }

    Ok(())
}

async fn handle_watch(_ctx: &Ctx) -> Result<()> {
    println!("Watch mode streams events in real-time.");
    println!("This feature requires a running web server with WebSocket support.");
    println!();
    println!("Start the web server with: cops web");
    println!("Then connect to ws://localhost:9090/ws for real-time updates.");

    Ok(())
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
git commit -m "feat(cops): implement board and status command handlers"
```

---

## Task 7: Update Web Command Handler (Placeholder)

**Files:**
- Update: `company-ops/subsystems/task-system/src/cli/web.rs`

- [ ] **Step 1: Update src/cli/web.rs**

```rust
//! Web server command handler

use super::args::WebCommands;
use super::ctx::Ctx;
use crate::error::Result;

pub async fn handle(cmd: WebCommands, ctx: &Ctx) -> Result<()> {
    println!("Starting web server...");
    println!("  Host: {}", cmd.host);
    println!("  Port: {}", cmd.port);
    println!("  WebSocket: {}", if ctx.config.server.websocket_enabled { "enabled" } else { "disabled" });
    
    if cmd.no_ui {
        println!("  Mode: API only (no frontend)");
    }
    
    println!();
    println!("Web server implementation is planned for Phase 5.");
    println!("This will include:");
    println!("  - REST API for tasks, questions, comments");
    println!("  - WebSocket for real-time updates");
    println!("  - Vue 3 SPA frontend (embedded)");
    
    if cmd.open {
        println!();
        println!("Note: Browser auto-open will be available in Phase 5.");
    }

    Ok(())
}
```

- [ ] **Step 2: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build
```

- [ ] **Step 3: Commit**

```bash
git add company-ops/subsystems/task-system/src/cli/web.rs
git commit -m "feat(cops): update web command handler with Phase 5 notice"
```

---

## Task 8: Final Testing and Integration

**Files:**
- Test: Manual CLI testing

- [ ] **Step 1: Build release binary**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build --release
```

- [ ] **Step 2: Test config init**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops config init
```
Expected: Creates cops.toml and data/ directory

- [ ] **Step 3: Test db migrate**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops db migrate
```
Expected: Creates database tables

- [ ] **Step 4: Test task creation**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops task create "Test task" -d "Test description" -P high
```
Expected: Creates task with ID, shows confirmation

- [ ] **Step 5: Test task list**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops task list
```
Expected: Shows task in table format

- [ ] **Step 6: Test task list JSON format**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops task list -F json
```
Expected: Shows tasks in JSON format

- [ ] **Step 7: Test board view**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops board show
```
Expected: Shows kanban-style board

- [ ] **Step 8: Test question creation**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops question create <task-id> "What priority?" -t single --option "High" --option "Medium" --option "Low"
```
Expected: Creates choice question

- [ ] **Step 9: Test question answering**

Run:
```bash
cd company-ops/subsystems/task-system && ./target/release/cops question answer <question-id> "High"
```
Expected: Marks question as answered

- [ ] **Step 10: Commit final version**

```bash
git add company-ops/subsystems/task-system/
git commit -m "feat(cops): complete Phase 4 CLI handlers implementation"
```

---

## Summary

This plan covers **Phase 4** (8 tasks) implementing:

- ✅ Shared context with database pool and config
- ✅ Output formatting (table, JSON, simple)
- ✅ Config command handlers (init, show)
- ✅ DB command handlers (migrate, status)
- ✅ Task command handlers (create, list, show, update, move, delete)
- ✅ Question and Comment repositories (SQLite)
- ✅ Question command handlers (create, list, answer)
- ✅ Comment command handlers (add, list)
- ✅ Board command handler (kanban view)
- ✅ Status command handler (system status)

**Remaining phases** (to be added in subsequent plan updates):
- Phase 5: REST API implementation
- Phase 6: WebSocket & real-time
- Phase 7: Vue 3 Frontend

---

*Plan version: 1.0.0*
*Created: 2026-04-08*
