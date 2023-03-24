# PEP Tracker

Simple tool for checking [PEP](https://peps.python.org/pep-0001) status updates.

## Installation

```sh
$ git clone https://github.com/trag1c/pep-tracker.git
$ cargo build --release
```

## Usage

```sh
$ ./target/release/pep-tracker
```

A JSON file will be created on the first run.
Subsequent runs will use this file as a point of reference to compare against
the current state. The file will be updated with the new state after each run
(unless there have been no updates).

## Example

<img width=50% src="https://user-images.githubusercontent.com/77130613/227407441-5a2a7370-525c-4daf-991e-b60af8058217.png">

## License

PEP Tracker is licensed under the MIT License.
