//! Events module - audit log tracking all entity changes

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::{Question, Task, TaskStatus};

/// Type of entity that an event relates to
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EntityType {
    Task,
    Question,
    Comment,
}

/// Type of event that occurred
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

/// Core Event entity for audit logging
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
    /// Create an event for task creation
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

    /// Create an event for task status change
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

    /// Create an event for question creation
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

    /// Create an event for question answer
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
