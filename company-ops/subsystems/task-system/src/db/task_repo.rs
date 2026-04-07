//! Task repository implementation

use crate::core::Task;
use crate::db::pool::DbPool;
use crate::db::repository::Repository;

/// Task repository for database operations
pub struct TaskRepository {
    pool: DbPool,
}

impl TaskRepository {
    /// Create a new task repository
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }
}

impl Repository<Task> for TaskRepository {
    async fn find_all(&self) -> crate::Result<Vec<Task>> {
        // TODO: Implement in Task 8
        Ok(Vec::new())
    }

    async fn find_by_id(&self, _id: uuid::Uuid) -> crate::Result<Option<Task>> {
        // TODO: Implement in Task 8
        Ok(None)
    }

    async fn create(&self, _entity: Task) -> crate::Result<Task> {
        // TODO: Implement in Task 8
        todo!("Implement in Task 8")
    }

    async fn update(&self, _entity: Task) -> crate::Result<Task> {
        // TODO: Implement in Task 8
        todo!("Implement in Task 8")
    }

    async fn delete(&self, _id: uuid::Uuid) -> crate::Result<()> {
        // TODO: Implement in Task 8
        Ok(())
    }
}
