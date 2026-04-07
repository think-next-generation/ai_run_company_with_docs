//! SQLite implementation of CommentRepository
//!
//! Provides type-safe database operations for comments using sqlx.

use async_trait::async_trait;
use sqlx::SqlitePool;

use crate::core::*;
use crate::db::{DbPool, CommentRepository as CommentRepositoryTrait};
use crate::error::Result;

/// SQLite-based comment repository implementation
pub struct SqliteCommentRepository {
    pool: SqlitePool,
}

impl SqliteCommentRepository {
    /// Create a new SQLite comment repository
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl CommentRepositoryTrait for SqliteCommentRepository {
    async fn create(&self, _task_id: uuid::Uuid, _comment: &CreateComment) -> Result<Comment> {
        // TODO: Implement in future task
        todo!("CommentRepository::create not yet implemented")
    }

    async fn find_by_task(&self, _task_id: uuid::Uuid) -> Result<Vec<Comment>> {
        // TODO: Implement in future task
        Ok(Vec::new())
    }
}
