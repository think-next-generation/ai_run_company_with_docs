//! Config command handlers

use super::args::ConfigCommands;
use crate::error::Result;

pub async fn handle(cmd: ConfigCommands) -> Result<()> {
    match cmd {
        ConfigCommands::Init => {
            println!("Not implemented yet: config init");
        }
        ConfigCommands::Show => {
            println!("Not implemented yet: config show");
        }
    }
    Ok(())
}
