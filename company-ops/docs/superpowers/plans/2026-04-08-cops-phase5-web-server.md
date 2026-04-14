# cops Phase 5: Web Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement REST API endpoints for tasks/questions/comments, WebSocket for real-time updates, and embedded Vue 3 SPA frontend.

**Architecture:** Use Axum web framework with tower middleware for routing. API handlers share the Ctx for database access. WebSocket broadcaster maintains connected clients. Vue 3 SPA is embedded via rust-embed and served as static files.

**Tech Stack:** Rust (axum 0.7, tower 0.4, tokio), Vue 3 (embedded), rust-embed for static file serving

---

## File Structure Overview

```
company-ops/subsystems/task-system/src/
├── api/
│   ├── mod.rs              # API module exports
│   ├── routes.rs            # Route definitions
│   ├── handlers/
│   │   ├── mod.rs          # Handler exports
│   │   ├── task.rs         # Task API handlers
│   │   ├── question.rs     # Question API handlers
│   │   ├── comment.rs      # Comment API handlers
│   │   └── status.rs       # Status API handlers
│   ├── state.rs            # Shared app state (Ctx wrapper)
│   └── error.rs            # API error types
├── ws/
│   ├── mod.rs              # WebSocket module
│   └── broadcaster.rs      # WebSocket broadcaster
├── frontend/
│   └── index.html          # Embedded Vue 3 SPA (single file)
└── cli/
    └── web.rs              # Updated: start server
```

---

## Task 1: API Infrastructure and Error Handling

**Files:**
- Create: `company-ops/subsystems/task-system/src/api/mod.rs`
- Create: `company-ops/subsystems/task-system/src/api/error.rs`
- Create: `company-ops/subsystems/task-system/src/api/state.rs`

- [ ] **Step 1: Create src/api/error.rs**

```rust
//! API error types and responses

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::{Deserialize, Serialize};
use std::fmt;

/// API error response
#[derive(Debug, Serialize)]
pub struct ApiError {
    pub error: String,
    #[serde(skip_serializing_if = "Option")]
    pub details: Option<String>,
}

impl ApiError {
    pub fn new(msg: impl Into<String>) -> Self {
        Self {
            error: msg.into(),
            details: None,
        }
    }

    pub fn with_details(mut self, details: impl Into<String>) -> Self {
        self.details = Some(details.into());
        self
    }
}

impl fmt::Display for ApiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Error: {}", self.error)
    }
}

/// Convert ApiError to HTTP response
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let status = StatusCode::INTERNAL_SERVER_ERROR;
        (status, Json(self))
    }
}

/// Common API result wrapper
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    #[serde(skip_serializing_if = "Option")]
    pub data: Option<T>,
    #[serde(skip_serializing_if = "Option")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option")]
    pub meta: Option<serde_json::Value>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
            meta: None,
        }
    }

    pub fn error(msg: impl Into<String>) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(msg.into()),
            meta: None,
        }
    }

    pub fn with_meta(mut self, meta: serde_json::Value) -> Self {
        self.meta = Some(meta);
        self
    }
}

impl<T: Serialize> IntoResponse for ApiResponse<T> {
    fn into_response(self) -> Response {
        let status = if self.success {
            StatusCode::OK
        } else {
            StatusCode::BAD_REQUEST
        };
        (status, Json(self))
    }
}
```

- [ ] **Step 2: Create src/api/state.rs**

```rust
//! Shared API state

use std::sync::Arc;
use crate::config::Config;
use crate::db::DbPool;

/// Shared state for API handlers
#[derive(Clone)]
pub struct ApiState {
    pub config: Arc<Config>,
    pub pool: Arc<DbPool>,
}

impl ApiState {
    pub fn new(config: Config, pool: DbPool) -> Self {
        Self {
            config: Arc::new(config),
            pool: Arc::new(pool),
        }
    }
}
```

- [ ] **Step 3: Create src/api/mod.rs**

```rust
//! API module - REST API and WebSocket handlers

pub mod error;
pub mod handlers;
pub mod routes;
pub mod state;

pub use error::{ApiError, ApiResponse};
pub use state::ApiState;

use axum::{
    routing::{get, post, put, delete},
    Router,
};
use tower_http::cors::{AnyOrigin, CorsLayer};

/// Create the API router
pub fn create_api_router(state: ApiState) -> Router {
    Router::new()
        .route(
            "/api/v1/tasks",
            get(handlers::task::list_tasks).post(handlers::task::create_task),
        )
        .route(
            "/api/v1/tasks/:id",
            get(handlers::task::get_task)
                .put(handlers::task::update_task)
                .delete(handlers::task::delete_task),
        )
        .route(
            "/api/v1/tasks/:id/move",
            post(handlers::task::move_task),
        )
        .route(
            "/api/v1/questions",
            get(handlers::question::list_questions),
        )
        .route(
            "/api/v1/questions/:id/answer",
            post(handlers::question::answer_question),
        )
        .route(
            "/api/v1/tasks/:task_id/questions",
            get(handlers::question::list_task_questions)
                .post(handlers::question::create_question),
        )
        .route(
            "/api/v1/tasks/:task_id/comments",
            get(handlers::comment::list_comments)
                .post(handlers::comment::create_comment),
        )
        .route(
            "/api/v1/status",
            get(handlers::status::get_status),
        )
        .route(
            "/api/v1/board",
            get(handlers::status::get_board),
        )
        .with_state(state)
}

/// Create CORS layer for development
pub fn create_cors_layer() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(AnyOrigin)
        .allow_methods([axum::http::Method::GET, axum::http::Method::POST, axum::http::Method::PUT, axum::http::Method::DELETE])
        .allow_headers(tower_http::cors::AnyHeader)
}
```

