//! Web server command handler
//!
//! Starts HTTP/WebSocket server with optional SPA frontend.

use super::args::WebCommands;
use super::ctx::Ctx;
use crate::error::Result;

pub async fn handle(cmd: WebCommands, ctx: &Ctx) -> Result<()> {
    println!("Starting web server...");
    println!("  Host: {}", cmd.host);
    println!("  Port: {}", cmd.port);
    println!("  WebSocket: {}", if ctx.config.server.websocket_enabled { "enabled" } else { "disabled" });

    if cmd.no_ui {
        println!("  Mode: API only (no frontend)");
    }

    println!();
    println!("Web server implementation is planned for Phase 5.");
    println!("This will include:");
    println!("  - REST API for tasks, questions, comments");
    println!("  - WebSocket for real-time updates");
    println!("  - Vue 3 SPA frontend (embedded)");

    if cmd.open {
        println!();
        println!("Note: Browser auto-open will be available in Phase 5.");
    }

    Ok(())
}
