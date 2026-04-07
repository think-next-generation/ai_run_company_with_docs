//! Question module - structured Q&A system with OPEN_ENDED, SINGLE_CHOICE, MULTI_CHOICE types

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Type of question - determines how the question should be answered
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum QuestionType {
    OpenEnded,
    SingleChoice,
    MultiChoice,
}

impl Default for QuestionType {
    fn default() -> Self {
        Self::OpenEnded
    }
}

/// Urgency level for questions
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "TEXT")]
#[serde(rename_all = "lowercase")]
pub enum Urgency {
    Low,
    Normal,
    High,
}

impl Default for Urgency {
    fn default() -> Self {
        Self::Normal
    }
}

/// Core Question entity for structured Q&A
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
    /// Create a new question with the given task ID, text, and type
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

    /// Check if this question has been answered
    pub fn is_answered(&self) -> bool {
        self.answer.is_some()
    }
}

/// Data required to create a new question
#[derive(Debug, Clone, Deserialize)]
pub struct CreateQuestion {
    pub question_text: String,
    #[serde(default)]
    pub question_type: QuestionType,
    pub options: Option<Vec<String>>,
    #[serde(default)]
    pub urgency: Urgency,
}

/// Data for answering a question
#[derive(Debug, Clone, Deserialize)]
pub struct AnswerQuestion {
    pub answer: String,
    pub answered_by: Option<String>,
}
