//! Database command handlers

use super::args::DbCommands;
use crate::error::Result;

pub async fn handle(cmd: DbCommands) -> Result<()> {
    match cmd {
        DbCommands::Migrate => {
            println!("Not implemented yet: db migrate");
        }
        DbCommands::Status => {
            println!("Not implemented yet: db status");
        }
    }
    Ok(())
}
