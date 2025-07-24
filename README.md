# OnCall

OnCall is a scheduling system designed to manage on-call rotations.

## Features

- **On-call Scheduling:** Define and manage on-call rotations for teams.


## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL (or compatible database)


### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-org/oncall.git
    cd oncall
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Set up the database:
    ```bash
    createdb oncall
    python manage.py migrate
    ```
4. Start the application:
    ```bash
    python manage.py runserver
    ```

### Configuration

Edit `config.yaml` 

## Usage

- Access the web UI at `http://localhost:8000`.
- Add users and teams.
- Configure on-call schedules


## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.

## Contact

For support, open an issue or contact the maintainers.
