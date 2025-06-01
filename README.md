# FireStrike

FireStrike is a decentralized anonymous file sharing network operating through TOR. The project provides secure and anonymous file sharing using DHT for distributed storage and magnet links for file access.

## Features

- **Anonymity**: All connections are made through TOR
- **Decentralization**: Using DHT for distributed storage
- **Encryption**: AES-256-CBC with random IV for each file
- **Magnet Links**: Convenient format `firestrike://<hash>#<key>`
- **CLI Interface**: Simple and functional command interface

## Requirements

- Python 3.8+
- TOR
- Dependencies from requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/firestrike.git
cd firestrike
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure TOR is installed and running on your system.

## Usage

### Upload File

```bash
python -m firestrike upload path/to/file
```

Options:
- `--temp`: Delete file after upload
- `--port PORT`: Use specified port (default 8789)

### Download File

```bash
python -m firestrike download "firestrike://hash#key"
```

Options:
- `--output PATH`: Path to save file
- `--temp`: Delete file after completion
- `--port PORT`: Use specified port

### View Peers

```bash
python -m firestrike peers
```

## Architecture

### DHT Network via TOR (`hidden_service.py`)

- Creation of hidden services with .onion addresses
- SOCKS5 proxy for anonymous connections
- Secure logging without IP disclosure
- P2P data exchange between nodes

### File Encryption (`file_encryptor.py`)

- AES-256-CBC encryption with random IV
- SHA3-256 hashing with salt
- Magnet link generation
- Secure key storage

### CLI Client (`cli.py`)

- Upload/download commands
- Asynchronous operation processing
- Temporary file support
- Node management

## Security

- All connections are made through TOR
- Files are encrypted on client side
- Keys are not transmitted over network
- Support for secure file deletion

## Testing

Run tests:
```bash
pytest tests/
```

Tests include:
- Encryption/decryption verification
- DHT testing in isolated network
- Memory leak control
- Automated fixtures

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## Warning

This project is intended for legal file sharing. The authors are not responsible for its misuse. 