- [ ] **Step 4: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -50
```

Expected: Compiles with errors about missing handlers (will be fixed in subsequent tasks)

- [ ] **Step 5: Commit**

```bash
git add company-ops/subsystems/task-system/src/api/
git commit -m "feat(cops): add API infrastructure and error types"
```

---

## Task 2: Task API Handlers

**Files:**
- Create: `company-ops/subsystems/task-system/src/api/handlers/mod.rs`
- Create: `company-ops/subsystems/task-system/src/api/handlers/task.rs`

- [ ] **Step 1: Create src/api/handlers/mod.rs**

```rust
//! API handlers module

pub mod task;
pub mod question;
pub mod comment;
pub mod status;
```

- [ ] **Step 2: Create src/api/handlers/task.rs**

```rust
//! Task API handlers

use axum::{
    extract::{Path, Query, State},
    Json,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::api::{ApiError, ApiResponse, ApiState};
use crate::core::{CreateTask, UpdateTask, TaskFilters, TaskStatus, Priority, Assignee, AssigneeType, AssigneeRole};
use crate::error::Error;

/// Task create request
#[derive(Debug, Deserialize)]
pub struct CreateTaskRequest {
    pub title: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub priority: Option<String>,
    #[serde(default)]
    pub tags: Option<Vec<String>>,
    #[serde(default)]
    pub assignees: Option<Vec<AssigneeRequest>>,
    #[serde(default)]
    pub blocked_by: Option<Vec<String>>,
    #[serde(default)]
    pub parent_id: Option<String>,
}

/// Assignee in request
#[derive(Debug, Deserialize)]
pub struct AssigneeRequest {
    pub id: String,
    #[serde(default = "agent")]
    pub r#type: String,
    #[serde(default = "primary")]
    pub role: String,
}

/// Task response
#[derive(Debug, Serialize)]
pub struct TaskResponse {
    pub id: String,
    pub title: String,
    pub description: Option<String>,
    pub status: String,
    pub priority: String,
    pub tags: Vec<String>,
    pub assignees: Vec<AssigneeResponse>,
    pub blocked_by: Vec<String>,
    pub parent_id: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

/// Assignee in response
#[derive(Debug, Serialize)]
pub struct AssigneeResponse {
    pub id: String,
    #[serde(rename = "type")]
    pub kind: String,
    pub role: String,
}

/// Task list query params
#[derive(Debug, Deserialize)]
pub struct TaskListParams {
    #[serde(default)]
    pub status: Option<String>,
    #[serde(default)]
    pub assignee: Option<String>,
    #[serde(default)]
    pub tag: Option<String>,
    #[serde(default)]
    pub parent: Option<String>,
    #[serde(default)]
    pub blocked: Option<bool>,
    #[serde(default)]
    pub limit: Option<i64>,
    #[serde(default)]
    pub offset: Option<i64>,
}

/// Task update request
#[derive(Debug, Deserialize)]
pub struct UpdateTaskRequest {
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub status: Option<String>,
    #[serde(default)]
    pub priority: Option<String>,
}

/// Move task request
#[derive(Debug, Deserialize)]
pub struct MoveTaskRequest {
    pub status: String,
}

/// Convert domain Task to response
fn task_to_response(task: &crate::core::Task) -> TaskResponse {
    TaskResponse {
        id: task.id.to_string(),
        title: task.title.clone(),
        description: task.description.clone(),
        status: task.status.to_string(),
        priority: task.priority.to_string(),
        tags: task.tags.clone(),
        assignees: task.assignees.iter().map(|a| AssigneeResponse {
            id: a.id.clone(),
            kind: a.kind.to_string(),
            role: a.role.to_string(),
        }).collect(),
        blocked_by: task.blocked_by.iter().map(|id| id.to_string()).collect(),
        parent_id: task.parent_id.map(|id| id.to_string()),
        created_at: task.created_at.to_rfc3339(),
        updated_at: task.updated_at.to_rfc3339(),
    }
}

/// List all tasks
pub async fn list_tasks(
    State(state): ApiState,
    Query(params): Query<TaskListParams>,
) -> Result<Json<ApiResponse<Vec<TaskResponse>>>, ApiError> {
    let state = state;
    
    // Build filters
    let status_filter = params.status.as_ref().and_then(|s| {
        let statuses: Vec<TaskStatus> = s.split(',')
            .filter_map(|s| s.parse().ok())
            .collect::<std::result::Result<Vec<_>, _>>();
        if statuses.is_empty() {
            None
        } else {
            Some(statuses)
        }
    });
    
    let filters = TaskFilters {
        status: status_filter,
        assignee: params.assignee.clone(),
        tag: params.tag.clone(),
        parent: params.parent.as_ref().and_then(|p| Uuid::parse_str(p).ok()),
        blocked: params.blocked,
    };
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.find_all(&filters).await {
        Ok(tasks) => {
            let responses: Vec<TaskResponse> = tasks.iter().map(task_to_response).collect();
            Ok(Json(ApiResponse::success(responses)))
        }
        Err(e) => Err(ApiError::new(format!("Database error: {}", e))),
 Json(ApiError::new("Failed to list tasks")))),
    }
}

