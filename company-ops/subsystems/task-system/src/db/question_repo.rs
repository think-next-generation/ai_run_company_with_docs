//! Question repository implementation

use crate::core::Question;
use crate::db::pool::DbPool;
use crate::db::repository::Repository;

/// Question repository for database operations
pub struct QuestionRepository {
    pool: DbPool,
}

impl QuestionRepository {
    /// Create a new question repository
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }
}

impl Repository<Question> for QuestionRepository {
    async fn find_all(&self) -> crate::Result<Vec<Question>> {
        // TODO: Implement later
        Ok(Vec::new())
    }

    async fn find_by_id(&self, _id: uuid::Uuid) -> crate::Result<Option<Question>> {
        // TODO: Implement later
        Ok(None)
    }

    async fn create(&self, _entity: Question) -> crate::Result<Question> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn update(&self, _entity: Question) -> crate::Result<Question> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn delete(&self, _id: uuid::Uuid) -> crate::Result<()> {
        // TODO: Implement later
        Ok(())
    }
}
