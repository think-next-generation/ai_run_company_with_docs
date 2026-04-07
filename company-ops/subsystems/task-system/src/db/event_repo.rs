//! Event repository implementation

use crate::core::Event;
use crate::db::pool::DbPool;
use crate::db::repository::Repository;

/// Event repository for database operations
pub struct EventRepository {
    pool: DbPool,
}

impl EventRepository {
    /// Create a new event repository
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }
}

impl Repository<Event> for EventRepository {
    async fn find_all(&self) -> crate::Result<Vec<Event>> {
        // TODO: Implement later
        Ok(Vec::new())
    }

    async fn find_by_id(&self, _id: uuid::Uuid) -> crate::Result<Option<Event>> {
        // TODO: Implement later
        Ok(None)
    }

    async fn create(&self, _entity: Event) -> crate::Result<Event> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn update(&self, _entity: Event) -> crate::Result<Event> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn delete(&self, _id: uuid::Uuid) -> crate::Result<()> {
        // TODO: Implement later
        Ok(())
    }
}