/// Create a new task
pub async fn create_task(
    State(state): ApiState,
    Json(req): Json<CreateTaskRequest>,
) -> Result<Json<ApiResponse<TaskResponse>>, ApiError> {
    let state = state;
    
    // Parse priority
    let priority = match req.priority.as_deref() {
        Some(p) => p.parse().unwrap_or(Priority::Medium),
        None => Priority::Medium,
    };
    
    // Parse assignees
    let assignees = req.assignees.as_ref().map(|a| {
        a.iter().map(|a| Assignee {
            id: a.id.clone(),
            kind: match a.r#type.to_lowercase().as_str() {
                "human" => AssigneeType::Human,
                _ => AssigneeType::Agent,
            },
            role: match a.role.to_lowercase().as_str() {
                "reviewer" => AssigneeRole::Reviewer,
                "approver" => AssigneeRole::Approver,
                "contributor" => AssigneeRole::Contributor,
                _ => AssigneeRole::Primary,
            },
        }).collect()
    }).unwrap_or_default();
    };
    
    // Parse blocked_by
    let blocked_by = req.blocked_by.as_ref().map(|ids| {
        ids.iter()
            .filter_map(|id| Uuid::parse_str(id).ok())
            .collect()
    }).unwrap_or_default();
    };
    
    // Parse parent_id
    let parent_id = req.parent_id.as_ref().and_then(|p| Uuid::parse_str(p).ok());
    
    let input = CreateTask {
        title: req.title,
        description: req.description,
        priority,
        tags: req.tags,
        assignees: if assignees.is_empty() { None } else { Some(assignees) },
        blocked_by: if blocked_by.is_empty() { None } else { Some(blocked_by) },
        parent_id,
    };
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.create(&input).await {
        Ok(task) => Ok(Json(ApiResponse::success(task_to_response(&task)))),
        Err(e) => Err(ApiError::new(format!("Failed to create task: {}", e)), Json(ApiError::new("Failed to create task"))),
    }
}

