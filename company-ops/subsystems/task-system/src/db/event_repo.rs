//! SQLite implementation of EventRepository
//!
//! Provides type-safe database operations for events using sqlx.

use async_trait::async_trait;
use sqlx::SqlitePool;

use crate::core::*;
use crate::db::{DbPool, EventRepository as EventRepositoryTrait};
use crate::error::Result;

/// SQLite-based event repository implementation
pub struct SqliteEventRepository {
    pool: SqlitePool,
}

impl SqliteEventRepository {
    /// Create a new SQLite event repository
    pub fn new(pool: &DbPool) -> Self {
        Self {
            pool: pool.as_sqlite().clone(),
        }
    }
}

#[async_trait]
impl EventRepositoryTrait for SqliteEventRepository {
    async fn append(&self, _event: &Event) -> Result<()> {
        // TODO: Implement in future task
        todo!("EventRepository::append not yet implemented")
    }

    async fn find_since(&self, _since: chrono::DateTime<chrono::Utc>) -> Result<Vec<Event>> {
        // TODO: Implement in future task
        Ok(Vec::new())
    }
}
