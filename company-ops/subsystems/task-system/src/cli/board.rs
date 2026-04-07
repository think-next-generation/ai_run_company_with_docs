//! Board command handlers

use super::args::BoardCommands;
use crate::error::Result;

pub async fn handle(cmd: BoardCommands) -> Result<()> {
    match cmd {
        BoardCommands::Show {
            filter,
            assignee,
            watch,
        } => {
            println!("Not implemented yet: board show");
            if let Some(f) = filter {
                println!("  filter: {}", f);
            }
            if let Some(a) = assignee {
                println!("  assignee: {}", a);
            }
            if watch {
                println!("  watch: true");
            }
        }
    }
    Ok(())
}
