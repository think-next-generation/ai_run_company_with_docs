//! Status command handlers

use super::args::StatusCommands;
use crate::error::Result;

pub async fn handle(cmd: StatusCommands) -> Result<()> {
    match cmd {
        StatusCommands::Show { format, since } => {
            println!("Not implemented yet: status show");
            println!("  format: {}", format);
            if let Some(s) = since {
                println!("  since: {}", s);
            }
        }
        StatusCommands::Watch => {
            println!("Not implemented yet: status watch");
        }
    }
    Ok(())
}
