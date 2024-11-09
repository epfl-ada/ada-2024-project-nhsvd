use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use csv::WriterBuilder;
use rayon::prelude::*;
use quick_xml::events::Event;
use quick_xml::Reader;

const INITIAL_BUF_SIZE: usize = 1024 * 64; // 64KB
const CSV_BUFFER_SIZE: usize = 1024 * 64; 

struct CsvWriters {
    tokens: csv::Writer<BufWriter<File>>,
    dependencies: csv::Writer<BufWriter<File>>,
    coreferences: csv::Writer<BufWriter<File>>,
}

impl CsvWriters {
    fn new(output_dir: &Path, base_name: &str) -> Result<Self> {
        let create_writer = |suffix: &str| -> Result<csv::Writer<BufWriter<File>>> {
            let path = output_dir.join(format!("{}_{}.csv", suffix, base_name));
            let file = BufWriter::with_capacity(
                CSV_BUFFER_SIZE,
                File::create(path)?
            );
            Ok(WriterBuilder::new()
                .buffer_capacity(CSV_BUFFER_SIZE)
                .from_writer(file))
        };

        Ok(CsvWriters {
            tokens: create_writer("tokens")?,
            dependencies: create_writer("dependencies")?,
            coreferences: create_writer("coreferences")?,
        })
    }

    fn write_headers(&mut self) -> Result<()> {
        self.tokens.write_record(&[
            "sentence_id", "token_id", "word", "lemma",
            "CharacterOffsetBegin", "CharacterOffsetEnd",
            "POS", "NER",
        ])?;

        self.dependencies.write_record(&[
            "sentence_id", "type",
            "governor", "governor_idx",
            "dependent", "dependent_idx",
        ])?;

        self.coreferences.write_record(&[
            "representative", "sentence_id", "start", "end", "head"
        ])?;

        Ok(())
    }
}

#[derive(Default)]
struct ParseContext {
    sentence_id: String,
    current_token: [String; 8],
    current_dep: [String; 6],
    current_coref: [String; 5],
    tag_stack: Vec<String>,
    governor_idx: String,
    dependent_idx: String,
    in_collapsed_ccprocessed_dependencies: bool,
}

impl ParseContext {
    fn new() -> Self {
        let mut context = Self::default();
        context.tag_stack.reserve(512);
        context
    }
}

