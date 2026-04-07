//! Comment repository implementation

use crate::core::Comment;
use crate::db::pool::DbPool;
use crate::db::repository::Repository;

/// Comment repository for database operations
pub struct CommentRepository {
    pool: DbPool,
}

impl CommentRepository {
    /// Create a new comment repository
    pub fn new(pool: DbPool) -> Self {
        Self { pool }
    }
}

impl Repository<Comment> for CommentRepository {
    async fn find_all(&self) -> crate::Result<Vec<Comment>> {
        // TODO: Implement later
        Ok(Vec::new())
    }

    async fn find_by_id(&self, _id: uuid::Uuid) -> crate::Result<Option<Comment>> {
        // TODO: Implement later
        Ok(None)
    }

    async fn create(&self, _entity: Comment) -> crate::Result<Comment> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn update(&self, _entity: Comment) -> crate::Result<Comment> {
        // TODO: Implement later
        todo!("Implement later")
    }

    async fn delete(&self, _id: uuid::Uuid) -> crate::Result<()> {
        // TODO: Implement later
        Ok(())
    }
}
