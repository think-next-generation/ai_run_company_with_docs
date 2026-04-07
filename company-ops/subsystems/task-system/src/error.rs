//! Error module - error types and Result alias

use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Task not found: {0}")]
    TaskNotFound(String),

    #[error("Invalid state transition: {0}")]
    InvalidStateTransition(String),
}

pub type Result<T> = std::result::Result<T, Error>;
