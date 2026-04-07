//! Comment command handlers

use super::args::CommentCommands;
use crate::error::Result;

pub async fn handle(cmd: CommentCommands) -> Result<()> {
    match cmd {
        CommentCommands::Add {
            task_id,
            message,
            author,
        } => {
            println!("Not implemented yet: comment add");
            println!("  task_id: {}", task_id);
            println!("  message: {}", message);
            if let Some(a) = author {
                println!("  author: {}", a);
            }
        }
        CommentCommands::List { task_id, reverse } => {
            println!("Not implemented yet: comment list");
            println!("  task_id: {}", task_id);
            if reverse {
                println!("  reverse (newest first): true");
            }
        }
    }
    Ok(())
}
