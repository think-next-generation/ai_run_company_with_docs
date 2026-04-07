//! Web server command handlers

use super::args::WebCommands;
use crate::error::Result;

pub async fn handle(cmd: WebCommands) -> Result<()> {
    println!("Not implemented yet: web server");
    println!("  host: {}", cmd.host);
    println!("  port: {}", cmd.port);
    if cmd.open {
        println!("  open browser: true");
    }
    if cmd.no_ui {
        println!("  API only (no UI): true");
    }
    Ok(())
}
