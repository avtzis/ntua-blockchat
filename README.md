# BlockChat
A Blockchain-Based Messaging and Transaction Platform

## About
BlockChat is an innovative platform developed as part of the Distributed Systems course at the National Technical University of Athens, School of Electrical and Computer Engineering. It leverages blockchain technology to provide a secure and decentralized environment for exchanging messages and conducting transactions with BlockChat Coins (BCC). By implementing a Proof of Stake (PoS) consensus algorithm, BlockChat ensures a secure and efficient mechanism for transaction validation and consensus across the network.

## Members

- [Altan Avtzi](https://github.com/avtzis) - el19241
- [Xhonatan Lukaj](https://github.com/ntua-el19230) - el19230

## Goal and Requirements
The primary goal of BlockChat is to create a distributed platform where users can safely and reliably send messages and conduct transactions without the need for a central authority. This project aims not only to demonstrate the practical application of blockchain technology beyond cryptocurrencies but also to explore the advantages of the Proof of Stake mechanism in ensuring network consensus and security.

### Core Requirements:

- **Wallet Implementation**: Each user (node) must have a unique wallet containing a pair of public and private keys. The public key serves as the wallet address for receiving messages and transactions, while the private key is used for signing transactions to ensure their authenticity.
- **Transaction Types**: The platform should support two types of transactions: coin transfers and message exchanges. Each transaction must be signed by the sender's private key and verified by network nodes.
- **Consensus Algorithm**: Utilize a Proof of Stake algorithm to select validators for new blocks based on the amount of BCC staked by each node. This approach aims to provide a more energy-efficient alternative to Proof of Work systems.
- **Network Communication**: Nodes should communicate over a distributed network, with capabilities for transaction broadcasting and block validation following the consensus rules.
- **Security Features**: Implement security measures such as transaction nonce for preventing replay attacks and ensuring the integrity and order of transactions.

## Key Learnings

Throughout the development of BlockChat, several key learnings emerged:

- **Blockchain Fundamentals**: Deepened understanding of blockchain technology's core principles, including decentralization, immutability, and consensus models.
- **Proof of Stake Mechanism**: Gained insights into the PoS algorithm, exploring its advantages in energy efficiency and stake-based validator selection over traditional PoW systems.
- **Cryptographic Security**: Enhanced knowledge of cryptographic techniques such as digital signatures for securing transactions and ensuring the authenticity and integrity of messages within the network.
- **Distributed Systems Challenges**: Faced and addressed common challenges in distributed systems, including network synchronization, consensus achievement, and data consistency across nodes.
- **Practical Application of Theoretical Concepts**: Applied theoretical concepts from the Distributed Systems course to a real-world project, bridging the gap between academic learning and practical implementation.

## Development and Dependencies

### Development Environment

BlockChat is developed in **Python**, leveraging its versatility and the extensive libraries available for building secure and efficient blockchain applications. The project is structured to run in any environment where Python is supported, including Windows, macOS, and Linux operating systems.

### Key Dependencies

- [cryptography](https://pypi.org/project/cryptography/): Public/private key pairs, sign transactions, and verify signatures.
- [prompt_toolkit](https://pypi.org/project/prompt_toolkit/): CLI prompts.

## Project Structure
- `dist/`: Distributable packages
- `docs/`: Documentation, including the project assignment.
- `scripts/`: Utility scripts.
- `src/`: Source code directory.
  - `blockchat/`: Main package folder.
    - `input/`: Sample transaction files.
    - `main/`: Application entry point.
      - `cli/`: Command-line interface.
      - `gui/`: Placeholder for future graphical interface.
    - `util/`: Utility modules, e.g., `termcolor.py` for colored console output.
    - Core modules: `block.py`, `blockchain.py`, `bootstrap.py`, `client.py`, `node.py`, `transaction.py`, `wallet.py`.
- `tests/`: Testing directory with transaction samples.
- `Dockerfile`: Docker container setup.
- `pyproject.toml`, `setup.py`: Build and distribution configuration.
- `requirements.txt`: External dependencies list.


## Installation
After cloning the repository, you can install `blockchat` as a package, or run on `docker` container:

### Install as a package
1. Create a virtual environment and activate it (optional):
```sh
python -m venv venv
```
then:
```sh
source venv/bin/activate
```

2. Install `build` if not already installed:
```sh
python -m pip install --upgrade build
```

3. Install dependencies from `requirements.txt`:
```sh
pip install -r requirements.txt
```

4. Build package with `build`:
```sh
python -m build
```

5. Install the package from `dist/`
```sh
pip install dist/*.whl
```

### Install using `docker`

1. Build the `blockchat` image:
```sh
docker build -t blockchat-image .
```

2. Create the `blockchat` blockchain network:
```sh
docker network create blockchat-network
```

## Usage

### As a `python` module
```sh
python -m blockchat -h
```

- Example for 5 nodes and 10 block capacity and stake 10BCC:
```sh
python -m blockchat --nodes=5 --capacity=10 --stake=10
```
> [!NOTE]
> With this command, a new client node connects to the blockchain network and provides a console-prompt cli for commands. To see more options, emit the `-h` flag.

- To start a bootstrap node, example:
```sh
python -m blockchat --bootstrap --nodes=5 --capacity=10 --stake=10
```

### As a `docker` container

- Example options:
```sh
docker run --name client-node --network blockchat-network blockchat-image:latest python -u -m blockchat -n 2 -c 5 -s 10 -td
```

- Bootstrap example:
```sh
docker run --name bootstrap-node --network blockchat-network blockchat-image:latest python -u -m blockchat -n 2 -c 5 -s 10 -td -b
```

> [!IMPORTANT]
> Make sure you emit `-d` at the end and `--name` is always `bootstap-node` for bootstrap when using with `docker`

- To run a node again:
```sh
docker start -a client-node
```

### Run a quick test
```sh
python tests/test_main.py -n 5 -c 10 -s 10 -vd
```

## License

BlockChat is released under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication. This means the software is free to be used for any purpose, to be modified and shared without any restrictions. For more details, see the [LICENSE](LICENSE).

