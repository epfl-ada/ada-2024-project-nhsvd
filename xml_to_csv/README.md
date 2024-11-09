## Rust version of parse_corenlp_xml.py

- Converts the nested XML files into CSVs for easier analysis with pandas etc.
- Only `collapsed-ccprocessed-dep
- ~8x faster than Python (48s vs. 6m 21s on my 8-core laptop)

### Usage

#### Install Rust

On Linux and macOS:

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

See https://www.rust-lang.org/tools/install for other options.

#### Build the project

```
cd xml_to_csv
cargo build --release
```

#### Run the binary

```
./target/release/xml_to_csv /path/to/input_dir /path/to/output_dir
```
