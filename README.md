# Blockchat
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

BlockChat is developed in Python, leveraging its versatility and the extensive libraries available for building secure and efficient blockchain applications. The project is structured to run in any environment where Python is supported, including Windows, macOS, and Linux operating systems.

### Key Dependencies

- [cryptography](https://pypi.org/project/cryptography/): The backbone of BlockChat's security, the `cryptography` library is used extensively for generating public/private key pairs, signing transactions, and verifying signatures. It provides robust cryptographic primitives and easy-to-use abstractions for implementing advanced cryptographic solutions.

## Project Structure
TBA

## Installation
TBA

## Usage
TBA

## Credits
TBA

## License

BlockChat is released under the CC0 1.0 Universal (CC0 1.0) Public Domain Dedication. This means the software is free to be used for any purpose, to be modified and shared without any restrictions. For more details, see the [LICENSE](LICENSE).

