//! Question command handlers

use super::args::QuestionCommands;
use crate::error::Result;

pub async fn handle(cmd: QuestionCommands) -> Result<()> {
    match cmd {
        QuestionCommands::Create {
            task_id,
            question,
            qtype,
            option,
            urgency,
        } => {
            println!("Not implemented yet: question create");
            println!("  task_id: {}", task_id);
            println!("  question: {}", question);
            println!("  type: {}", qtype);
            if !option.is_empty() {
                println!("  options: {:?}", option);
            }
            println!("  urgency: {}", urgency);
        }
        QuestionCommands::List {
            task,
            unanswered,
            urgent,
        } => {
            println!("Not implemented yet: question list");
            if let Some(t) = task {
                println!("  task: {}", t);
            }
            if unanswered {
                println!("  unanswered only: true");
            }
            if urgent {
                println!("  urgent only: true");
            }
        }
        QuestionCommands::Answer { id, answer, by } => {
            println!("Not implemented yet: question answer");
            println!("  id: {}", id);
            println!("  answer: {}", answer);
            if let Some(b) = by {
                println!("  by: {}", b);
            }
        }
    }
    Ok(())
}
