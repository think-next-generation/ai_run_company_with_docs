//! CLI module - command-line interface handling

mod args;
mod board;
mod comment;
mod config_cmd;
mod db_cmd;
mod question;
mod status;
mod task;
mod web;

use clap::Parser;

pub use args::*;

pub fn run() -> anyhow::Result<()> {
    let args = Cli::parse();

    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async {
        match args.command {
            Commands::Task(cmd) => task::handle(cmd).await,
            Commands::Board(cmd) => board::handle(cmd).await,
            Commands::Question(cmd) => question::handle(cmd).await,
            Commands::Comment(cmd) => comment::handle(cmd).await,
            Commands::Status(cmd) => status::handle(cmd).await,
            Commands::Config(cmd) => config_cmd::handle(cmd).await,
            Commands::Db(cmd) => db_cmd::handle(cmd).await,
            Commands::Web(cmd) => web::handle(cmd).await,
        }
    })?;

    Ok(())
}
