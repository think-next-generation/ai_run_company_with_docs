//! Repository trait and common database operations

/// Base repository trait for CRUD operations
pub trait Repository<T> {
    /// Find all entities matching optional filters
    fn find_all(&self) -> impl std::future::Future<Output = crate::Result<Vec<T>>> + Send;

    /// Find entity by ID
    fn find_by_id(
        &self,
        id: uuid::Uuid,
    ) -> impl std::future::Future<Output = crate::Result<Option<T>>> + Send;

    /// Create a new entity
    fn create(&self, entity: T) -> impl std::future::Future<Output = crate::Result<T>> + Send;

    /// Update an existing entity
    fn update(&self, entity: T) -> impl std::future::Future<Output = crate::Result<T>> + Send;

    /// Delete an entity by ID
    fn delete(&self, id: uuid::Uuid) -> impl std::future::Future<Output = crate::Result<()>> + Send;
}
