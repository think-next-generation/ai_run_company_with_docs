//! Task command handlers

use super::args::TaskCommands;
use crate::error::Result;

pub async fn handle(cmd: TaskCommands) -> Result<()> {
    match cmd {
        TaskCommands::Create {
            title,
            description,
            assignee,
            parent,
            blocked_by,
            priority,
            tag,
        } => {
            println!("Not implemented yet: task create");
            println!("  title: {}", title);
            if let Some(d) = description {
                println!("  description: {}", d);
            }
            if !assignee.is_empty() {
                println!("  assignees: {:?}", assignee);
            }
            if let Some(p) = parent {
                println!("  parent: {}", p);
            }
            if !blocked_by.is_empty() {
                println!("  blocked_by: {:?}", blocked_by);
            }
            println!("  priority: {}", priority);
            if !tag.is_empty() {
                println!("  tags: {:?}", tag);
            }
        }
        TaskCommands::List {
            status,
            assignee,
            tag,
            parent,
            blocked,
            format,
        } => {
            println!("Not implemented yet: task list");
            if !status.is_empty() {
                println!("  status filter: {:?}", status);
            }
            if let Some(a) = assignee {
                println!("  assignee: {}", a);
            }
            if let Some(t) = tag {
                println!("  tag: {}", t);
            }
            if let Some(p) = parent {
                println!("  parent: {}", p);
            }
            if blocked {
                println!("  blocked only: true");
            }
            println!("  format: {}", format);
        }
        TaskCommands::Show {
            id,
            with_children,
            with_dependencies,
        } => {
            println!("Not implemented yet: task show");
            println!("  id: {}", id);
            if with_children {
                println!("  with_children: true");
            }
            if with_dependencies {
                println!("  with_dependencies: true");
            }
        }
        TaskCommands::Update {
            id,
            title,
            description,
            status,
            priority,
        } => {
            println!("Not implemented yet: task update");
            println!("  id: {}", id);
            if let Some(t) = title {
                println!("  title: {}", t);
            }
            if let Some(d) = description {
                println!("  description: {}", d);
            }
            if let Some(s) = status {
                println!("  status: {}", s);
            }
            if let Some(p) = priority {
                println!("  priority: {}", p);
            }
        }
        TaskCommands::Move { id, status } => {
            println!("Not implemented yet: task move");
            println!("  id: {}", id);
            println!("  status: {}", status);
        }
        TaskCommands::Delete { id, yes } => {
            println!("Not implemented yet: task delete");
            println!("  id: {}", id);
            if yes {
                println!("  skip confirmation: true");
            }
        }
    }
    Ok(())
}
