//! SQLite implementation of QuestionRepository
//!
//! Provides type-safe database operations for questions using sqlx.

use async_trait::async_trait;
use sqlx::SqlitePool;

use crate::core::*;
use crate::db::{DbPool, QuestionRepository as QuestionRepositoryTrait};
use crate::error::Result;

/// SQLite-based question repository implementation
pub struct SqliteQuestionRepository {
    pool: SqlitePool,
}

impl SqliteQuestionRepository {
    /// Create a new SQLite question repository
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl QuestionRepositoryTrait for SqliteQuestionRepository {
    async fn create(&self, _task_id: uuid::Uuid, _question: &CreateQuestion) -> Result<Question> {
        // TODO: Implement in future task
        todo!("QuestionRepository::create not yet implemented")
    }

    async fn find_by_id(&self, _id: uuid::Uuid) -> Result<Option<Question>> {
        // TODO: Implement in future task
        Ok(None)
    }

    async fn find_by_task(&self, _task_id: uuid::Uuid) -> Result<Vec<Question>> {
        // TODO: Implement in future task
        Ok(Vec::new())
    }

    async fn answer(&self, _id: uuid::Uuid, _answer: &AnswerQuestion) -> Result<Question> {
        // TODO: Implement in future task
        todo!("QuestionRepository::answer not yet implemented")
    }
}