fn parse_xml_to_csv(file_path: &Path, output_dir: &Path) -> Result<()> {
    let file = File::open(file_path)
        .with_context(|| format!("Failed to open file: {}", file_path.display()))?;
    let file = BufReader::with_capacity(INITIAL_BUF_SIZE, file);
    let mut reader = Reader::from_reader(file);
    reader.config_mut().trim_text(true);

    let base_name = file_path
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or_else(|| anyhow::anyhow!("Invalid file name"))?;

    let mut writers = CsvWriters::new(output_dir, base_name)?;
    writers.write_headers()?;

    let mut context = ParseContext::new();
    let mut buf = Vec::with_capacity(INITIAL_BUF_SIZE);

    loop {
        match reader.read_event_into(&mut buf) {
            Err(e) => return Err(anyhow::anyhow!(
                "Error at position {}: {:?}", 
                reader.error_position(), 
                e
            )),

            Ok(Event::Start(e)) => {
                let tag = String::from_utf8_lossy(e.name().into_inner()).to_string();
                context.tag_stack.push(tag);

                match e.name().as_ref() {
                    b"sentence" => {
                        if let Some(attr) = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"id")
                                .map(|attr| String::from_utf8_lossy(&attr.value).to_string())) 
                        {
                            context.sentence_id = attr;
                        }
                    }
                    b"collapsed-ccprocessed-dependencies" => {
                        context.in_collapsed_ccprocessed_dependencies = true;
                        context.current_dep[0] = context.sentence_id.clone();
                    }
                    b"token" => {
                        if let Some(attr) = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"id")
                                .map(|attr| String::from_utf8_lossy(&attr.value).to_string()))
                        {
                            context.current_token[0] = context.sentence_id.clone();
                            context.current_token[1] = attr;
                        }
                    }
                    b"dep" if context.in_collapsed_ccprocessed_dependencies => {
                        if let Some(attr) = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"type")
                                .map(|attr| String::from_utf8_lossy(&attr.value).to_string()))
                        {
                            context.current_dep[0] = context.sentence_id.clone();
                            context.current_dep[1] = attr;
                        }
                    }
                    b"governor" if context.in_collapsed_ccprocessed_dependencies => {
                        if let Some(attr) = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"idx")
                                .map(|attr| String::from_utf8_lossy(&attr.value).to_string()))
                        {
                            context.governor_idx = attr;
                        }
                    }
                    b"dependent" if context.in_collapsed_ccprocessed_dependencies => {
                        if let Some(attr) = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"idx")
                                .map(|attr| String::from_utf8_lossy(&attr.value).to_string()))
                        {
                            context.dependent_idx = attr;
                        }
                    }
                    b"mention" => {
                        let is_representative = e.attributes()
                            .find_map(|a| a.ok()
                                .filter(|attr| attr.key.as_ref() == b"representative")
                                .map(|attr| String::from_utf8_lossy(&attr.value) == "true"))
                            .unwrap_or(false);
                        context.current_coref[0] = is_representative.to_string();
                    }
                    _ => ()
                }
            }

            Ok(Event::End(ref e)) => {
                context.tag_stack.pop();

                match e.name().as_ref() {
                    b"sentence" => {
                        context.sentence_id.clear();
                    }
                    b"collapsed-ccprocessed-dependencies" => {
                        context.in_collapsed_ccprocessed_dependencies = false;
                    }
                    b"token" => {
                        writers.tokens.write_record(&context.current_token)?;
                        context.current_token = Default::default();
                    }
                    b"dep" => {
                        writers.dependencies.write_record(&context.current_dep)?;
                        context.current_dep = Default::default();
                        context.governor_idx.clear();
                        context.dependent_idx.clear();
                    }
                    b"mention" => {
                        writers.coreferences.write_record(&context.current_coref)?;
                        context.current_coref = Default::default();
                    }
                    _ => ()
                }
            }

            Ok(Event::Text(e)) => {
                if let Some(last_tag) = context.tag_stack.last() {
                    let text = e.unescape()?.to_string();
                    match last_tag.as_str() {
                        // Token fields
                        "word" => context.current_token[2] = text,
                        "lemma" => context.current_token[3] = text,
                        "CharacterOffsetBegin" => context.current_token[4] = text,
                        "CharacterOffsetEnd" => context.current_token[5] = text,
                        "POS" => context.current_token[6] = text,
                        "NER" => context.current_token[7] = text,
                        
                        // Dependency fields
                        "governor" if context.in_collapsed_ccprocessed_dependencies => {
                            context.current_dep[2] = text;
                            context.current_dep[3] = context.governor_idx.clone();
                        }
                        "dependent" if context.in_collapsed_ccprocessed_dependencies => {
                            context.current_dep[4] = text;
                            context.current_dep[5] = context.dependent_idx.clone();
                        }
                        
                        // Coreference fields
                        "sentence" => context.current_coref[1] = text,
                        "start" => context.current_coref[2] = text,
                        "end" => context.current_coref[3] = text,
                        "head" =>context.current_coref[4] = text,

                        _ => ()
                    }
                }
            }

            Ok(Event::Eof) => break,
            _ => ()
        }

        buf.clear();
    }

    Ok(())
}


fn process_files(file_paths: &[PathBuf], output_dir: &Path) -> Result<()> {
    println!("Processing {} files", file_paths.len());

    file_paths.par_iter().try_for_each(|file_path| -> Result<()> {
        parse_xml_to_csv(file_path, output_dir)?;
        Ok(())
    })?;

    println!("Processing completed");
    Ok(())
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 3 {
        eprintln!("Usage: {} <input_dir> <output_dir>", args[0]);
        std::process::exit(1);
    }

    let input_dir = Path::new(&args[1]);
    let output_dir = Path::new(&args[2]);

    if !input_dir.exists() {
        eprintln!("Input directory does not exist: {:?}", input_dir);
        std::process::exit(1);
    }

    std::fs::create_dir_all(output_dir)?;

    let file_paths: Vec<_> = std::fs::read_dir(input_dir)?
        .filter_map(|entry| {
            entry.ok().and_then(|e| {
                let path = e.path();
                if path.extension().and_then(|s| s.to_str()) == Some("xml") {
                    Some(path)
                } else {
                    None
                }
            })
        })
        .collect();

    process_files(&file_paths, output_dir)?;

    Ok(())
}