/// Get a single task
pub async fn get_task(
    State(state): ApiState,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<TaskResponse>>, ApiError> {
    let state = state;
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.find_by_id(task_id).await {
        Ok(Some(task)) => Ok(Json(ApiResponse::success(task_to_response(&task)))),
        Ok(None) => Err(ApiError::new("Task not found")),
        Err(e) => Err(ApiError::new(format!("Database error: {}", e))),
    }
}

/// Update a task
pub async fn update_task(
    State(state): ApiState,
    Path(id): Path<String>,
    Json(req): Json<UpdateTaskRequest>,
) -> Result<Json<ApiResponse<TaskResponse>>, ApiError> {
    let state = state;
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let status = req.status.as_ref().and_then(|s| s.parse().ok());
    let priority = req.priority.as_ref().and_then(|p| p.parse().ok());
    
    let input = UpdateTask {
        title: req.title,
        description: req.description,
        status,
        priority,
        tags: None,
    };
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.update(task_id, &input).await {
        Ok(task) => Ok(Json(ApiResponse::success(task_to_response(&task)))),
        Err(e) => Err(ApiError::new(format!("Failed to update task: {}", e))),
    }
}

/// Move task to new status
pub async fn move_task(
    State(state): ApiState,
    Path(id): Path<String>,
    Json(req): Json<MoveTaskRequest>,
) -> Result<Json<ApiResponse<TaskResponse>>, ApiError> {
    let state = state;
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let new_status: TaskStatus = req.status.parse()
        .map_err(|e: String| ApiError::new(e))?;
    
    let input = UpdateTask {
        status: Some(new_status),
        ..Default::default()
    };
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.update(task_id, &input).await {
        Ok(task) => Ok(Json(ApiResponse::success(task_to_response(&task)))),
        Err(e) => Err(ApiError::new(format!("Failed to move task: {}", e))),
    }
}

/// Delete a task
pub async fn delete_task(
    State(state): ApiState,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<()>>, ApiError> {
    let state = state;
    let task_id = Uuid::parse_str(&id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    match repo.delete(task_id).await {
        Ok(()) => Ok(Json(ApiResponse::success(()))),
        Err(e) => Err(ApiError::new(format!("Failed to delete task: {}", e))),
    }
}
```

- [ ] **Step 3: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -50
```

Expected: Compiles with errors about missing handlers (will be fixed in subsequent tasks)

- [ ] **Step 4: Commit**

```bash
git add company-ops/subsystems/task-system/src/api/handlers/
git commit -m "feat(cops): add task API handlers"
```

---

## Task 3: Question and Comment API Handlers

**Files:**
- Create: `company-ops/subsystems/task-system/src/api/handlers/question.rs`
- Create: `company-ops/subsystems/task-system/src/api/handlers/comment.rs`

- [ ] **Step 1: Create src/api/handlers/question.rs**

```rust
//! Question API handlers

use axum::{
    extract::{Path, Query, State},
    Json,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::api::{ApiError, ApiResponse, ApiState};
use crate::core::{CreateQuestion, AnswerQuestion, QuestionType, Urgency};

/// Question response
#[derive(Debug, Serialize)]
pub struct QuestionResponse {
    pub id: String,
    pub task_id: String,
    pub question_type: String,
    pub question_text: String,
    pub options: Option<Vec<String>>,
    pub answer: Option<String>,
    pub answered_at: Option<String>,
    pub answered_by: Option<String>,
    pub urgency: String,
    pub created_at: String,
}

/// Create question request
#[derive(Debug, Deserialize)]
pub struct CreateQuestionRequest {
    pub question_text: String,
    #[serde(default)]
    pub question_type: Option<String>,
    #[serde(default)]
    pub options: Option<Vec<String>>,
    #[serde(default)]
    pub urgency: Option<String>,
}

/// Answer question request
#[derive(Debug, Deserialize)]
pub struct AnswerQuestionRequest {
    pub answer: String,
    #[serde(default)]
    pub answered_by: Option<String>,
}

/// Question list params
#[derive(Debug, Deserialize)]
pub struct QuestionListParams {
    #[serde(default)]
    pub unanswered: Option<bool>,
    #[serde(default)]
    pub urgent: Option<bool>,
}

/// Convert domain Question to response
fn question_to_response(q: &crate::core::Question) -> QuestionResponse {
    QuestionResponse {
        id: q.id.to_string(),
        task_id: q.task_id.to_string(),
        question_type: format!("{:?}", q.question_type),
        question_text: q.question_text.clone(),
        options: q.options.clone(),
        answer: q.answer.clone(),
        answered_at: q.answered_at.map(|dt| dt.to_rfc3339()),
        answered_by: q.answered_by.clone(),
        urgency: format!("{:?}", q.urgency),
        created_at: q.created_at.to_rfc3339(),
    }
}

/// List questions (optionally filter by task)
pub async fn list_questions(
    State(state): ApiState,
    Query(params): Query<QuestionListParams>,
) -> Result<Json<ApiResponse<Vec<QuestionResponse>>>, ApiError> {
    let state = state;
    let repo = crate::db::SqliteQuestionRepository::new(&state.pool);
    let task_repo = crate::db::SqliteTaskRepository::new(&state.pool);
    
    // Get all tasks to collect questions
    let tasks = task_repo.find_all(&Default::default()).await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
    
    let mut all_questions = Vec::new();
    for task in tasks {
        let task_questions = repo.find_by_task(task.id).await
            .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
        all_questions.extend(task_questions);
    }
    
    // Apply filters
    if params.unanswered.unwrap_or(false) {
        all_questions.retain(|q| !q.is_answered());
    }
    if params.urgent.unwrap_or(false) {
        all_questions.retain(|q| matches!(q.urgency, Urgency::High));
    }
    
    let responses: Vec<QuestionResponse> = all_questions.iter().map(question_to_response).collect();
    Ok(Json(ApiResponse::success(responses)))
}

/// List questions for a specific task
pub async fn list_task_questions(
    State(state): ApiState,
    Path(task_id): Path<String>,
    Query(params): Query<QuestionListParams>,
) -> Result<Json<ApiResponse<Vec<QuestionResponse>>>, ApiError> {
    let state = state;
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let repo = crate::db::SqliteQuestionRepository::new(&state.pool);
    let questions = repo.find_by_task(task_uuid).await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
    
    let mut questions = questions;
    
    // Apply filters
    if params.unanswered.unwrap_or(false) {
        questions.retain(|q| !q.is_answered());
    }
    if params.urgent.unwrap_or(false) {
        questions.retain(|q| matches!(q.urgency, Urgency::High));
    }
    
    let responses: Vec<QuestionResponse> = questions.iter().map(question_to_response).collect();
    Ok(Json(ApiResponse::success(responses)))
}

/// Create a question
pub async fn create_question(
    State(state): ApiState,
    Path(task_id): Path<String>,
    Json(req): Json<CreateQuestionRequest>,
) -> Result<Json<ApiResponse<QuestionResponse>>, ApiError> {
    let state = state;
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    // Verify task exists
    let task_repo = crate::db::SqliteTaskRepository::new(&state.pool);
    task_repo.find_by_id(task_uuid).await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?
        .ok_or_else(|| Err(ApiError::new("Task not found")))?;
    
    // Parse question type
    let question_type = match req.question_type.as_deref() {
        Some(t) => match t.to_lowercase().as_str() {
            "open" => QuestionType::OpenEnded,
            "single" => QuestionType::SingleChoice,
            "multi" => QuestionType::MultiChoice,
            _ => return Err(ApiError::new(format!("Invalid question type: {}", t))),
        },
        None => QuestionType::OpenEnded,
    };
    
    // Parse urgency
    let urgency = match req.urgency.as_deref() {
        Some(u) => u.parse().unwrap_or(Urgency::Normal),
        None => Urgency::Normal,
    };
    
    // Validate options for choice types
    if matches!(question_type, QuestionType::SingleChoice | QuestionType::MultiChoice) {
        if req.options.as_ref().map(|o| o.len()).unwrap_or(0) < 2 {
            return Err(ApiError::new("Choice questions require at least 2 options"));
        }
    }
    
    let input = CreateQuestion {
        question_text: req.question_text,
        question_type,
        options: req.options,
        urgency,
    };
    
    let repo = crate::db::SqliteQuestionRepository::new(&state.pool);
    match repo.create(task_uuid, &input).await {
        Ok(question) => Ok(Json(ApiResponse::success(question_to_response(&question)))),
        Err(e) => Err(ApiError::new(format!("Failed to create question: {}", e))),
    }
}

/// Answer a question
pub async fn answer_question(
    State(state): ApiState,
    Path(id): Path<String>,
    Json(req): Json<AnswerQuestionRequest>,
) -> Result<Json<ApiResponse<QuestionResponse>>, ApiError> {
    let state = state;
    let question_id = Uuid::parse_str(&id)
        .map_err(|e| ApiError::new(format!("Invalid question ID: {}", e)))?;
    
    let input = AnswerQuestion {
        answer: req.answer,
        answered_by: req.answered_by,
    };
    
    let repo = crate::db::SqliteQuestionRepository::new(&state.pool);
    match repo.answer(question_id, &input).await {
        Ok(question) => Ok(Json(ApiResponse::success(question_to_response(&question)))),
        Err(e) => Err(ApiError::new(format!("Failed to answer question: {}", e))),
    }
}
```

- [ ] **Step 2: Create src/api/handlers/comment.rs**

```rust
//! Comment API handlers

use axum::{
    extract::{Path, State},
    Json,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::api::{ApiError, ApiResponse, ApiState};
use crate::core::{CreateComment, AuthorType};

/// Comment response
#[derive(Debug, Serialize)]
pub struct CommentResponse {
    pub id: String,
    pub task_id: String,
    pub author_id: String,
    pub author_type: String,
    pub content: String,
    pub created_at: String,
}

/// Create comment request
#[derive(Debug, Deserialize)]
pub struct CreateCommentRequest {
    pub content: String,
    #[serde(default)]
    pub author_id: Option<String>,
    #[serde(default)]
    pub author_type: Option<String>,
}

/// Convert domain Comment to response
fn comment_to_response(c: &crate::core::Comment) -> CommentResponse {
    CommentResponse {
        id: c.id.to_string(),
        task_id: c.task_id.to_string(),
        author_id: c.author_id.clone(),
        author_type: format!("{:?}", c.author_type),
        content: c.content.clone(),
        created_at: c.created_at.to_rfc3339(),
    }
}

/// List comments for a task
pub async fn list_comments(
    State(state): ApiState,
    Path(task_id): Path<String>,
) -> Result<Json<ApiResponse<Vec<CommentResponse>>>, ApiError> {
    let state = state;
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    let repo = crate::db::SqliteCommentRepository::new(&state.pool);
    match repo.find_by_task(task_uuid).await {
        Ok(comments) => {
            let responses: Vec<CommentResponse> = comments.iter().map(comment_to_response).collect();
            Ok(Json(ApiResponse::success(responses)))
        }
        Err(e) => Err(ApiError::new(format!("Database error: {}", e))),
    }
}

/// Create a comment
pub async fn create_comment(
    State(state): ApiState,
    Path(task_id): Path<String>,
    Json(req): Json<CreateCommentRequest>,
) -> Result<Json<ApiResponse<CommentResponse>>, ApiError> {
    let state = state;
    let task_uuid = Uuid::parse_str(&task_id)
        .map_err(|e| ApiError::new(format!("Invalid task ID: {}", e)))?;
    
    // Verify task exists
    let task_repo = crate::db::SqliteTaskRepository::new(&state.pool);
    task_repo.find_by_id(task_uuid).await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?
        .ok_or_else(|| ApiError::new("Task not found"))?;
    
    let author_type = match req.author_type.as_deref() {
        Some(t) => match t.to_lowercase().as_str() {
            "human" => AuthorType::Human,
            _ => AuthorType::Agent,
        },
        None => AuthorType::Human,
    };
    
    let input = CreateComment {
        content: req.content,
        author_id: req.author_id,
        author_type: Some(author_type),
    };
    
    let repo = crate::db::SqliteCommentRepository::new(&state.pool);
    match repo.create(task_uuid, &input).await {
        Ok(comment) => Ok(Json(ApiResponse::success(comment_to_response(&comment)))),
        Err(e) => Err(ApiError::new(format!("Failed to create comment: {}", e))),
    }
}
```

- [ ] **Step 3: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -50
```

Expected: Compiles with errors about missing status handler

- [ ] **Step 4: Commit**

```bash
git add company-ops/subsystems/task-system/src/api/handlers/
git commit -m "feat(cops): add question and comment API handlers"
```

---

## Task 4: Status API Handler

**Files:**
- Create: `company-ops/subsystems/task-system/src/api/handlers/status.rs`

- [ ] **Step 1: Create src/api/handlers/status.rs**

```rust
//! Status API handlers

use axum::{
    extract::State,
    Json,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::api::{ApiError, ApiResponse, ApiState};

/// Status response
#[derive(Debug, Serialize)]
pub struct StatusResponse {
    pub status_counts: HashMap<String, i64>,
    pub total_tasks: i64,
    pub database: String,
}

/// Board column response
#[derive(Debug, Serialize)]
pub struct BoardColumnResponse {
    pub status: String,
    pub count: i64,
    pub tasks: Vec<BoardTaskResponse>,
}

/// Board task response
#[derive(Debug, Serialize)]
pub struct BoardTaskResponse {
    pub id: String,
    pub title: String,
    pub priority: String,
}

/// Board response
#[derive(Debug, Serialize)]
pub struct BoardResponse {
    pub columns: Vec<BoardColumnResponse>,
    pub total: i64,
}

/// Get system status
pub async fn get_status(
    State(state): State<ApiState>,
) -> Result<Json<ApiResponse<StatusResponse>>, ApiError> {
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    
    let status_counts = repo.count_by_status().await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
    
    let counts_map: HashMap<String, i64> = status_counts
        .iter()
        .map(|(s, c)| (s.to_string(), *c))
        .collect();
    
    let total: i64 = status_counts.iter().map(|(_, c)| c).sum();
    
    let response = StatusResponse {
        status_counts: counts_map,
        total_tasks: total,
        database: state.config.database.backend.clone(),
    };
    
    Ok(Json(ApiResponse::success(response)))
}

/// Get board view
pub async fn get_board(
    State(state): State<ApiState>,
) -> Result<Json<ApiResponse<BoardResponse>>, ApiError> {
    let repo = crate::db::SqliteTaskRepository::new(&state.pool);
    
    let status_counts = repo.count_by_status().await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
    
    let all_tasks = repo.find_all(&Default::default()).await
        .map_err(|e| ApiError::new(format!("Database error: {}", e)))?;
    
    let mut columns = Vec::new();
    let mut total = 0;
    
    for column_status in &state.config.board.default_columns {
        let count = status_counts.iter()
            .find(|(s, _)| s.to_string() == *column_status)
            .map(|(_, c)| *c)
            .unwrap_or(0);
        
        let tasks: Vec<BoardTaskResponse> = all_tasks.iter()
            .filter(|t| t.status.to_string() == *column_status)
            .take(10)
            .map(|t| BoardTaskResponse {
                id: t.id.to_string(),
                title: t.title.clone(),
                priority: t.priority.to_string(),
            })
            .collect();
        
        columns.push(BoardColumnResponse {
            status: column_status.clone(),
            count,
            tasks,
        });
        
        total += count;
    }
    
    Ok(Json(ApiResponse::success(BoardResponse { columns, total })))
}
```

- [ ] **Step 2: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -50
```

Expected: Compiles successfully

- [ ] **Step 3: Commit**

```bash
git add company-ops/subsystems/task-system/src/api/handlers/status.rs
git commit -m "feat(cops): add status API handlers"
```

---

## Task 5: WebSocket Broadcaster

**Files:**
- Create: `company-ops/subsystems/task-system/src/ws/mod.rs`
- Create: `company-ops/subsystems/task-system/src/ws/broadcaster.rs`

- [ ] **Step 1: Create src/ws/mod.rs**

```rust
//! WebSocket module - real-time updates

pub mod broadcaster;

pub use broadcaster::Broadcaster;
```

- [ ] **Step 2: Create src/ws/broadcaster.rs**

```rust
//! WebSocket broadcaster for real-time updates

use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::Response,
};
use futures::{SinkExt, StreamExt};
use serde::Serialize;
use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};
use uuid::Uuid;

/// Event types that can be broadcast
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WsEvent {
    TaskCreated { id: String, title: String },
    TaskUpdated { id: String, status: String },
    TaskDeleted { id: String },
    QuestionCreated { id: String, task_id: String },
    QuestionAnswered { id: String },
    CommentCreated { id: String, task_id: String },
}

/// WebSocket broadcaster
#[derive(Clone)]
pub struct Broadcaster {
    sender: broadcast::Sender<WsEvent>,
    clients: Arc<RwLock<Vec<Uuid>>>,
}

impl Default for Broadcaster {
    fn default() -> Self {
        Self::new()
    }
}

impl Broadcaster {
    /// Create a new broadcaster
    pub fn new() -> Self {
        let (sender, _) = broadcast::channel(100);
        Self {
            sender,
            clients: Arc::new(RwLock::new(Vec::new())),
        }
    }

    /// Broadcast an event to all connected clients
    pub fn broadcast(&self, event: WsEvent) {
        // Ignore send errors (no clients connected)
        let _ = self.sender.send(event);
    }

    /// Get number of connected clients
    pub async fn client_count(&self) -> usize {
        self.clients.read().await.len()
    }

    /// Handle WebSocket upgrade
    pub async fn handle_ws(
        &self,
        ws: WebSocketUpgrade,
    ) -> Response {
        let client_id = Uuid::new_v4();
        let broadcaster = self.clone();
        
        ws.on_upgrade(move |socket| broadcaster.handle_socket(socket, client_id))
    }

    async fn handle_socket(&self, socket: WebSocket, client_id: Uuid) {
        // Register client
        {
            let mut clients = self.clients.write().await;
            clients.push(client_id);
        }
        
        // Split socket into sender and receiver
        let (mut sender, mut receiver) = socket.split();
        
        // Subscribe to events
        let mut rx = self.sender.subscribe();
        
        // Task 1: Forward events to client
        let send_task = tokio::spawn(async move {
            while let Ok(event) = rx.recv().await {
                let json = serde_json::to_string(&event).unwrap_or_default();
                if sender.send(Message::Text(json)).await.is_err() {
                    break;
                }
            }
        });
        
        // Task 2: Handle incoming messages (keep-alive / close)
        let recv_task = tokio::spawn(async move {
            while let Some(msg) = receiver.next().await {
                if msg.is_close() {
                    break;
                }
                // Ignore other messages for now
            }
        });
        
        // Wait for either task to complete
        tokio::select! {
            _ = send_task => {},
            _ = recv_task => {},
        }
        
        // Unregister client
        {
            let mut clients = self.clients.write().await;
            clients.retain(|id| id != &client_id);
        }
    }
}
```

- [ ] **Step 3: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -50
```

Expected: Compiles successfully

- [ ] **Step 4: Commit**

```bash
git add company-ops/subsystems/task-system/src/ws/
git commit -m "feat(cops): add WebSocket broadcaster"
```

---

## Task 6: Embedded Vue 3 Frontend

**Files:**
- Create: `company-ops/subsystems/task-system/src/frontend/index.html`

- [ ] **Step 1: Create src/frontend/index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COPS - Task Board</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .app { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; margin-bottom: 20px; color: #fff; }
        
        .board { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 20px; }
        .column { 
            flex: 0 0 250px; 
            background: #252536; 
            border-radius: 8px; 
            padding: 12px;
            min-height: 400px;
        }
        .column-header { 
            font-weight: 600; 
            padding: 8px 12px; 
            margin-bottom: 12px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }
        .column-header.new { background: #3b82f6; }
        .column-header.assigned { background: #8b5cf6; }
        .column-header.in_progress { background: #f59e0b; }
        .column-header.blocked { background: #ef4444; }
        .column-header.review { background: #a855f7; }
        .column-header.done { background: #22c55e; }
        
        .task-card {
            background: #1a1a2e;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.1s;
            border: 1px solid #3a3a4e;
        }
        .task-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        .task-title { font-weight: 500; margin-bottom: 4px; }
        .task-meta { font-size: 12px; color: #888; display: flex; gap: 8px; }
        .priority-high { border-left: 3px solid #ef4444; }
        .priority-urgent { border-left: 3px solid #f97316; }
        .priority-medium { border-left: 3px solid #fbbf24; }
        .priority-low { border-left: 3px solid #6b7280; }
        
        .modal-overlay {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            display: flex; align-items: center; justify-content: center;
        }
        .modal {
            background: #252536;
            border-radius: 12px;
            padding: 24px;
            width: 500px;
            max-width: 90%;
        }
        .modal h2 { margin-bottom: 16px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 4px; font-size: 14px; color: #888; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #3a3a4e;
            border-radius: 6px;
            background: #1a1a2e;
            color: #e0e0e0;
        }
        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-weight: 500;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-secondary { background: #3a3a4e; color: #e0e0e0; }
        .btn-group { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
        
        .status-bar {
            background: #252536;
            border-radius: 8px;
            padding: 12px 20px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-item { text-align: center; }
        .status-value { font-size: 24px; font-weight: 700; }
        .status-label { font-size: 12px; color: #888; }
        
        .new-task-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #3b82f6;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
    </style>
</head>
<body>
    <div id="app" class="app">
        <h1>📋 COPS Task Board</h1>
        
        <div class="status-bar">
            <div class="status-item" v-for="(count, status) in statusCounts" :key="status">
                <div class="status-value">{{ count }}</div>
                <div class="status-label">{{ status }}</div>
            </div>
        </div>
        
        <div class="board">
            <div class="column" v-for="column in board.columns" :key="column.status">
                <div class="column-header" :class="column.status.toLowerCase()">
                    <span>{{ column.status }}</span>
                    <span>{{ column.count }}</span>
                </div>
                <div class="task-card" 
                     v-for="task in column.tasks" 
                     :key="task.id"
                     :class="'priority-' + task.priority"
                     @click="showTask(task)">
                    <div class="task-title">{{ task.title }}</div>
                    <div class="task-meta">
                        <span>{{ task.priority }}</span>
                        <span>{{ task.id.substring(0, 8) }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <button class="new-task-btn" @click="showNewTaskModal = true">+</button>
        
        <div class="modal-overlay" v-if="showNewTaskModal" @click.self="showNewTaskModal = false">
            <div class="modal" @click.stop>
                <h2>New Task</h2>
                <div class="form-group">
                    <label>Title</label>
                    <input v-model="newTask.title" placeholder="Enter task title">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea v-model="newTask.description" rows="3" placeholder="Optional description"></textarea>
                </div>
                <div class="form-group">
                    <label>Priority</label>
                    <select v-model="newTask.priority">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                </div>
                <div class="btn-group">
                    <button class="btn btn-secondary" @click="showNewTaskModal = false">Cancel</button>
                    <button class="btn btn-primary" @click="createTask">Create</button>
                </div>
            </div>
        </div>
        
        <div class="modal-overlay" v-if="selectedTask" @click.self="selectedTask = null">
            <div class="modal" @click.stop>
                <h2>{{ selectedTask.title }}</h2>
                <p v-if="selectedTask.description">{{ selectedTask.description }}</p>
                <div class="form-group">
                    <label>Status</label>
                    <select v-model="selectedTask.status" @change="moveTask(selectedTask)">
                        <option v-for="s in validStatuses" :value="s">{{ s }}</option>
                    </select>
                </div>
                <div class="btn-group">
                    <button class="btn btn-secondary" @click="selectedTask = null">Close</button>
                    <button class="btn btn-primary" style="background: #ef4444" @click="deleteTask(selectedTask)">Delete</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const { createApp, ref, onMounted, computed } = Vue;
        
        createApp({
            setup() {
                const board = ref({ columns: [], total: 0 });
                const statusCounts = ref([]);
                const showNewTaskModal = ref(false);
                const selectedTask = ref(null);
                const newTask = ref({ title: '', description: '', priority: 'medium' });
                const validStatuses = ['NEW', 'ASSIGNED', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'DONE'];
                
                async function fetchBoard() {
                    try {
                        const res = await fetch('/api/v1/board');
                        const data = await res.json();
                        if (data.success) {
                            board.value = data.data;
                            updateStatusCounts();
                        }
                    } catch (e) {
                        console.error('Failed to fetch board:', e);
                    }
                }
                
                function updateStatusCounts() {
                    statusCounts.value = board.value.columns.map(c => [c.count, c.status]);
                }
                
                async function createTask() {
                    if (!newTask.value.title.trim()) return;
                    try {
                        const res = await fetch('/api/v1/tasks', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(newTask.value)
                        });
                        const data = await res.json();
                        if (data.success) {
                            showNewTaskModal.value = false;
                            newTask.value = { title: '', description: '', priority: 'medium' };
                            fetchBoard();
                        }
                    } catch (e) {
                        console.error('Failed to create task:', e);
                    }
                }
                
                function showTask(task) {
                    selectedTask.value = { ...task };
                }
                
                async function moveTask(task) {
                    try {
                        await fetch(`/api/v1/tasks/${task.id}/move`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ status: task.status })
                        });
                        fetchBoard();
                    } catch (e) {
                        console.error('Failed to move task:', e);
                    }
                }
                
                async function deleteTask(task) {
                    if (!confirm('Delete this task?')) return;
                    try {
                        await fetch(`/api/v1/tasks/${task.id}`, { method: 'DELETE' });
                        selectedTask.value = null;
                        fetchBoard();
                    } catch (e) {
                        console.error('Failed to delete task:', e);
                    }
                }
                
                onMounted(() => {
                    fetchBoard();
                    // Refresh every 30 seconds
                    setInterval(fetchBoard, 30000);
                });
                
                return {
                    board, statusCounts, showNewTaskModal, selectedTask, newTask, validStatuses,
                    fetchBoard, createTask, showTask, moveTask, deleteTask
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
```

- [ ] **Step 2: Verify file created**

Run:
```bash
ls -la company-ops/subsystems/task-system/src/frontend/
```

Expected: Shows index.html file

- [ ] **Step 3: Commit**

```bash
git add company-ops/subsystems/task-system/src/frontend/
git commit -m "feat(cops): add embedded Vue 3 SPA frontend"
```

---

## Task 7: Update Web Command Handler

**Files:**
- Modify: `company-ops/subsystems/task-system/src/cli/web.rs`
- Create: `company-ops/subsystems/task-system/src/api/routes.rs`

- [ ] **Step 1: Create src/api/routes.rs with full router setup**

```rust
//! API routes configuration

use axum::{
    routing::{get, post, put, delete},
    Router,
};
use tower_http::{cors::CorsLayer, services::ServeDir};
use rust_embed::RustEmbed;

use super::handlers;
use super::state::ApiState;
use crate::ws::Broadcaster;

#[derive(RustEmbed)]
#[folder = "src/frontend"]
struct FrontendAssets;

/// Serve frontend index.html
async fn serve_index() -> impl axum::response::IntoResponse {
    match FrontendAssets::get("index.html") {
        Some(content) => {
            let mime = mime_guess::from_path("index.html").first_or_octet_stream();
            axum::response::Html::from(content.data.into_owned())
        }
        None => axum::response::Html::from("<h1>Frontend not found</h1>"),
    }
}

/// Create the full application router
pub fn create_app_router(state: ApiState, broadcaster: Broadcaster) -> Router {
    let api_router = Router::new()
        // Tasks
        .route("/api/v1/tasks", 
            get(handlers::task::list_tasks).post(handlers::task::create_task))
        )
        .route("/api/v1/tasks/:id",
            get(handlers::task::get_task)
                .put(handlers::task::update_task)
                .delete(handlers::task::delete_task)
        )
        .route("/api/v1/tasks/:id/move", post(handlers::task::move_task))
        // Questions
        .route("/api/v1/questions", get(handlers::question::list_questions))
        .route("/api/v1/questions/:id/answer", post(handlers::question::answer_question))
        .route("/api/v1/tasks/:task_id/questions",
            get(handlers::question::list_task_questions)
                .post(handlers::question::create_question)
        )
        // Comments
        .route("/api/v1/tasks/:task_id/comments",
            get(handlers::comment::list_comments)
                .post(handlers::comment::create_comment)
        )
        // Status
        .route("/api/v1/status", get(handlers::status::get_status))
        .route("/api/v1/board", get(handlers::status::get_board))
        // WebSocket
        .route("/ws", get(|ws: axum::extract::WebSocketUpgrade| async move {
            broadcaster.handle_ws(ws).await
        }))
        .with_state(state);

    // Serve frontend for all non-API routes
    Router::new()
        .merge(api_router)
        .fallback(serve_index)
        .layer(CorsLayer::permissive())
}
```

- [ ] **Step 2: Update src/api/mod.rs to export routes**

```rust
//! API module - REST API and WebSocket handlers

pub mod error;
pub mod handlers;
pub mod routes;
pub mod state;

pub use error::{ApiError, ApiResponse};
pub use routes::create_app_router;
pub use state::ApiState;
```

- [ ] **Step 3: Update src/cli/web.rs**

```rust
//! Web server command handler

use super::args::WebCommands;
use super::ctx::Ctx;
use crate::api::{create_app_router, ApiState};
use crate::error::Result;
use crate::ws::Broadcaster;
use std::net::SocketAddr;

pub async fn handle(cmd: WebCommands, ctx: &Ctx) -> Result<()> {
    let host = cmd.host.parse()
        .map_err(|e| crate::error::Error::Config(format!("Invalid host: {}", e)))?;
    let addr = SocketAddr::new(host, cmd.port);
    
    let state = ApiState::new(ctx.config.clone(), ctx.pool.clone());
    let broadcaster = Broadcaster::new();
    
    let app = create_app_router(state, broadcaster);
    
    println!("Starting web server...");
    println!("  Address: http://{}", addr);
    println!("  WebSocket: {}", if ctx.config.server.websocket_enabled { "enabled" } else { "disabled" });
    
    if cmd.open {
        println!();
        println!("Open http://{} in your browser", addr);
    }
    
    let listener = tokio::net::TcpListener::bind(addr).await
        .map_err(|e| crate::error::Error::Io(e))?;
    
    axum::serve(listener, app).await
        .map_err(|e| crate::error::Error::Custom(format!("Server error: {}", e)))?;
    
    Ok(())
}
```

- [ ] **Step 4: Update src/lib.rs to include new modules**

```rust
pub mod cli;
pub mod config;
pub mod core;
pub mod db;
pub mod api;
pub mod ws;
pub mod error;

pub use error::Result;
```

- [ ] **Step 5: Verify compilation**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build 2>&1 | head -80
```

Expected: Compiles with minor warnings

- [ ] **Step 6: Commit**

```bash
git add company-ops/subsystems/task-system/
git commit -m "feat(cops): integrate web server with API routes and frontend"
```

---

## Task 8: Final Testing and Integration

**Files:**
- Test: Manual API testing

- [ ] **Step 1: Build release binary**

Run:
```bash
cd company-ops/subsystems/task-system && cargo build --release
```

- [ ] **Step 2: Start web server**

Run:
```bash
cd company-ops/subsystems/task-system && cargo run --release -- web --port 9090
```

Expected: Server starts on http://127.0.0.1:9090

- [ ] **Step 3: Test API endpoints (in another terminal)**

Run:
```bash
# Create task
curl -X POST http://127.0.0.1:9090/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test from API", "priority": "high"}'

# List tasks
curl http://127.0.0.1:9090/api/v1/tasks

# Get board
curl http://127.0.0.1:9090/api/v1/board

# Get status
curl http://127.0.0.1:9090/api/v1/status
```

- [ ] **Step 4: Open browser to test frontend**

Navigate to: http://127.0.0.1:9090

Expected: Vue 3 board UI loads

- [ ] **Step 5: Commit final version**

```bash
git add company-ops/subsystems/task-system/
git commit -m "feat(cops): complete Phase 5 web server implementation"
```

---

## Summary

This plan covers **Phase 5** (8 tasks) implementing:

- ✅ API infrastructure with error types
- ✅ Task API handlers (CRUD + move)
- ✅ Question API handlers (create, list, answer)
- ✅ Comment API handlers (create, list)
- ✅ Status/Board API handlers
- ✅ WebSocket broadcaster for real-time updates
- ✅ Embedded Vue 3 SPA frontend
- ✅ Full web server integration

**API Endpoints:**
- `GET/POST /api/v1/tasks` - List/Create tasks
- `GET/PUT/DELETE /api/v1/tasks/:id` - Get/Update/Delete task
- `POST /api/v1/tasks/:id/move` - Move task status
- `GET/POST /api/v1/tasks/:task_id/questions` - List/Create questions
- `GET/POST /api/v1/tasks/:task_id/comments` - List/Create comments
- `GET /api/v1/questions` - List all questions
- `POST /api/v1/questions/:id/answer` - Answer question
- `GET /api/v1/status` - System status
- `GET /api/v1/board` - Kanban board data
- `GET /ws` - WebSocket connection

---

*Plan version: 1.0.0*
*Created: 2026-04-08*
